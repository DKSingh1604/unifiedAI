#!/bin/bash

# Electric Vehicle Analytics - Setup Script
# This script automates the setup process

set -e  # Exit on error

echo "================================================================================"
echo "Electric Vehicle Analytics - Setup Script"
echo "================================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo -e "${RED}❌ Python 3.11+ required. Found: $python_version${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python $python_version${NC}"
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Setup .env file
echo ""
echo "⚙️  Setting up environment variables..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists. Skipping...${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created from .env.example${NC}"
    echo -e "${YELLOW}📝 Please edit .env file with your configuration${NC}"
fi

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p data/raw
mkdir -p logs
echo -e "${GREEN}✅ Directories created${NC}"

# Check MongoDB
echo ""
echo "🔍 Checking MongoDB..."
if command -v mongod &> /dev/null; then
    echo -e "${GREEN}✅ MongoDB found${NC}"
else
    echo -e "${RED}❌ MongoDB not found. Please install MongoDB:${NC}"
    echo "   macOS: brew install mongodb-community@7.0"
    echo "   Ubuntu: sudo apt install mongodb"
fi

# Check if CSV exists
echo ""
echo "📊 Checking for CSV file..."
if [ -f "data/raw/Electric_Vehicle_Population_Data.csv" ]; then
    echo -e "${GREEN}✅ CSV file found${NC}"
else
    echo -e "${YELLOW}⚠️  CSV file not found${NC}"
    echo "   Please place Electric_Vehicle_Population_Data.csv in data/raw/"
fi

echo ""
echo "================================================================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Ensure MongoDB is running"
echo ""
echo "3. Place CSV file in data/raw/"
echo ""
echo "4. Run the ETL pipeline:"
echo "   python scripts/run_pipeline.py"
echo ""
echo "5. Start the API server:"
echo "   python scripts/run_server.py"
echo ""
echo "6. Visit the API docs:"
echo "   http://localhost:8000/api/docs"
echo ""
echo "================================================================================"
