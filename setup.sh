#!/bin/bash
# Setup script for Kortex Agent

echo "🧠 Setting up Kortex Agent..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✓ Python 3 found"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "⚠️  IMPORTANT: Set your Gemini API key before running:"
echo "   export GEMINI_API_KEY='your-api-key-here'"
echo ""
echo "Get your API key from: https://aistudio.google.com/app/apikey"
echo ""
echo "To run the chatbot:"
echo "   python3 main.py"
echo ""
