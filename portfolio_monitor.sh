#!/bin/bash

# --- Configuration ---
PROJECT_ROOT="/Users/nathanielislas/PycharmProjects/CryptoTrading"  # Replace with actual path
VENV_NAME="venv"  # Virtual environment name

# --- Error Handling ---
set -e  # Exit on error

# --- Navigation ---
echo "Navigating to the project root: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

# --- Virtual Environment ---
echo "Activating virtual environment: ${VENV_NAME}"
if [ -d "${VENV_NAME}" ]; then
  source "${VENV_NAME}/bin/activate"
else
  echo "Virtual environment '${VENV_NAME}' not found. Please create it first."
  exit 1
fi

# Run the Python script
echo "Starting portfolio monitoring..."
python src/portfolio_analytics/portfolio_monitor.py

echo "Portfolio monitoring completed."