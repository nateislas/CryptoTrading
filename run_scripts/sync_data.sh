#!/bin/bash

# Configuration
JETBOT_USER="jetbot"  # Jetson Nano username
JETBOT_IP="10.0.0.75"  # Replace with your Jetson's actual IP
JETBOT_DATA_PATH="/home/jetbot/Workspace/CryptoTrading/data"
LOCAL_DATA_PATH="/Users/nathanielislas/PycharmProjects/CryptoTrading/data"

# Ensure the local directory exists
mkdir -p "$LOCAL_DATA_PATH"

# Sync data from Jetson Nano to local machine
rsync -avz --progress --delete "$JETBOT_USER@$JETBOT_IP:$JETBOT_DATA_PATH/" "$LOCAL_DATA_PATH/"

echo "Sync complete: Data from Jetson Nano has been copied to $LOCAL_DATA_PATH"
