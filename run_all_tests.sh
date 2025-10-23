#!/bin/bash
echo "=========================================="
echo "Running All MCP Server Tests"
echo "=========================================="
echo ""

echo "1. pfSense MCP Tests"
echo "----------------------------------------"
cd pfsense-mcp
pytest tests/test_validation.py -v --tb=no 2>&1 | tail -5
cd ..
echo ""

echo "2. iDRAC MCP Tests"
echo "----------------------------------------"
cd idrac-mcp
pytest tests/test_basic.py -v --tb=no 2>&1 | tail -5
cd ..
echo ""

echo "3. Proxmox MCP Tests"
echo "----------------------------------------"
cd proxmox-mcp
pytest tests/test_unit.py::TestValidationUtils -v --tb=no 2>&1 | tail -5
cd ..
echo ""

echo "=========================================="
echo "Test Summary Complete"
echo "=========================================="
