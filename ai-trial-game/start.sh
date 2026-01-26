#!/bin/bash
# AI Trial Game - 启动脚本

cd "$(dirname "$0")/backend"

echo "================================"
echo "  AI Trial Game - AI审判"
echo "================================"
echo ""
echo "启动服务器..."
echo ""

python3 main.py
