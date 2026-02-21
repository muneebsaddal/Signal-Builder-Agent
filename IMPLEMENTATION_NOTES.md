# Implementation Notes

## Key Design Decisions

### 1. Why Intermediate Representation (IR)?

**Problem:** Trading platforms have thousands of schemas. Can't fit all in LLM context.

**Solution:** Two-stage process:
1. LLM outputs tiny IR (fits in context)
2. Code resolves IR to full schema (deterministic)

**Benefits:**
- No hallucinations (code handles schema details)
- Scalable (add 1000 more schemas, IR stays same)
- Testable (IR validation is code, not prompting)

### 2. Why LangGraph?

**Alternative:** Simple function calls

**LangGraph advantages:**
- State management built-in
- Conditional routing (retry logic)
- Execution tracing automatic
- Production-grade patterns
- Scales to complex workflows

### 3. Why Pydantic?

**Alternative:** Manual dict validation

**Pydantic advantages:**
- Type safety
- Automatic validation
- Clear error messages
- JSON schema generation
- Zero-cost abstractions

### 4. Why Dual LLM Support?

**Practical reasons:**
- Development: Free (Ollama)
- Production: Reliable (OpenAI)
- Demo: Can show both modes
- No vendor lock-in

**Implementation:**
- Single config switch
- Same interface
- No code changes

---

## Code Architecture Patterns

### State Management

```python
class State(TypedDict):
    # Input
    user_request: str
    
    # Intermediate
    ir: Optional[SignalIR]
    validation_result: Optional[Dict]
    
    # Output
    final_output: Optional[Dict]
    
    # Metadata
    execution_log: List[Dict]
    retry_count: int
```

**Why:** TypedDict gives type hints but stays compatible with LangGraph's dict-based state.

### Node Pattern

```python
def node_function(state: State) -> State:
    # 1. Do work
    result = do_something(state["input"])
    
    # 2. Update state
    state["output"] = result
    
    # 3. Log
    log_step(state, "node_name", result)
    
    # 4. Return state
    return state
```

**Why:** Pure functions, easy to test, clear data flow.

### Validation Pattern

```python
def validate(ir):
    errors = []
    
    # Check existence
    if not exists(ir.node):
        errors.append("Node not found")
    
    # Check parameters
    for param in required_params:
        if param not in ir.params:
            errors.append(f"Missing: {param}")
    
    return len(errors) == 0, errors
```

**Why:** Collect all errors at once, give user complete picture.

### Retry Logic

```python
def should_retry(state):
    if not valid:
        if retry_count < MAX_RETRIES:
            return "retry"
        else:
            return "fail"
    return "proceed"
```

**Why:** Explicit retry limits, clear decision logic, no infinite loops.

---

## LLM Prompting Strategy

### Structured Output Prompting

```python
prompt = f"""
Convert request to JSON.

Request: "{user_request}"

Respond with ONLY this JSON structure:
{{
  "signal_type": "indicator",
  "node": "NodeName",
  "params": {{"key": value}}
}}

JSON:"""
```

**Why:**
- Clear output format
- JSON: prefix helps LLM context switch
- "ONLY" reduces extraneous text

### Fallback Strategy

```python
try:
    response = llm.invoke(prompt)
    json_match = re.search(r'\{.*\}', response)
    return parse_json(json_match.group())
except:
    return fallback_ir(request)  # Rule-based backup
```

**Why:** 
- LLMs aren't 100% reliable
- Fallback ensures system always returns something
- Gradual degradation better than hard failure

---

## Schema Resolution Pattern

### Template System

```json
{
  "output_schema": {
    "indicator": "moving_average",
    "period": "{{window}}"
  }
}
```

### Resolution

```python
def resolve_template(template, params):
    if isinstance(template, str) and '{{' in template:
        for key, value in params.items():
            template = template.replace(f'{{{{{key}}}}}', str(value))
    return template
```

**Why:**
- Simple string replacement
- Works for nested structures
- Easy to debug

---

## Error Handling Philosophy

### 1. Fail Fast on Setup

```python
if not api_key:
    raise ValueError("API key required")
```

**Why:** Better to fail immediately than during execution.

### 2. Graceful Degradation on Runtime

```python
try:
    result = llm.invoke(prompt)
except:
    result = fallback_logic()
```

**Why:** System should always return something useful.

### 3. Clear Error Messages

