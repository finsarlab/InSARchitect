#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}InSARchitect Installation Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# verify if pixi is installed
if ! command -v pixi &> /dev/null; then
    echo -e "${YELLOW}Pixi not found. Installing pixi...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://pixi.sh/install.sh | bash
        export PATH="$HOME/.pixi/bin:$PATH"
    else
        echo -e "${RED}Unsupported OS. Please install pixi manually from https://pixi.sh${NC}"
        exit 1
    fi
    
    # verify pixi installation
    if ! command -v pixi &> /dev/null; then
        echo -e "${RED}Failed to install pixi. Please install manually.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Pixi installed successfully!${NC}"
else
    echo -e "${GREEN}Pixi is already installed${NC}"
fi

cd "${PROJECT_ROOT}"

echo ""
echo -e "${GREEN}Creating pixi environment...${NC}"
pixi install

echo ""
echo -e "${GREEN}Installing InSARchitect package in editable mode...${NC}"
pixi run install

echo ""
echo -e "${GREEN}Installing additional InSAR packages (ISCE2, MintPy, MiaplPy)...${NC}"
pixi run install-extra

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To activate the environment, run:"
echo -e "  ${YELLOW}pixi shell${NC}"
echo ""
echo "Or run commands directly with:"
echo -e "  ${YELLOW}pixi run insarchitect${NC}"
echo ""

