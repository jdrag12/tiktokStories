#!/usr/bin/env bash
set -euo pipefail

echo "=== TikTok Story Bot — Setup ==="

# Create virtualenv
if [ ! -d ".venv" ]; then
    echo "[1/3] Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "[1/3] Virtual environment already exists, skipping."
fi

# Activate and install dependencies
echo "[2/3] Installing dependencies from requirements.txt..."
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Copy .env.example to .env if not already present
echo "[3/3] Setting up .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
else
    echo "  .env already exists, skipping."
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Fill in your API keys in .env:"
echo "       ANTHROPIC_API_KEY   → https://console.anthropic.com"
echo "       ELEVENLABS_API_KEY  → https://elevenlabs.io"
echo "       PEXELS_API_KEY      → https://www.pexels.com/api"
echo ""
echo "  2. (Optional) Place Impact.ttf in assets/fonts/ for best subtitle rendering."
echo "     Without it, PIL's default font will be used as a fallback."
echo ""
echo "  3. Activate the virtualenv and run:"
echo "       source .venv/bin/activate"
echo "       python scripts/main.py"
