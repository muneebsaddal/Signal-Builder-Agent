import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from schemas.ir_schema import SignalIR, ResolvedSignal
from datetime import datetime


class SchemaRegistry:
    """Loads and manages signal schemas"""
    
    def __init__(self, registry_path: str = "schemas/registry.json"):
        self.registry_path = Path(registry_path)
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict:
        """Load schema registry from JSON"""
        with open(self.registry_path, 'r') as f:
            return json.load(f)
    
    def get_schema(self, signal_type: str, node: str) -> Optional[Dict]:
        """Get schema for a specific node"""
        category = f"{signal_type}s"  # indicator -> indicators
        return self.schemas.get(category, {}).get(node)
    
    def list_nodes(self, signal_type: Optional[str] = None) -> Dict[str, list]:
        """List all available nodes"""
        if signal_type:
            category = f"{signal_type}s"
            return {category: list(self.schemas.get(category, {}).keys())}
        
        return {
            category: list(nodes.keys())
            for category, nodes in self.schemas.items()
        }


class SchemaResolver:
    """Resolves IR to full trading signal schemas"""
    
    def __init__(self, registry: SchemaRegistry):
        self.registry = registry
        
        # Parameter alias map - translates LLM terms to schema terms
        self.alias_map = {
            # Generic aliases
            "period": "window",
            "length": "window",
            "timeframe": "window",
            
            # MACD specific
            "fast": "fast_period",
            "slow": "slow_period",
            "signal": "signal_period",
            
            # Threshold/condition aliases
            "value": "threshold",
            "level": "threshold",
            
            # Operator aliases
            "direction": "operator",
            "comparison": "operator",
            
            # Source aliases
            "field": "source",
            "price": "source",
        }
        
        # Node-specific defaults - fills in common missing parameters
        self.node_defaults = {
            # Indicators
            "MovingAverage": {"source": "price.close"},
            "RSI": {"source": "price.close"},
            "BollingerBands": {"source": "price.close"},
            "ATR": {"source": "price.close"},
            "Stochastic": {"source": "price.close"},
            "ADX": {"source": "price.close"},
            
            # Conditions
            "IndicatorThreshold": {"operator": "above"},
            "VolumeSpike": {"period": 20},
            "PriceThreshold": {"operator": "above"},
        }

    def _normalize_params(self, node: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parameters by:
        1. Translating LLM terms to schema terms (alias_map)
        2. Adding node-specific defaults
        """
        normalized = {}
        
        # Apply alias translations
        for key, value in params.items():
            normalized_key = self.alias_map.get(key, key)
            normalized[normalized_key] = value
        
        # Add node-specific defaults (only if not already present)
        if node in self.node_defaults:
            for key, value in self.node_defaults[node].items():
                normalized.setdefault(key, value)
        
        return normalized
    
    def validate_ir(self, ir: SignalIR) -> Tuple[bool, list]:
        """Validate IR against registry"""
        errors = []
        
        ir.params = self._normalize_params(ir.node, ir.params)

        # Check if node exists
        schema = self.registry.get_schema(ir.signal_type, ir.node)
        if not schema:
            errors.append(f"Node '{ir.node}' not found in '{ir.signal_type}' category")
            return False, errors
        
        # Validate parameters
        required_params = schema.get('params', {})
        for param_name, param_def in required_params.items():
            if param_name not in ir.params:
                if 'default' not in param_def:
                    errors.append(f"Missing required parameter: {param_name}")
                continue
            
            # Type validation
            param_value = ir.params[param_name]
            param_type = param_def.get('type')
            
            if param_type == 'int' and not isinstance(param_value, int):
                errors.append(f"Parameter '{param_name}' must be int, got {type(param_value).__name__}")
            elif param_type == 'float' and not isinstance(param_value, (int, float)):
                errors.append(f"Parameter '{param_name}' must be float, got {type(param_value).__name__}")
            elif param_type == 'string' and not isinstance(param_value, str):
                errors.append(f"Parameter '{param_name}' must be string, got {type(param_value).__name__}")
            
            # Range validation
            if 'range' in param_def and isinstance(param_value, (int, float)):
                min_val, max_val = param_def['range']
                if not (min_val <= param_value <= max_val):
                    errors.append(f"Parameter '{param_name}' must be between {min_val} and {max_val}")
            
            # Options validation
            if 'options' in param_def and param_value not in param_def['options']:
                errors.append(f"Parameter '{param_name}' must be one of {param_def['options']}")
        
        return len(errors) == 0, errors
    
    def resolve(self, ir: SignalIR) -> ResolvedSignal:
        """Resolve IR to full schema"""
        schema = self.registry.get_schema(ir.signal_type, ir.node)
        
        # Get output template
        output_template = schema['output_schema']
        
        # Merge params with defaults
        params = self._merge_with_defaults(ir.params, schema.get('params', {}))
        
        # Resolve template placeholders
        resolved = self._resolve_template(output_template, params)
        
        return ResolvedSignal(
            ir=ir,
            resolved_schema=resolved,
            metadata={
                "version": "1.0",
                "timestamp": datetime.utcnow().isoformat(),
                "node": ir.node,
                "type": ir.signal_type
            }
        )
    
    def _merge_with_defaults(self, params: Dict[str, Any], param_defs: Dict) -> Dict[str, Any]:
        """Merge provided params with defaults"""
        merged = params.copy()
        for param_name, param_def in param_defs.items():
            if param_name not in merged and 'default' in param_def:
                merged[param_name] = param_def['default']
        return merged
    
    def _resolve_template(self, template: Any, params: Dict[str, Any]) -> Any:
        """Recursively resolve template placeholders"""
        if isinstance(template, dict):
            return {
                k: self._resolve_template(v, params)
                for k, v in template.items()
            }
        elif isinstance(template, list):
            return [self._resolve_template(item, params) for item in template]
        elif isinstance(template, str) and '{{' in template:
            # Replace {{param_name}} with actual value
            pattern = r'\{\{(\w+)\}\}'
            matches = re.findall(pattern, template)
            
            if matches:
                result = template
                for match in matches:
                    if match in params:
                        # If template is just {{param}}, return the value directly
                        if template == f'{{{{{match}}}}}':
                            return params[match]
                        # Otherwise replace in string
                        result = result.replace(f'{{{{{match}}}}}', str(params[match]))
                return result
        
        return template
