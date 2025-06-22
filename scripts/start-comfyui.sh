#!/bin/bash

set -e

# Create user site-packages directory in the mounted volume
USER_SITE_PACKAGES="/opt/app-root/src/.local/lib/python3.11/site-packages"
mkdir -p "$USER_SITE_PACKAGES"

# Copy existing packages from system site-packages to user site-packages if not already done
COPY_MARKER="/opt/app-root/src/.packages_copied"
if [ ! -f "$COPY_MARKER" ]; then
    echo "Copying system packages to user site-packages..."
    # Copy all packages from system site-packages to user site-packages
    if [ -d "/opt/app-root/lib64/python3.11/site-packages" ]; then
        cp -r /opt/app-root/lib64/python3.11/site-packages/* "$USER_SITE_PACKAGES/" 2>/dev/null || true
    fi
    # Also copy from lib (without 64) if it exists
    if [ -d "/opt/app-root/lib/python3.11/site-packages" ]; then
        cp -r /opt/app-root/lib/python3.11/site-packages/* "$USER_SITE_PACKAGES/" 2>/dev/null || true
    fi
    touch "$COPY_MARKER"
    echo "Package copying completed."
fi

# Configure Python to use user site-packages
export PYTHONPATH="$USER_SITE_PACKAGES:$PYTHONPATH"

# Configure pip to use target directory only (simplest approach to avoid conflicts)
# Remove any potentially conflicting environment variables
unset PIP_USER
unset PIP_PREFIX
unset PYTHONUSERBASE

# Create pip configuration directory and file with minimal config
PIP_CONFIG_DIR="/opt/app-root/src/.config/pip"
mkdir -p "$PIP_CONFIG_DIR"
cat > "$PIP_CONFIG_DIR/pip.conf" << EOF
[install]
target = /opt/app-root/src/.local/lib/python3.11/site-packages
EOF

# Create model subdirectories in the mounted volume
echo "Creating model directories..."
mkdir -p /opt/app-root/src/models/checkpoints \
    /opt/app-root/src/models/clip \
    /opt/app-root/src/models/clip_vision \
    /opt/app-root/src/models/configs \
    /opt/app-root/src/models/controlnet \
    /opt/app-root/src/models/diffusion_models \
    /opt/app-root/src/models/unet \
    /opt/app-root/src/models/embeddings \
    /opt/app-root/src/models/loras \
    /opt/app-root/src/models/upscale_models \
    /opt/app-root/src/models/vae \
    /opt/app-root/src/models/gligen \
    /opt/app-root/src/input \
    /opt/app-root/src/output

# Change to the ComfyUI directory
cd /opt/app-root/ComfyUI

# Install ComfyUI Manager if not already installed and DISABLE_MANAGER env variable is not equal to "true"
if [ ! -d "custom_nodes/ComfyUI-Manager" ] && [ "${DISABLE_MANAGER}" != "true" ]; then
    echo "Installing ComfyUI Manager..."
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
fi

# Start ComfyUI
echo "Starting ComfyUI on port ${PORT:-8888}..."
python main.py --listen 0.0.0.0 --port ${PORT:-8888} "$@" 