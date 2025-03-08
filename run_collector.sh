#!/bin/bash

# Script: run_collector.sh
# Description: Sets up the environment and runs the collect_ticker_data.py script.
# Example Usage:  ./run_collector.sh --ticker BTC-USD --interval 1s

# --- Configuration ---
PROJECT_ROOT="/Users/nathanielislas/PycharmProjects/CryptoTrading"  # Replace with the actual path if it's different
VENV_NAME="venv" # Name of your virtual enviornment
SCRIPT_PATH="src/data_processing/collect_ticker_data.py"

# --- Error Handling ---
set -e  # Exit immediately if a command exits with a non-zero status

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

# --- Run the Script ---
echo "Running the data collection script:"
# Check if the script exists
if [ -f "${SCRIPT_PATH}" ]; then
    ./venv/bin/python3 -m src.data_processing.collect_ticker_data "$@" #"$@" allows to pass arguments.
    #the same can be done without using ./venv/bin/python3:
    #python3 -m src.data_processing.collect_ticker_data "$@"
else
  echo "Script '${SCRIPT_PATH}' not found."
  exit 1
fi

echo "Data collection script completed."

# Deactivate the virtual environment (optional)
echo "Deactivating virtual environment."
deactivate