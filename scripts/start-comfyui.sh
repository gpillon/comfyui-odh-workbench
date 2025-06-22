#!/bin/bash

set -e

# Change to the ComfyUI directory
cd /opt/app-root/ComfyUI


# Install ComfyUI Manager if not already installed
if [ ! -d "custom_nodes/ComfyUI-Manager" ]; then
    echo "Installing ComfyUI Manager..."
    mkdir -p custom_nodes
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
fi

# # Fix permissions for OpenShift
# if [ "$(id -u)" -ne 0 ]; then
#     echo "Setting correct permissions for non-root user..."
#     find /opt/app-root/ComfyUI -type d -exec chmod 775 {} \;
#     find /opt/app-root/ComfyUI -type f -exec chmod 664 {} \;
#     chmod +x /opt/app-root/ComfyUI/main.py
# fi

# Start ComfyUI
echo "Starting ComfyUI on port ${PORT:-8080}..."
python main.py --listen 0.0.0.0 --port ${PORT:-8080} "$@" 