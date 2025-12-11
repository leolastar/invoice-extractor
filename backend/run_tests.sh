#!/bin/bash
# Script to run backend tests

echo "Running backend tests..."
pytest tests/ -v

echo ""
echo "Tests completed!"

