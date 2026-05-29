#!/bin/bash

# CFO-Bot Setup Script
# Designed for macOS systems to set up a virtual environment and launch VS Code

# Colorful Terminal Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================================================${NC}"
echo -e "${GREEN}                  💰 CFO-Bot: Relational Text-to-SQL Setup 💰            ${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo ""

# 1. Check Python Version
echo -e "${BLUE}[1/4] Checking python3 installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed on your system.${NC}"
    echo -e "Please install Python 3.9+ and try again."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "Found Python ${GREEN}${PY_VERSION}${NC}"

# 2. Creating Virtual Environment
echo -e "\n${BLUE}[2/4] Creating a clean Python virtual environment (venv)...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Warning: 'venv' directory already exists. Re-using existing environment.${NC}"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment 'venv' successfully created!${NC}"
fi

# 3. Activating and Installing Dependencies
echo -e "\n${BLUE}[3/4] Activating venv and installing packages...${NC}"
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

echo -e "Upgrading pip..."
python3 -m pip install --upgrade pip

echo -e "Installing requirements (Streamlit, Pandas, Matplotlib, Plotly, Gemini AI, sqlparse)..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Package installation failed.${NC}"
    exit 1
fi

echo -e "${GREEN}Dependencies installed successfully!${NC}"

# 4. Success and Instructions
echo ""
echo -e "${BLUE}========================================================================${NC}"
echo -e "${GREEN}🎉 Setup Complete! Your CFO-Bot environment is fully configured! 🎉${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo ""
echo -e "${YELLOW}To run the app from VS Code:${NC}"
echo -e "1. Open this folder (${BLUE}cfo-bot${NC}) in VS Code."
echo -e "2. Press ${GREEN}F5${NC} to start debugging (we have set up .vscode launch settings for you)."
echo -e "3. Or run these commands in the terminal:"
echo -e "   ${BLUE}source venv/bin/activate${NC}"
echo -e "   ${BLUE}streamlit run app.py${NC}"
echo ""
echo -e "${GREEN}Enjoy exploring your secure Natural Language to SQL dashboard!${NC}"
echo -e "${BLUE}========================================================================${NC}"
