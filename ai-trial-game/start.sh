#!/bin/bash
# AI Trial Game - startup script

cd "$(dirname "$0")/backend"

echo "================================"
echo "  AI Trial Game"
echo "================================"
echo ""
echo "Starting server..."
echo ""

python3 main.py
