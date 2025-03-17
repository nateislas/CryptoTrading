#!/bin/bash
# Print the full script path and working directory
echo "Starting Crypto Dashboard..."
echo "Script Location: $(realpath "$0")"
echo "Current Working Directory: $(pwd)"
# Navigate to the project root directory
cd "$(dirname "$0")"
# Print environment details
echo "Using Python: $(which python3)"
python3 --version
# Activate the virtual environment (if it exists)
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found! Running without it."
fi
# Set PYTHONPATH to the parent of `src` (project root)
export PYTHONPATH=$(pwd)
echo "PYTHONPATH set to: $PYTHONPATH"
# Run the dashboard using the `-m` flag to treat it as a package module
echo "Launching Dashboard..."
python3 -m src.dashboard.app