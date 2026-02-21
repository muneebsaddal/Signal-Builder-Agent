from pydantic import BaseModel, Field, validator
from typing import Literal, Dict, Any, List, Optional


class SignalIR(BaseModel):
    """Intermediate Representation for trading signals"""
    signal_type: Literal["indicator", "condition", "strategy"] = Field(
        description="Type of signal to build"
    )
    node: str = Field(
        description="Signal node name from registry (e.g., 'MovingAverage', 'RSI')"
    )
    params: Dict[str, Any] = Field(
        description="Parameters for the signal node"
    )
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="Other signals this depends on"
    )

    @validator('node')
    def validate_node(cls, v):
        """Ensure node name is properly formatted"""
        if not v or not v[0].isupper():
            raise ValueError("Node name must start with uppercase letter")
        return v


class ValidationResult(BaseModel):
    """Result of IR validation"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ResolvedSignal(BaseModel):
    """Final resolved signal schema"""
    ir: SignalIR
    resolved_schema: Dict[str, Any]
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "version": "1.0",
            "timestamp": None
        }
    )
