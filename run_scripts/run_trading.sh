#!/bin/bash

# Script: run_trading.sh
# Description: Runs the Crypto Trading script `test.py`.
# Usage: ./run_trading.sh

# --- Configuration ---
PROJECT_ROOT="/Users/nathanielislas/PycharmProjects/CryptoTrading"  # Root directory of your project
VENV_NAME="venv"  # Virtual environment name
SCRIPT_PATH="src/strategy_execution/test.py"  # Path to your trading script

# --- Error Handling ---
set -e  # Exit immediately if a command fails

# --- Navigation ---
echo "Navigating to project root: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

# --- Virtual Environment ---
echo "Activating virtual environment: ${VENV_NAME}"
if [ -d "${VENV_NAME}" ]; then
  source "${VENV_NAME}/bin/activate"
else
  echo "Virtual environment '${VENV_NAME}' not found. Please create it first."
  exit 1
fi

# --- Add Project Root to PYTHONPATH ---
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# --- Run the Trading Script ---
echo "Starting trading script: ${SCRIPT_PATH}"
python3 "$SCRIPT_PATH"

# --- Deactivate Virtual Environment ---
echo "Deactivating virtual environment."
deactivate