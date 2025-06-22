#!/bin/bash

set -e

# Change to the ComfyUI directory
cd /opt/app-root/src/ComfyUI

# Fix permissions for OpenShift
if [ "$(id -u)" -ne 0 ]; then
    echo "Setting correct permissions for non-root user..."
    find /opt/app-root/src/ComfyUI -type d -exec chmod 775 {} \;
    find /opt/app-root/src/ComfyUI -type f -exec chmod 664 {} \;
    chmod +x /opt/app-root/src/ComfyUI/main.py
fi

# Start ComfyUI
echo "Starting ComfyUI..."
python main.py --listen 0.0.0.0 --port ${PORT:-8080} "$@" 