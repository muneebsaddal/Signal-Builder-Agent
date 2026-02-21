# Testing Checklist

## Pre-Testing Setup

- [ ] Ollama installed and running
- [ ] `ollama pull llama3.2:3b` completed
- [ ] Python 3.10+ installed
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file exists with `LLM_PROVIDER=ollama`

---

## Test 1: Schema Registry

```bash
python tests/test_all.py
```

Expected output:
```
✓ Schemas loaded successfully
✓ MovingAverage schema found
✓ Found X indicators
```

**Pass criteria:** No errors, all schemas load correctly

---

## Test 2: IR Validation

Should be included in `test_all.py`

Expected output:
```
✓ Valid IR passed validation
✓ Invalid IR caught: [error message]
```

**Pass criteria:** Valid IR passes, invalid IR caught with clear errors

---

## Test 3: IR Resolution

Should be included in `test_all.py`

Expected output:
```
✓ IR resolved correctly
  Resolved schema: {indicator: "rsi", period: 14}
```

**Pass criteria:** IR correctly maps to full schema

---

## Test 4: End-to-End Graph

Should be included in `test_all.py`

Expected output:
```
Request: 20-day moving average of closing price
Status: success
✓ IR: MovingAverage
✓ Resolved: [dict_keys]
Execution steps: 5
Retries: 0
```

**Pass criteria:** Request successfully processed through entire graph

---

## Test 5: Example Executions

```bash
python examples/run_examples.py
```

Expected output:
```
EXAMPLE: Simple Moving Average Indicator
Request: "20-day moving average of closing price"

Status: success
Retries: 0

Intermediate Representation (IR):
  Type: indicator
  Node: MovingAverage
  Params: {...}

Resolved Schema:
{...}

Execution Steps:
  1. classify_intent
  2. generate_ir
  3. validate_ir
  4. resolve_schema
  5. finalize
```

**Pass criteria:** 
- At least 6/8 examples succeed
- Execution traces saved to `examples/execution_traces/`
- Each has 5 execution steps

---

## Test 6: API Server

```bash
# Terminal 1
python api.py

# Terminal 2
curl http://localhost:8000/health
```

Expected output:
```json
{"status": "healthy"}
```

**Pass criteria:** Server starts on port 8000, health check returns OK

---

## Test 7: API Build Signal

```bash
curl -X POST http://localhost:8000/build-signal \
  -H "Content-Type: application/json" \
  -d '{"request": "14-period RSI indicator"}'
```

Expected output:
```json
{
  "status": "success",
  "ir": {...},
  "resolved_schema": {...},
  "execution_log": [...],
  "retry_count": 0
}
```

**Pass criteria:** Returns valid JSON with resolved schema

---

## Test 8: API List Signals

```bash
curl http://localhost:8000/list-signals
```

Expected output:
```json
{
  "available_signals": {
    "indicators": [...],
    "conditions": [...],
    "strategies": [...]
  },
  "total_count": 17
}
```

**Pass criteria:** Returns list of all available signals

---

## Test 9: Error Handling

```bash
curl -X POST http://localhost:8000/build-signal \
  -H "Content-Type: application/json" \
  -d '{"request": "invalid gibberish xyz 123"}'
```

Expected behavior:
- Either returns success with best-effort IR
- Or returns failed status with clear errors
- Should NOT crash or return 500 error

**Pass criteria:** Graceful handling, clear error messages

---

## Test 10: Retry Logic

Look at execution traces in `examples/execution_traces/`

Find a trace with `retry_count > 0`

Expected behavior:
- Validation fails first time
- System retries generation
- Either succeeds on retry or fails with clear errors

**Pass criteria:** Retry logic executes, logged in execution trace

---

## Switch to OpenAI (Optional)

If you have OpenAI API key:

1. Edit `.env`:
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
```

2. Rerun tests:
```bash
python tests/test_all.py
python examples/run_examples.py
```

Expected behavior:
- Should work exactly the same
- Possibly faster responses
- Possibly higher success rate

**Pass criteria:** All tests pass with OpenAI provider

---

## Success Criteria Summary

✅ All unit tests pass  
✅ 6+ example executions succeed  
✅ API starts and responds  
✅ Execution traces generated  
✅ Error handling graceful  
✅ Retry logic works  
✅ Can switch LLM providers  

---

## If Tests Fail

### Ollama Not Running
```bash
# Check
curl http://localhost:11434/api/tags

# Fix: Start Ollama application
```

### Model Not Found
```bash
ollama pull llama3.2:3b
```

### Import Errors
```bash
pip install -r requirements.txt
```

### Port Already in Use (8000)
```bash
# Change port in api.py
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### LLM Response Parsing Errors

This is expected with Ollama occasionally. Check:
- Response includes fallback logic
- System still produces valid output
- Retry logic catches and fixes

---

## Performance Benchmarks

Expected performance on typical hardware:

| Operation | Ollama (CPU) | OpenAI |
|-----------|--------------|---------|
| First request | 5-10s | 1-2s |
| Subsequent | 2-3s | 1-2s |
| Test suite | 30-60s | 10-20s |
| Examples | 60-120s | 20-40s |

---

## What to Document

After testing, document:
1. Which tests passed
2. Success rate (X/8 examples)
3. Average execution time
4. Any interesting failures
5. Screenshots of API responses

This documentation proves the system works.

---

## Ready for Showcase

You're ready to showcase when:

✅ All core tests pass  
✅ API responds correctly  
✅ Have execution traces  
✅ Can switch to OpenAI  
✅ Understand the flow  
✅ Can explain the IR pattern  

Then: Push to GitHub, add to portfolio, link in resume.
