#!/bin/bash

# Script: run_collector.sh
# Description: Runs the collect_ticker_data.py script for multiple tickers simultaneously.
# Usage: ./run_collector.sh --tickers BTC-USD ETH-USD SOL-USD --interval 1s --batch_size 185

# --- Configuration ---
PROJECT_ROOT="/Users/nathanielislas/PycharmProjects/CryptoTrading"  # Replace with actual path
VENV_NAME="venv"  # Virtual environment name
SCRIPT_PATH="src/data_processing/collect_ticker_data.py"

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

# --- Parse Arguments ---
TICKERS=()
INTERVAL="1s"  # Default interval
BATCH_SIZE=120  # Default batch size

# Process command-line arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --tickers) shift; while [[ "$#" -gt 0 && ! "$1" =~ ^-- ]]; do TICKERS+=("$1"); shift; done ;;
        --interval) INTERVAL="$2"; shift 2 ;;
        --batch_size) BATCH_SIZE="$2"; shift 2 ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

# Ensure at least one ticker is provided
if [ ${#TICKERS[@]} -eq 0 ]; then
    echo "Error: No tickers provided. Use --tickers TICKER1 TICKER2 ..."
    exit 1
fi

# --- Run the Script for Each Ticker ---
echo "Starting data collection for tickers: ${TICKERS[*]}"

for TICKER in "${TICKERS[@]}"; do
    echo "Launching collection for $TICKER with interval $INTERVAL and batch size $BATCH_SIZE"
    python3 -m src.data_processing.collect_ticker_data --ticker "$TICKER" --interval "$INTERVAL" --batch_size "$BATCH_SIZE" &
done

# Wait for all background jobs to finish
wait

echo "All ticker collection processes have completed."

# Deactivate the virtual environment (optional)
echo "Deactivating virtual environment."
deactivate
