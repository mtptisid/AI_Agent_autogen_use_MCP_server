#!/bin/bash

# Ensure script fails on any error
set -e

# Check if virtual environment exists, create if it doesn't
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install requirements if not already installed
if ! pip freeze | grep -q "requests"; then
    echo "Installing required packages..."
    pip install requests
fi

# Run the agent
echo "Starting MCP Agent..."
python ai_agent.py
