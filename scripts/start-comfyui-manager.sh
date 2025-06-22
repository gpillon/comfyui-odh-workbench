#!/bin/bash

set -e

# Change to the ComfyUI directory
cd /opt/app-root/src/ComfyUI

# Install ComfyUI Manager if not already installed
if [ ! -d "custom_nodes/ComfyUI-Manager" ]; then
    echo "Installing ComfyUI Manager..."
    mkdir -p custom_nodes
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
fi

# Start ComfyUI
echo "Starting ComfyUI..."
python main.py --listen 0.0.0.0 --port ${PORT:-8080} "$@" 