#!/bin/bash

# --- Configuration ---
PROJECT_ROOT="/Users/nathanielislas/PycharmProjects/CryptoTrading"  # Replace with actual path
VENV_NAME="venv"  # Virtual environment name

# --- Error Handling ---
set -e  # Exit on error

# Print the full script path and working directory
echo "Starting Portfolio Monitor..."
echo "Script Location: $(realpath "$0")"
echo "Current Working Directory: $(pwd)"

# --- Navigation ---
echo "Navigating to the project root: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

# Print environment details
echo "Using Python: $(which python3)"
python3 --version

# --- Virtual Environment ---
echo "Activating virtual environment: ${VENV_NAME}"
if [ -d "${VENV_NAME}" ]; then
  source "${VENV_NAME}/bin/activate"
else
  echo "Virtual environment '${VENV_NAME}' not found. Please create it first."
  exit 1
fi

# --- Python Path ---
# Set PYTHONPATH to the project root (parent of `src`)
export PYTHONPATH=$(pwd)
echo "PYTHONPATH set to: $PYTHONPATH"

# Run the Python script
echo "Starting portfolio monitoring..."
python3 src/portfolio_analytics/portfolio_monitor.py

echo "Portfolio monitoring completed."