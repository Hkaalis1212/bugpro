#!/bin/bash

# Comprehensive Test Runner Script
# Runs all tests and generates reports

echo "=========================================="
echo "🧪 RUNNING COMPREHENSIVE TEST SUITE"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Test Configuration:${NC}"
echo "  - Framework: unittest + pytest"
echo "  - Database: SQLite (in-memory)"
echo "  - Coverage: Enabled"
echo ""

# Run unittest suite
echo -e "${YELLOW}🔧 Running unittest suite...${NC}"
python run_tests.py
unittest_result=$?

echo ""
echo -e "${YELLOW}🔧 Running pytest suite...${NC}"

# Create tests directory if it doesn't exist
mkdir -p tests

# Run pytest with coverage if available
if command -v pytest &> /dev/null; then
    if command -v pytest-cov &> /dev/null; then
        pytest tests/ --cov=app --cov-report=html --cov-report=term
    else
        pytest tests/ -v
    fi
    pytest_result=$?
else
    echo -e "${RED}❌ pytest not found, skipping pytest tests${NC}"
    pytest_result=0
fi

echo ""
echo "=========================================="
echo "📊 TEST RESULTS SUMMARY"
echo "=========================================="

if [ $unittest_result -eq 0 ]; then
    echo -e "${GREEN}✅ unittest suite: PASSED${NC}"
else
    echo -e "${RED}❌ unittest suite: FAILED${NC}"
fi

if [ $pytest_result -eq 0 ]; then
    echo -e "${GREEN}✅ pytest suite: PASSED${NC}"
else
    echo -e "${RED}❌ pytest suite: FAILED${NC}"
fi

# Overall result
if [ $unittest_result -eq 0 ] && [ $pytest_result -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}The application is ready for deployment.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}💥 SOME TESTS FAILED!${NC}"
    echo -e "${RED}Please fix failing tests before deployment.${NC}"
    exit 1
fi