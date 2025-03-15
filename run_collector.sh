#!/bin/bash

# Script: run_collector.sh
# Description: Runs collect_ticker_data.py with multiple tickers as a single process using asyncio.
# Usage: ./run_collector.sh --tickers BTC-USD ETH-USD --interval 1s --batch_size 250

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
BATCH_SIZE=250  # Default batch size

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

# Convert ticker array to a comma-separated string
TICKER_LIST=$(IFS=,; echo "${TICKERS[*]}")

# --- Run the Python script with multiple tickers ---
echo "Starting data collection for tickers: ${TICKERS[*]}"
python3 -m src.data_processing.collect_ticker_data --tickers "$TICKER_LIST" --interval "$INTERVAL" --batch_size "$BATCH_SIZE"

# Deactivate the virtual environment
echo "Deactivating virtual environment."
deactivate