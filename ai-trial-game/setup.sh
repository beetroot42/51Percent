#!/bin/bash
# AI Trial Game - environment setup script
# Purpose: install dependencies and tools

set -e  # exit on error

echo "============================================"
echo "  AI Trial Game - environment setup"
echo "============================================"
echo ""

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Unable to detect OS${NC}"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# 1. Python and pip
echo "========== [1/4] Python tools =========="
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}OK${NC} Python3: $(python3 --version)"
else
    echo -e "${RED}ERROR${NC} Python3 not installed"
    exit 1
fi

if python3 -m pip --version &> /dev/null; then
    echo -e "${GREEN}OK${NC} pip installed"
else
    echo -e "${YELLOW}WARN${NC} pip not installed, installing..."

    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt update
        sudo apt install -y python3-pip python3-venv
    elif [ "$OS" = "fedora" ] || [ "$OS" = "rhel" ]; then
        sudo dnf install -y python3-pip python3-virtualenv
    elif [ "$OS" = "arch" ]; then
        sudo pacman -S --noconfirm python-pip python-virtualenv
    else
        echo -e "${YELLOW}WARN${NC} Unknown OS, trying ensurepip"
        python3 -m ensurepip --default-pip
    fi

    echo -e "${GREEN}OK${NC} pip installed"
fi

# 2. Virtual environment
echo ""
echo "========== [2/4] Virtual environment =========="
if [ -d "venv" ]; then
    echo -e "${YELLOW}WARN${NC} venv already exists"
else
    python3 -m venv venv
    echo -e "${GREEN}OK${NC} venv created"
fi

source venv/bin/activate
echo -e "${GREEN}OK${NC} venv activated"

# 3. Python dependencies
echo ""
echo "========== [3/4] Python dependencies =========="
if [ -f "backend/requirements.txt" ]; then
    pip install -q -r backend/requirements.txt
    echo -e "${GREEN}OK${NC} dependencies installed"
else
    echo -e "${RED}ERROR${NC} backend/requirements.txt not found"
    exit 1
fi

# 4. Foundry (optional)
echo ""
echo "========== [4/4] Foundry =========="
if command -v anvil &> /dev/null && command -v forge &> /dev/null; then
    echo -e "${GREEN}OK${NC} Foundry installed"
    anvil --version | head -1
else
    echo -e "${YELLOW}WARN${NC} Foundry not installed (voting disabled)"
    echo ""
    echo "Install Foundry (optional):"
    echo "  curl -L https://foundry.paradigm.xyz | bash"
    echo "  foundryup"
fi

# Done
echo ""
echo "============================================"
echo -e "${GREEN}Environment setup complete${NC}"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Configure .env:"
echo "     cp backend/.env.example backend/.env"
echo "     edit backend/.env to add API key"
echo ""
echo "  2. Start the game:"
echo "     source venv/bin/activate"
echo "     python start.py"
echo ""
