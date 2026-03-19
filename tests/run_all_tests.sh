#!/bin/bash
# Run all automated tests for the SCIM 2.0 Service Provider
# This script runs all test suites and generates coverage reports

set -e  # Exit on error

echo "=========================================="
echo "SCIM 2.0 Service Provider - Test Suite"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed"
    echo "Please run: pip install -r tests/requirements.txt"
    exit 1
fi

# Set Python path to include project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Running all tests with coverage..."
echo ""

# Run all tests with coverage
pytest tests/ \
    --verbose \
    --tb=short \
    --cov=. \
    --cov-report=html:tests/htmlcov \
    --cov-report=term-missing \
    --cov-report=json:tests/coverage.json \
    -v

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Coverage report generated in: tests/htmlcov/index.html"
echo "JSON coverage report: tests/coverage.json"
echo ""
echo "To view HTML coverage report:"
echo "  open tests/htmlcov/index.html"
echo ""
echo "To run specific test suites:"
echo "  pytest tests/test_scim_users_api.py -v"
echo "  pytest tests/test_scim_groups_api.py -v"
echo "  pytest tests/test_scim_discovery_api.py -v"
echo "  pytest tests/test_supporting_data_complete.py -v"
echo ""
echo "To run tests with specific markers:"
echo "  pytest -m integration -v"
echo "  pytest -m security -v"
echo ""

# Made with Bob
