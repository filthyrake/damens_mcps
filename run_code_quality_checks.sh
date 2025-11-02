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
    
    # Activate virtual environment (platform-specific)
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
    else
        echo "  ⚠ Failed to find virtual environment activation script"
        cd ..
        return
    fi
    
    # Install dependencies
    echo "Installing dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt 2>/dev/null || echo "  ⚠ Warning: Some dependencies from requirements.txt failed to install"
    fi
    # Pin versions to match pre-commit config
    if ! pip install -q 'black>=24.1.0' 'isort>=5.13.0' 'flake8>=7.0.0' 'mypy>=1.8.0' 'bandit>=1.7.6' 'safety>=3.0.0' 'interrogate>=1.5.0' 2>/dev/null; then
        echo "  ⚠ Warning: Some quality tools failed to install, checks may not run properly"
    fi
    
    # Check which directories exist
    DIRS=""
    [ -d "src" ] && DIRS="$DIRS src/"
    [ -d "tests" ] && DIRS="$DIRS tests/"
    
    if [ -z "$DIRS" ]; then
        echo "  ⚠ No src/ or tests/ directories found, skipping checks"
        cd ..
        return
    fi
    
    # Run checks
    echo ""
    echo "1. Format check with black..."
    black --check "$DIRS" --line-length=120 || echo "  ⚠ Black found formatting issues"
    
    echo ""
    echo "2. Import sort check with isort..."
    isort --check-only "$DIRS" --profile black --line-length=120 || echo "  ⚠ Isort found import issues"
    
    echo ""
    echo "3. Lint with flake8..."
    flake8 "$DIRS" --max-line-length=120 --extend-ignore=E203,W503 --statistics || echo "  ⚠ Flake8 found linting issues"
    
    echo ""
    echo "4. Type check with mypy..."
    [ -d "src" ] && mypy src/ --ignore-missing-imports --no-strict-optional || echo "  ⚠ Mypy found type issues or src/ not found"
    
    echo ""
    echo "5. Security scan with bandit..."
    [ -d "src" ] && bandit -r src/ -ll -f txt || echo "  ⚠ Bandit found security issues or src/ not found"
    
    echo ""
    echo "6. Dependency vulnerability scan with safety..."
    safety check --json || echo "  ⚠ Safety check skipped or found issues"
    
    echo ""
    echo "7. Documentation coverage with interrogate..."
    [ -d "src" ] && interrogate src/ -vv --fail-under=40 || echo "  ⚠ Interrogate found documentation issues or src/ not found"
    
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
