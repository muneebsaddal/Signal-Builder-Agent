from typing import Dict, Any
from schemas.ir_schema import SignalIR, ResolvedSignal
from schemas.resolver import SchemaResolver


class ResolverNode:
    """Resolves IR to full trading signal schema"""
    
    def __init__(self, resolver: SchemaResolver):
        self.resolver = resolver
    
    def resolve(self, ir: SignalIR) -> ResolvedSignal:
        """
        Convert IR to full signal schema.
        Injects parameters and builds complete structure.
        """
        return self.resolver.resolve(ir)
    
    def resolve_with_validation(self, ir: SignalIR) -> Dict[str, Any]:
        """
        Resolve IR and validate the output.
        Returns dict with resolved signal and validation status.
        """
        try:
            resolved = self.resolve(ir)
            
            # Basic output validation
            is_valid = self._validate_resolved_schema(resolved.resolved_schema)
            
            return {
                "success": True,
                "resolved_signal": resolved,
                "output_valid": is_valid,
                "errors": [] if is_valid else ["Resolved schema structure invalid"]
            }
        
        except Exception as e:
            return {
                "success": False,
                "resolved_signal": None,
                "output_valid": False,
                "errors": [str(e)]
            }
    
    def _validate_resolved_schema(self, schema: Dict[str, Any]) -> bool:
        """Validate that resolved schema has required structure"""
        # Check that schema has at least one key
        if not schema:
            return False
        
        # Check that it has proper signal identifier
        has_identifier = any(
            key in schema 
            for key in ['indicator', 'condition', 'strategy']
        )
        
        return has_identifier
