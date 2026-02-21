#!/bin/bash

echo "=================================="
echo "Signal Builder Agent - Quick Start"
echo "=================================="
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Please install from: https://ollama.ai"
    echo ""
    echo "After installing, run:"
    echo "  ollama pull llama3.2:3b"
    echo ""
    exit 1
fi

# Check if model is available
if ! ollama list | grep -q "llama3.2:3b"; then
    echo "📥 Pulling llama3.2:3b model..."
    ollama pull llama3.2:3b
fi

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. Run tests:"
echo "   python tests/test_all.py"
echo ""
echo "2. Run examples:"
echo "   python examples/run_examples.py"
echo ""
echo "3. Start API server:"
echo "   python api.py"
echo ""
echo "For OpenAI (showcase mode):"
echo "   Edit .env and set:"
echo "   LLM_PROVIDER=openai"
echo "   OPENAI_API_KEY=your-key"
echo ""
