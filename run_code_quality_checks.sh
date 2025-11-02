#!/bin/bash

# Script to run code quality checks locally on all projects
# This mimics what the GitHub Actions workflow does

set -e

echo "=========================================="
echo "Running Code Quality Checks"
echo "=========================================="
echo ""

# Function to run checks for a project
run_checks() {
    local project=$1
    echo ""
    echo "=========================================="
    echo "Checking: $project"
    echo "=========================================="
    
    cd "$project"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -q -r requirements.txt 2>/dev/null || true
    pip install -q flake8 black isort mypy bandit safety interrogate 2>/dev/null || true
    
    # Run checks
    echo ""
    echo "1. Format check with black..."
    black --check src/ tests/ --line-length=120 || echo "  ⚠ Black found formatting issues"
    
    echo ""
    echo "2. Import sort check with isort..."
    isort --check-only src/ tests/ --profile black --line-length=120 || echo "  ⚠ Isort found import issues"
    
    echo ""
    echo "3. Lint with flake8..."
    flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503 --statistics || echo "  ⚠ Flake8 found linting issues"
    
    echo ""
    echo "4. Type check with mypy..."
    mypy src/ --ignore-missing-imports --no-strict-optional || echo "  ⚠ Mypy found type issues"
    
    echo ""
    echo "5. Security scan with bandit..."
    bandit -r src/ -ll -f txt || echo "  ⚠ Bandit found security issues"
    
    echo ""
    echo "6. Dependency vulnerability scan with safety..."
    safety check --json || echo "  ⚠ Safety check skipped or found issues"
    
    echo ""
    echo "7. Documentation coverage with interrogate..."
    interrogate src/ -vv --fail-under=40 || echo "  ⚠ Interrogate found documentation issues"
    
    # Deactivate virtual environment
    deactivate
    
    cd ..
}

# Run checks for each project
for project in pfsense-mcp truenas-mcp idrac-mcp proxmox-mcp; do
    if [ -d "$project" ]; then
        run_checks "$project"
    else
        echo "Warning: $project directory not found, skipping..."
    fi
done

echo ""
echo "=========================================="
echo "Code Quality Checks Complete"
echo "=========================================="
echo ""
echo "Note: Warnings (⚠) indicate areas for improvement but don't fail the checks."
echo "Run individual tools to fix issues:"
echo "  - black src/ tests/ --line-length=120"
echo "  - isort src/ tests/ --profile black --line-length=120"
echo "  - See CODE_QUALITY.md for more details"
