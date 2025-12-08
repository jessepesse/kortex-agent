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

# Check if npm is installed (needed for React frontend)
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js and npm first."
    echo ""
    echo "On Arch: sudo pacman -S nodejs npm"
    echo "On Debian/Ubuntu: sudo apt install nodejs npm"
    echo "On Fedora: sudo dnf install nodejs npm"
    exit 1
fi

echo "✓ npm found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Install Python dependencies in virtual environment
echo "📦 Installing Python dependencies..."
./venv/bin/pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend && npm install && cd ..

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
