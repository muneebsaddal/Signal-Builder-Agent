# Signal Builder Agent

**Production-grade AI agent that converts natural language into structured trading signals using LangGraph.**

Solves the "schema explosion problem" by using Intermediate Representation (IR) to decouple LLM outputs from complex domain schemas.

---

## Architecture

```
User Request (natural language)
    ↓
Intent Classifier → Determine signal type
    ↓
IR Generator → Create minimal IR
    ↓
IR Validator → Check schema compliance
    ↓
Schema Resolver → Map IR → Full Schema
    ↓
Output + Execution Trace
```

**Key Innovation**: LLM outputs tiny IR (~10 lines), backend resolves to full schemas (avoiding 8000+ schema context problem).

---

## Project Structure

```
signal-builder-agent/
├── schemas/
│   ├── ir_schema.py          # Pydantic IR models
│   ├── registry.json         # 25+ signal definitions
│   └── resolver.py           # IR → schema mapping
├── nodes/
│   ├── classifier.py         # Intent classification
│   ├── ir_generator.py       # Natural language → IR
│   ├── validator.py          # IR validation
│   └── resolver_node.py      # Schema resolution
├── graph.py                  # LangGraph state machine
├── api.py                    # FastAPI REST interface
├── llm_config.py            # LLM provider config (Ollama/OpenAI)
├── tests/
│   └── test_all.py          # Test suite
└── examples/
    └── run_examples.py       # Demo script
```

---

## Features

✅ **Deterministic AI Pipeline** - State-based, reproducible execution  
✅ **Schema Governance** - Strict validation with retry logic  
✅ **LangGraph Architecture** - Production-grade agent graphs  
✅ **Dual LLM Support** - Ollama (free) + OpenAI (showcase)  
✅ **Execution Tracing** - Complete audit trail of every step  
✅ **25+ Trading Signals** - Indicators, conditions, strategies  

---

## Requirements

- Python 3.10+
- Ollama (for free local LLM) OR OpenAI API key
- Dependencies: See `requirements.txt`

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure LLM Provider

**Option A: Ollama (Free, Local)**

Install Ollama: https://ollama.ai

```bash
# Pull model (runs on CPU)
ollama pull llama3.2:3b

# Create .env file
cp .env.example .env
```

Edit `.env`:
```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
```

**Option B: OpenAI (Paid, for Showcase)**

Edit `.env`:
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

---

## Usage

### Run Tests

```bash
python tests/test_all.py
```

### Run Examples

```bash
python examples/run_examples.py
```

Example output:
```
Request: "20-day moving average of closing price"

Intermediate Representation (IR):
  Type: indicator
  Node: MovingAverage
  Params: {'window': 20, 'source': 'price.close'}

Resolved Schema:
{
  "indicator": "moving_average",
  "type": "sma",
  "period": 20,
  "field": "price.close"
}
```

### Start API Server

```bash
python api.py
```

API runs at: `http://localhost:8000`

**Endpoints:**
- `POST /build-signal` - Build signal from natural language
- `GET /list-signals` - List available signals
- `GET /health` - Health check
- `GET /` - API info

**Example API Call:**
```bash
curl -X POST http://localhost:8000/build-signal \
  -H "Content-Type: application/json" \
  -d '{"request": "14-period RSI indicator"}'
```

---

## Example Requests

| Request | Signal Type | Node |
|---------|-------------|------|
| "20-day moving average of closing price" | indicator | MovingAverage |
| "RSI below 30" | condition | IndicatorThreshold |
| "MACD with fast 12, slow 26" | indicator | MACD |
| "Volume spike above 2x average" | condition | VolumeSpike |
| "MA crossover strategy 10 and 20 periods" | strategy | MACrossover |

---

## Key Concepts

### Intermediate Representation (IR)

Minimal structure LLM outputs:

```python
{
  "signal_type": "indicator",
  "node": "MovingAverage",
  "params": {
    "window": 20,
    "source": "price.close"
  }
}
```

### Schema Resolution

IR is resolved to full trading schema:

```python
{
  "indicator": "moving_average",
  "type": "sma",
  "period": 20,
  "field": "price.close",
  "metadata": {...}
}
```

### Execution Tracing

Every step logged:
1. classify_intent
2. generate_ir
3. validate_ir
4. resolve_schema
5. finalize

---

## Why This Matters

**Problem**: LLMs can't handle 8000+ schemas in context window.

**Solution**: 
1. LLM outputs tiny IR (10 lines)
2. Deterministic resolver maps IR → full schema
3. No hallucinations, full validation

**Real-world use case**: Trading platforms, CRM automation, complex config systems.

---

## Switching to OpenAI

For production/showcase, switch provider:

1. Edit `.env`:
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
```

2. Restart services. That's it.

No code changes needed.

---

## Production Considerations

- **Validation**: Max 1 retry on IR validation failure
- **Logging**: Complete execution trace for debugging
- **Error Handling**: Clear error messages with suggestions
- **Determinism**: Low temperature (0.1) for consistent outputs
- **Scalability**: Stateless API, can be containerized

---

## What You Learn

1. **Agent Architecture** - State-based workflows
2. **Deterministic AI** - Validation, retry logic, hard stops
3. **Schema Management** - IR decoupling pattern
4. **Production Design** - Logging, tracing, error handling
5. **LangGraph** - Graph-based agent systems

---

## Next Steps

- Add schema versioning
- Multi-signal composition
- Parameter suggestion (LLM recommends defaults)
- Cost tracking per resolution
- Deploy with Docker

---

## License

MIT
