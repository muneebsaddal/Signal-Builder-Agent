from typing import Dict, Any, List, Tuple
from schemas.ir_schema import SignalIR
from schemas.resolver import SchemaResolver


class IRValidator:
    """Validates IR against schema registry"""
    
    def __init__(self, resolver: SchemaResolver):
        self.resolver = resolver
    
    def validate(self, ir: SignalIR) -> Tuple[bool, List[str]]:
        """
        Validate IR structure and parameters.
        Returns (is_valid, error_list)
        """
        errors = []
        
        # Basic structure validation (already done by Pydantic)
        # Additional business logic validation
        
        # Use resolver's validation
        is_valid, validation_errors = self.resolver.validate_ir(ir)
        errors.extend(validation_errors)
        
        return is_valid, errors
    
    def validate_with_retry_suggestion(self, ir: SignalIR) -> Dict[str, Any]:
        """
        Validate and provide suggestions for fixing errors
        """
        is_valid, errors = self.validate(ir)
        
        if not is_valid:
            # Generate suggestions
            suggestions = []
            for error in errors:
                if "not found" in error:
                    suggestions.append("Check available nodes in registry")
                elif "Missing required parameter" in error:
                    param = error.split(":")[1].strip()
                    suggestions.append(f"Add parameter: {param}")
                elif "must be" in error:
                    suggestions.append("Check parameter type and range")
        
            return {
                "valid": False,
                "errors": errors,
                "suggestions": suggestions,
                "should_retry": len(errors) <= 3  # Only retry if few errors
            }
        
        return {
            "valid": True,
            "errors": [],
            "suggestions": [],
            "should_retry": False
        }