```python
errors.append(f"Parameter '{param}' must be int, got {type(value).__name__}")
```

**Why:** Users need to know exactly what's wrong.

---

## Performance Considerations

### LLM Calls

- **Temperature: 0.1** (deterministic)
- **Max tokens: 1000** (sufficient for IR)
- **Streaming: No** (need complete response)

### Caching Strategy

Not implemented, but would add:
```python
@lru_cache(maxsize=100)
def resolve_schema(ir_hash):
    return resolver.resolve(ir)
```

### Async Potential

Current: Synchronous
Could add: `async def` for API endpoints

**Trade-off:** Added complexity vs. throughput

---

## Testing Strategy

### Unit Tests

- Schema loading
- IR validation
- Schema resolution
- Template rendering

### Integration Tests

- Complete graph execution
- API endpoints
- Error handling

### Example-Based Tests

- Real user requests
- Edge cases
- Failure modes

**Why:** Multiple test layers catch different bug types.

---

## What Makes This Production-Ready

### 1. Determinism

- Low temperature
- Validation
- Fallbacks
- No randomness in resolution

### 2. Observability

- Execution logs
- Retry counts
- Error messages
- Trace files

### 3. Resilience

- Retry logic
- Fallback IR
- Error recovery
- Graceful degradation

### 4. Maintainability

- Clear structure
- Type hints
- Documentation
- Test coverage

---

## Common Pitfalls (Avoided)

### ❌ Don't: Let LLM output full schema

```python
# Bad
prompt = f"Generate full trading schema for: {request}"
```

**Why fails:** Hallucinations, inconsistency, schema explosion

### ✅ Do: Use IR

```python
# Good
prompt = f"Generate IR (10 lines) for: {request}"
resolved = resolve_ir_to_schema(ir)
```

### ❌ Don't: Retry forever

```python
# Bad
while not valid:
    ir = generate_ir(request)
```

**Why fails:** Infinite loops, cost explosion

### ✅ Do: Limit retries

```python
# Good
if retry_count < MAX_RETRIES:
    return "retry"
else:
    return "fail"
```

### ❌ Don't: Assume LLM follows format

```python
# Bad
ir = json.loads(llm_response)
```

**Why fails:** LLM might add markdown, explanations

### ✅ Do: Parse defensively

```python
# Good
json_match = re.search(r'\{.*\}', response)
ir = json.loads(json_match.group()) if json_match else fallback()
```

---

## Extension Points

### Add New Signal

1. Edit `schemas/registry.json`
2. Add node definition
3. No code changes needed

### Add New LLM Provider

1. Add case in `llm_config.py`
2. Return compatible interface
3. Update `.env.example`

### Add Validation Rule

1. Edit `nodes/validator.py`
2. Add to `validate()` method
3. Return clear error message

### Add API Endpoint

1. Add function in `api.py`
2. Use existing graph
3. Define request/response models

---

## Interview Talking Points

### "Why did you use IR?"

"Direct LLM to schema doesn't scale. With thousands of schemas, the context window fills up. IR decouples the LLM from implementation details - the model outputs a tiny structure, then deterministic code handles the complexity."

### "How do you ensure reliability?"

"Multiple layers: Pydantic validates structure, custom validators check business rules, retry logic handles transient failures, fallback logic ensures we always return something. Plus complete execution tracing for debugging."

### "Why LangGraph vs. simple functions?"

"LangGraph gives us production patterns out of the box - state management, conditional routing, execution tracing. As the system grows, we can add more complex workflows without refactoring the core architecture."

### "How do you handle errors?"

"Three-tier approach: fail fast on setup errors, retry on transient errors, graceful degradation on persistent errors. Every error has a clear message with suggestions for fixing."

### "How would this scale?"

"IR pattern scales linearly - add 1000 schemas, IR stays the same size. The resolution is pure code, so it's fast and cacheable. Could add Redis caching, async processing, horizontal scaling of API servers."

---

## What You Built

Not just a chatbot. A production-grade AI system with:

✅ **Architecture** - State machines, not scripts  
✅ **Validation** - Multiple layers  
✅ **Observability** - Complete tracing  
✅ **Resilience** - Retry and fallback  
✅ **Scalability** - IR pattern  
✅ **Maintainability** - Clean code  
✅ **Flexibility** - Dual LLM support  

This is what separates junior from senior AI engineers.
