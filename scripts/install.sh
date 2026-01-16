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

echo -e "${GREEN}Creating pixi environment...${NC}"
pixi install

echo -e "${GREEN}Installing InSARchitect package in editable mode...${NC}"
pixi run install

echo -e "${GREEN}Installing additional InSAR packages (ISCE2, MintPy, MiaplPy)...${NC}"
pixi run install-extra

echo -e "${GREEN}Generating pixi shell hook${NC}"

pixi shell-hook > "${PROJECT_ROOT}/activate.sh"

# add the original path 
sed -i 's|^export PATH="|export PATH="$PATH:|' "${PROJECT_ROOT}/activate.sh"

ALIAS_NAME="insarchitect.load"
ALIAS_VALUE="source ${PROJECT_ROOT}/activate.sh"
BASHRC="$HOME/.bashrc"

if grep -qF "alias ${ALIAS_NAME}='${ALIAS_VALUE}'" "$BASHRC"; then
    echo "The alias ${ALIAS_NAME} already exists and is correct"
elif grep -qE "^alias[[:space:]]+${ALIAS_NAME}=" "$BASHRC"; then
    echo "Alias ${ALIAS_NAME} exists but is different. Overwriting..."
    sed -i.bak "s|^alias[[:space:]]\+${ALIAS_NAME}=.*|alias ${ALIAS_NAME}='${ALIAS_VALUE}'|" "$BASHRC"
else
    echo "Creating load alias..."
    echo -e "\nalias ${ALIAS_NAME}='${ALIAS_VALUE}'" >> "$BASHRC"
fi

if grep -qE "^alias insarchitect=" ~/.bashrc; then
    echo "The alias insarchitect already exists"
else
    echo "Creating insarchitect alias..."
    echo -e "\nalias insarchitect='pixi run insarchitect'" >> ~/.bashrc
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"


echo -e "\n  ${YELLOW}Close your current terminal and open a new bash session${NC}\n"

echo "To activate the environment, run:"
echo -e "  ${YELLOW}insarchitect.load${NC}"
echo "Run commands directly with:"
echo -e "  ${YELLOW}insarchitect${NC}"

