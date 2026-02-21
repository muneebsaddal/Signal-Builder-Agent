from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from schemas.ir_schema import SignalIR, ResolvedSignal
from schemas.resolver import SchemaRegistry, SchemaResolver
from nodes.classifier import IntentClassifier
from nodes.ir_generator import IRGenerator
from nodes.validator import IRValidator
from nodes.resolver_node import ResolverNode
import time


# Define state
class SignalBuilderState(TypedDict):
    user_request: str
    intent: Optional[Dict[str, str]]
    signal_type: Optional[str]
    ir: Optional[SignalIR]
    validation_result: Optional[Dict[str, Any]]
    resolved_signal: Optional[ResolvedSignal]
    execution_log: List[Dict[str, Any]]
    retry_count: int
    final_output: Optional[Dict[str, Any]]
    errors: List[str]


class SignalBuilderGraph:
    """LangGraph-based signal builder pipeline"""
    
    def __init__(self):
        # Initialize components
        self.registry = SchemaRegistry()
        self.resolver = SchemaResolver(self.registry)
        
        self.classifier = IntentClassifier()
        self.ir_generator = IRGenerator(self.registry)
        self.validator = IRValidator(self.resolver)
        self.resolver_node = ResolverNode(self.resolver)
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construct the LangGraph state machine"""
        
        workflow = StateGraph(SignalBuilderState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("generate_ir", self._generate_ir_node)
        workflow.add_node("validate_ir", self._validate_ir_node)
        workflow.add_node("resolve_schema", self._resolve_schema_node)
        workflow.add_node("finalize", self._finalize_node)
        workflow.add_node("retry_ir", self._retry_ir_node)
        
        # Define edges
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "generate_ir")
        workflow.add_edge("generate_ir", "validate_ir")
        
        # Conditional edge after validation
        workflow.add_conditional_edges(
            "validate_ir",
            self._should_retry,
            {
                "retry": "retry_ir",
                "proceed": "resolve_schema",
                "fail": "finalize"
            }
        )
        
        workflow.add_edge("retry_ir", "generate_ir")
        workflow.add_edge("resolve_schema", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _log_step(self, state: SignalBuilderState, step: str, data: Dict[str, Any]):
        """Add execution log entry"""
        log_entry = {
            "step": step,
            "timestamp": time.time(),
            "data": data
        }
        state["execution_log"].append(log_entry)
    
    def _classify_intent_node(self, state: SignalBuilderState) -> SignalBuilderState:
        """Node: Classify user intent"""
        intent = self.classifier.classify(state["user_request"])
        
        state["intent"] = intent
        state["signal_type"] = intent["signal_type"]
        
        self._log_step(state, "classify_intent", {
            "intent": intent
        })
        
        return state
    
    def _generate_ir_node(self, state: SignalBuilderState) -> SignalBuilderState:
        """Node: Generate IR from user request"""
        ir = self.ir_generator.generate(
            state["user_request"],
            state["signal_type"],
            state["intent"].get("signal_hint", "")
        )
        
        state["ir"] = ir
        
        self._log_step(state, "generate_ir", {
            "ir": ir.dict()
        })
        
        return state
    
    def _validate_ir_node(self, state: SignalBuilderState) -> SignalBuilderState:
        """Node: Validate IR"""
        validation = self.validator.validate_with_retry_suggestion(state["ir"])
        
        state["validation_result"] = validation
        
        if not validation["valid"]:
            state["errors"].extend(validation["errors"])
        
        self._log_step(state, "validate_ir", {
            "valid": validation["valid"],
            "errors": validation.get("errors", []),
            "suggestions": validation.get("suggestions", [])
        })
        
        return state
    
    def _retry_ir_node(self, state: SignalBuilderState) -> SignalBuilderState:
        """Node: Increment retry counter"""
        state["retry_count"] += 1
        
        self._log_step(state, "retry_ir", {
            "retry_count": state["retry_count"],
            "previous_errors": state["validation_result"].get("errors", [])
        })
        
        return state
    
    def _resolve_schema_node(self, state: SignalBuilderState) -> SignalBuilderState:
        """Node: Resolve IR to full schema"""
        result = self.resolver_node.resolve_with_validation(state["ir"])
        
        if result["success"]:
            state["resolved_signal"] = result["resolved_signal"]
        else:
            state["errors"].extend(result["errors"])
        
        self._log_step(state, "resolve_schema", {
            "success": result["success"],
            "output_valid": result["output_valid"]
        })
        
        return state
    
    def _finalize_node(self, state: SignalBuilderState) -> SignalBuilderState:
        """Node: Create final output"""
        if state["resolved_signal"]:
            state["final_output"] = {
                "status": "success",
                "ir": state["ir"].dict(),
                "resolved_schema": state["resolved_signal"].resolved_schema,
                "metadata": state["resolved_signal"].metadata
            }
        else:
            state["final_output"] = {
                "status": "failed",
                "errors": state["errors"],
                "retry_count": state["retry_count"]
            }
        
        self._log_step(state, "finalize", {
            "status": state["final_output"]["status"]
        })
        
        return state
    
    def _should_retry(self, state: SignalBuilderState) -> str:
        """Decide whether to retry IR generation"""
        validation = state["validation_result"]
        
        # Failed validation
        if not validation["valid"]:
            # Max 1 retry
            if state["retry_count"] < 1 and validation.get("should_retry", False):
                return "retry"
            else:
                return "fail"
        
        # Validation passed
        return "proceed"
    
    def run(self, user_request: str) -> Dict[str, Any]:
        """Execute the graph with a user request"""
        
        initial_state = {
            "user_request": user_request,
            "intent": None,
            "signal_type": None,
            "ir": None,
            "validation_result": None,
            "resolved_signal": None,
            "execution_log": [],
            "retry_count": 0,
            "final_output": None,
            "errors": []
        }
        
        # Run graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "output": final_state["final_output"],
            "execution_log": final_state["execution_log"],
            "retry_count": final_state["retry_count"]
        }
