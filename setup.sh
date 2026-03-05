#!/bin/bash
# Quick Setup Script for Clara AI Automation Pipeline
# Mac/Linux Bash Script

echo "=========================================="
echo "Clara AI Automation Pipeline Setup"
echo "=========================================="
echo ""

# Check Python installation
echo "[1/6] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10+ from https://python.org"
    exit 1
fi
python3 --version
echo ""

# Create virtual environment
echo "[2/6] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully"
fi
echo ""

# Activate virtual environment and install dependencies
echo "[3/6] Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully"
echo ""

# Create .env file if it doesn't exist
echo "[4/6] Setting up environment variables..."
if [ -f ".env" ]; then
    echo ".env file already exists, skipping..."
else
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Please edit .env file and add your OpenRouter API key"
    echo "Get your free API key from: https://openrouter.ai/keys"
    echo ""
    echo "Opening .env file..."
    sleep 2
    ${EDITOR:-nano} .env
fi
echo ""

# Create necessary directories
echo "[5/6] Creating directories..."
mkdir -p outputs/accounts
mkdir -p logs
mkdir -p database
echo "Directories created"
echo ""

# Test installation
echo "[6/6] Testing installation..."
python -c "from scripts.utils import llm_client; print('LLM client loaded successfully')"
if [ $? -ne 0 ]; then
    echo "WARNING: Could not load LLM client. Check your .env configuration."
else
    echo "Installation test passed"
fi
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Ensure your .env file has a valid API key"
echo "2. Run: python scripts/batch_process.py --mode demo"
echo ""
echo "For full instructions, see QUICKSTART.md"
echo ""
