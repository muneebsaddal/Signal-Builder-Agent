# How to Use Signal Builder Agent

## Quick Start (3 Steps)

### Step 1: Install Ollama (Free Local LLM)

```bash
# Visit https://ollama.ai and install for your OS

# Then pull the model
ollama pull llama3.2:3b

# Verify it's running
ollama list
```

### Step 2: Install Python Dependencies

```bash
cd signal-builder-agent
pip install -r requirements.txt
```

### Step 3: Run Tests

```bash
python tests/test_all.py
```

You should see:
```
✓ Schemas loaded successfully
✓ MovingAverage schema found
✓ Valid IR passed validation
...
ALL TESTS PASSED ✓
```

---

## Running Examples

### Console Examples

```bash
python examples/run_examples.py
```

This runs 8 example requests and saves execution traces to `examples/execution_traces/`

### API Server

```bash
# Start server
python api.py

# In another terminal, test it
curl -X POST http://localhost:8000/build-signal \
  -H "Content-Type: application/json" \
  -d '{"request": "20-day moving average"}'
```

---

## Using in Your Code

```python
from graph import SignalBuilderGraph

# Create builder
builder = SignalBuilderGraph()

# Build a signal
result = builder.run("14-period RSI indicator")

# Check result
if result["output"]["status"] == "success":
    print("IR:", result["output"]["ir"])
    print("Schema:", result["output"]["resolved_schema"])
    print("Steps:", len(result["execution_log"]))
else:
    print("Failed:", result["output"]["errors"])
```

---

## Switching to OpenAI (for Showcase)

When ready to showcase with OpenAI:

### 1. Edit `.env`

```bash
# Change from:
LLM_PROVIDER=ollama

# To:
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

### 2. Restart Services

That's it! No code changes needed.

```bash
python api.py
```

---

## Understanding the Output

### Success Response

```json
{
  "status": "success",
  "ir": {
    "signal_type": "indicator",
    "node": "MovingAverage",
    "params": {"window": 20, "source": "price.close"}
  },
  "resolved_schema": {
    "indicator": "moving_average",
    "type": "sma",
    "period": 20,
    "field": "price.close"
  },
  "metadata": {
    "version": "1.0",
    "timestamp": "2024-02-21T10:30:00",
    "node": "MovingAverage",
    "type": "indicator"
  },
  "execution_log": [
    {"step": "classify_intent", ...},
    {"step": "generate_ir", ...},
    {"step": "validate_ir", ...},
    {"step": "resolve_schema", ...},
    {"step": "finalize", ...}
  ],
  "retry_count": 0
}
```

### Failed Response

```json
{
  "status": "failed",
  "errors": [
    "Node 'InvalidNode' not found in 'indicator' category",
    "Missing required parameter: window"
  ],
  "retry_count": 1
}
```

---

## Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama (auto-starts on macOS/Windows)
# On Linux: sudo systemctl start ollama
```

### Model Not Found

```bash
ollama pull llama3.2:3b
```

### Import Errors

```bash
pip install -r requirements.txt
```

---

## Testing Different Requests

Try these in `examples/run_examples.py` or API:

```python
requests = [
    # Indicators
    "20-day exponential moving average",
    "RSI with 21-period",
    "MACD default settings",
    "Bollinger Bands 2 standard deviations",
    
    # Conditions
    "Price above 100",
    "Volume spike above 2x average",
    "RSI below 30",
    
    # Strategies
    "Moving average crossover 10 and 20",
    "RSI mean reversion strategy",
]
```

---

## Performance Tips

### Ollama (CPU Mode)

- First request: ~5-10s (model loading)
- Subsequent: ~2-3s per request
- Memory: ~2GB RAM

### OpenAI

- ~1-2s per request
- Requires API key and credits
- More reliable for complex requests

---

## Development Workflow

```bash
# 1. Develop with Ollama (free)
LLM_PROVIDER=ollama

# 2. Test thoroughly
python tests/test_all.py

# 3. Run examples to generate traces
python examples/run_examples.py

# 4. Switch to OpenAI for demo
LLM_PROVIDER=openai

# 5. Start API for live demo
python api.py
```

---

## Adding New Signals

### 1. Edit `schemas/registry.json`

```json
{
  "indicators": {
    "YourIndicator": {
      "description": "Your custom indicator",
      "params": {
        "period": {"type": "int", "default": 10}
      },
      "output_schema": {
        "indicator": "your_indicator",
        "period": "{{period}}"
      }
    }
  }
}
```

### 2. Test It

```python
result = builder.run("Your custom indicator with 15 period")
```

That's it! The system automatically picks it up.

---

## Next Steps

1. ✅ Run all tests
2. ✅ Run examples
3. ✅ Try custom requests
4. ✅ Start API server
5. ✅ Test API endpoints
6. ✅ Review execution traces
7. ✅ Switch to OpenAI
8. ✅ Showcase to employers

---

## Getting Help

Check these files:
- `README.md` - Full documentation
- `ARCHITECTURE.md` - System design
- `PROJECT_SUMMARY.md` - High-level overview
- `examples/execution_traces/` - Real execution logs
