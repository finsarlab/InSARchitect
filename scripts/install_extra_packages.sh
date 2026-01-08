#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TOOLS_DIR="${PROJECT_ROOT}/tools"

mkdir -p "${TOOLS_DIR}"

echo -e "${GREEN}Installing additional InSAR packages...${NC}"

# clone repository if it doesn't exist
clone_if_missing() {
    local repo_url=$1
    local repo_name=$2
    local target_dir="${TOOLS_DIR}/${repo_name}"
    
    if [ -d "${target_dir}" ]; then
        echo -e "${YELLOW}${repo_name} already exists, skipping clone...${NC}"
    else
        echo -e "${GREEN}Cloning ${repo_name}...${NC}"
        git clone "${repo_url}" "${target_dir}" || {
            echo -e "${RED}Failed to clone ${repo_name}${NC}"
            return 1
        }
    fi
}

# clone required repositories
echo -e "${GREEN}Cloning repositories...${NC}"
clone_if_missing "git@github.com:finsarlab/MintPy.git" "MintPy"
clone_if_missing "git@github.com:finsarlab/MiaplPy.git" "MiaplPy"
clone_if_missing "git@github.com:finsarlab/isce2.git" "isce2"
clone_if_missing "git@github.com:finsarlab/insarmaps-scripts.git" "insarmaps-scripts"

# uncomment if needed in the future
# clone_if_missing "https://gitlab.com/earthscope/public/sar/ssara_client.git" "ssara_client"

echo -e "${GREEN}Installing packages with pip...${NC}"

# MintPy
if [ -d "${TOOLS_DIR}/MintPy" ]; then
    echo -e "${GREEN}Installing MintPy...${NC}"
    pip install -e "${TOOLS_DIR}/MintPy" || {
        echo -e "${RED}Error: MintPy installation had issues{NC}"
    }
fi

# MiaplPy
if [ -d "${TOOLS_DIR}/MiaplPy" ]; then
    echo -e "${GREEN}Installing MiaplPy...${NC}"
    pip install -e "${TOOLS_DIR}/MiaplPy" || {
        echo -e "${RED}Error: MiaplPy installation had issues{NC}"
    }
fi

# ISCE2
if [ -d "${TOOLS_DIR}/isce2" ]; then
    echo -e "${GREEN}ISCE2 repository cloned.${NC}"
fi

# insarmaps-scripts
if [ -d "${TOOLS_DIR}/insarmaps-scripts" ]; then
    echo -e "${GREEN}insarmaps-scripts repository cloned.${NC}"
fi

echo -e "${GREEN}Additional packages installation completed!${NC}"
echo -e "${YELLOW}Note: Environment variables can be set using:${NC}"
echo -e "${YELLOW}  source scripts/setup_env.sh${NC}"

