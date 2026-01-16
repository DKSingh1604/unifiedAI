#!/bin/bash
# Quick verification script for the EV Analytics project

echo "🧪 EV Analytics - Quick Verification"
echo "====================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo "1️⃣  Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   ✓ Python $PYTHON_VERSION"
echo ""

# Step 2: Check if virtual environment is activated
echo "2️⃣  Checking virtual environment..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "   ${GREEN}✓${NC} Virtual environment activated: $VIRTUAL_ENV"
else
    echo -e "   ${YELLOW}⚠${NC}  Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    exit 1
fi
echo ""

# Step 3: Check file structure
echo "3️⃣  Checking project structure..."
REQUIRED_DIRS=("app" "tests" "scripts" "data/raw" "frontend")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "   ${GREEN}✓${NC} $dir/"
    else
        echo -e "   ${RED}✗${NC} $dir/ - Missing!"
    fi
done
echo ""

# Step 4: Check required files
echo "4️⃣  Checking configuration files..."
REQUIRED_FILES=("requirements.txt" "pytest.ini" ".env.example")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $file"
    else
        echo -e "   ${RED}✗${NC} $file - Missing!"
    fi
done
echo ""

# Step 5: Check dependencies
echo "5️⃣  Checking Python dependencies..."
REQUIRED_PACKAGES=("fastapi" "pymongo" "pydantic" "pandas" "pytest")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if pip show "$package" > /dev/null 2>&1; then
        VERSION=$(pip show "$package" | grep Version | awk '{print $2}')
        echo -e "   ${GREEN}✓${NC} $package ($VERSION)"
    else
        echo -e "   ${RED}✗${NC} $package - Not installed!"
        echo "   Run: pip install -r requirements.txt"
    fi
done
echo ""

# Step 6: Check CSV data file
echo "6️⃣  Checking for data file..."
if [ -f "data/raw/Electric_Vehicle_Population_Data.csv" ]; then
    SIZE=$(du -h data/raw/Electric_Vehicle_Population_Data.csv | awk '{print $1}')
    LINES=$(wc -l < data/raw/Electric_Vehicle_Population_Data.csv)
    echo -e "   ${GREEN}✓${NC} CSV file found (Size: $SIZE, Lines: $LINES)"
else
    echo -e "   ${YELLOW}⚠${NC}  CSV file not found"
    echo "   Download from: https://data.wa.gov/Transportation/Electric-Vehicle-Population-Data/"
    echo "   Place in: data/raw/Electric_Vehicle_Population_Data.csv"
fi
echo ""

# Step 7: Run unit tests
echo "7️⃣  Running unit tests (pipeline validation)..."
pytest tests/test_pipeline.py -v --tb=no -q
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} Pipeline tests passed!"
else
    echo -e "   ${RED}✗${NC} Pipeline tests failed!"
fi
echo ""

# Step 8: Check MongoDB
echo "8️⃣  Checking MongoDB connection..."
if command -v mongo &> /dev/null || command -v mongosh &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} MongoDB client installed"
    if pgrep -x mongod > /dev/null; then
        echo -e "   ${GREEN}✓${NC} MongoDB server running"
    else
        echo -e "   ${YELLOW}⚠${NC}  MongoDB server not running"
        echo "   Start with: brew services start mongodb/brew/mongodb-community@7.0"
    fi
else
    echo -e "   ${YELLOW}⚠${NC}  MongoDB client not found"
fi
echo ""

# Summary
echo "📊 Summary"
echo "=========="
echo ""
echo "Next steps to get the project fully working:"
echo ""
echo "1. Start MongoDB (if not running):"
echo "   brew services start mongodb/brew/mongodb-community@7.0"
echo ""
echo "2. Load the data:"
echo "   python scripts/run_pipeline.py"
echo ""
echo "3. Start the API server:"
echo "   python scripts/run_server.py"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "5. Open the dashboard:"
echo "   open http://localhost:8000"
echo ""
echo "6. Run all tests:"
echo "   pytest"
echo ""
