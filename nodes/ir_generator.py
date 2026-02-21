import json
import re
from typing import Dict, Any
from schemas.ir_schema import SignalIR
from schemas.resolver import SchemaRegistry
from llm_config import get_llm


class IRGenerator:
    """Generates Intermediate Representation from natural language"""
    
    def __init__(self, registry: SchemaRegistry):
        self.llm = get_llm()
        self.registry = registry
    
    def generate(self, user_request: str, signal_type: str, signal_hint: str = "") -> SignalIR:
        """Generate IR from user request"""
        
        # Get available nodes for this signal type
        available_nodes = self.registry.list_nodes(signal_type)
        nodes_list = ', '.join(available_nodes.get(f"{signal_type}s", []))
        
        prompt = f"""Convert this trading signal request into a structured intermediate representation.

User Request: "{user_request}"
Signal Type: {signal_type}
{f"Suggested Signal: {signal_hint}" if signal_hint else ""}

Available {signal_type} nodes: {nodes_list}

You MUST respond with ONLY a valid JSON object (no extra text before or after):
{{
  "signal_type": "{signal_type}",
  "node": "[choose from available nodes]",
  "params": {{
    "param_name": value
  }}
}}

Rules:
1. Pick the most appropriate node from the available list
2. Extract numeric values from the request (periods, thresholds, etc)
3. Use sensible defaults if values not specified
4. Respond with ONLY the JSON object

JSON:"""

        try:
            response = self.llm.invoke(prompt).strip()
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                ir_dict = json.loads(json_str)
                
                return SignalIR(**ir_dict)
            else:
                raise ValueError("No valid JSON found in response")
        
        except Exception as e:
            # Fallback: create basic IR based on keywords
            return self._fallback_ir(user_request, signal_type, nodes_list.split(', '))
    
    def _fallback_ir(self, request: str, signal_type: str, available_nodes: list) -> SignalIR:
        """Fallback IR generation using simple keyword matching"""
        request_lower = request.lower()
        
        # Default nodes by signal type
        default_nodes = {
            'indicator': 'MovingAverage',
            'condition': 'PriceThreshold',
            'strategy': 'MACrossover'
        }
        
        # Try to match node from request
        matched_node = None
        if available_nodes:
            for node in available_nodes:
                if node and node.lower() in request_lower:
                    matched_node = node
                    break
        
        # Use default if no match
        if not matched_node:
            matched_node = default_nodes.get(signal_type, 'MovingAverage')
        
        # Extract numbers from request
        numbers = re.findall(r'\d+', request)
        
        # Build params based on signal type and keywords
        params = {}
        
        if signal_type == 'strategy' or 'crossover' in request_lower or 'strategy' in request_lower:
            # Strategy defaults
            if len(numbers) >= 2:
                params['fast_period'] = int(numbers[0])
                params['slow_period'] = int(numbers[1])
            else:
                params['fast_period'] = 10
                params['slow_period'] = 20
        elif 'moving' in request_lower or 'average' in request_lower or 'ma' in request_lower:
            params['window'] = int(numbers[0]) if numbers else 20
            params['source'] = 'price.close'
        elif 'rsi' in request_lower:
            params['period'] = int(numbers[0]) if numbers else 14
            params['source'] = 'price.close'
        elif 'macd' in request_lower:
            params['fast_period'] = 12
            params['slow_period'] = 26
            params['signal_period'] = 9
        elif 'bollinger' in request_lower:
            params['period'] = int(numbers[0]) if numbers else 20
            params['std_dev'] = 2.0
        elif 'volume' in request_lower:
            params['multiplier'] = float(numbers[0]) if numbers else 1.5
            params['period'] = 20
        else:
            # Generic fallback
            params['period'] = int(numbers[0]) if numbers else 14
        
        # Ensure we have at least one param
        if not params:
            params = {"period": 14}
        
        return SignalIR(
            signal_type=signal_type,
            node=matched_node,
            params=params
        )