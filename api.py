from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from graph import SignalBuilderGraph
from llm_config import get_provider_info
from schemas.resolver import SchemaRegistry
import uvicorn


app = FastAPI(
    title="Signal Builder Agent API",
    description="AI-powered trading signal builder using LangGraph",
    version="1.0.0"
)

# Initialize graph
signal_builder = SignalBuilderGraph()


# Request/Response models
class SignalRequest(BaseModel):
    request: str = Field(
        description="Natural language trading signal request",
        example="20-day moving average of closing price"
    )


class SignalResponse(BaseModel):
    status: str
    ir: Optional[Dict[str, Any]] = None
    resolved_schema: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_log: List[Dict[str, Any]]
    retry_count: int
    errors: Optional[List[str]] = None


@app.get("/")
def read_root():
    """API status and info"""
    provider_info = get_provider_info()
    return {
        "service": "Signal Builder Agent",
        "status": "running",
        "llm_provider": provider_info,
        "endpoints": {
            "build_signal": "/build-signal",
            "list_signals": "/list-signals",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/build-signal", response_model=SignalResponse)
def build_signal(request: SignalRequest):
    """
    Build a trading signal from natural language request.
    
    The agent will:
    1. Classify the intent
    2. Generate intermediate representation (IR)
    3. Validate the IR
    4. Resolve to full schema
    5. Return structured output with execution trace
    """
    try:
        result = signal_builder.run(request.request)
        
        output = result["output"]
        
        return SignalResponse(
            status=output["status"],
            ir=output.get("ir"),
            resolved_schema=output.get("resolved_schema"),
            metadata=output.get("metadata"),
            execution_log=result["execution_log"],
            retry_count=result["retry_count"],
            errors=output.get("errors")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list-signals")
def list_signals(signal_type: Optional[str] = None):
    """
    List available signal nodes.
    
    Query params:
    - signal_type: Filter by 'indicator', 'condition', or 'strategy'
    """
    registry = SchemaRegistry()
    nodes = registry.list_nodes(signal_type)
    
    return {
        "available_signals": nodes,
        "total_count": sum(len(v) for v in nodes.values())
    }


@app.get("/provider-info")
def provider_info():
    """Get current LLM provider configuration"""
    return get_provider_info()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
