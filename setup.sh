#!/bin/bash
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Copying .env template..."
cp .env.example .env

echo ""
echo "============================================"
echo "Setup complete! Next steps:"
echo "  1. Install Ollama from https://ollama.com"
echo "  2. Run: ollama pull gemma3:4b"
echo "  3. Edit .env with your Telegram token"
echo "  4. Edit config.yaml with your companies"
echo "  5. Run: python main.py"
echo "============================================"