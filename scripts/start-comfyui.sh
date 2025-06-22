#!/bin/bash

set -e

# Change to the ComfyUI directory
cd /opt/app-root/ComfyUI

# Install ComfyUI Manager if not already installed and DISABLE_MANAGER env variable is not equal to "true"
if [ ! -d "custom_nodes/ComfyUI-Manager" ] && [ "${DISABLE_MANAGER}" != "true" ]; then
    echo "Installing ComfyUI Manager..."
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
fi

# Start ComfyUI
echo "Starting ComfyUI on port ${PORT:-8080}..."
python main.py --listen 0.0.0.0 --port ${PORT:-8080} "$@" 