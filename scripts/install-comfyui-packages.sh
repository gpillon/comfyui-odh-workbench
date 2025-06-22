#!/bin/bash

set -e

# Script to install custom ComfyUI packages at build time
# This script reads from the build-config.yaml file

COMFYUI_DIR="/opt/app-root/src/ComfyUI"
CONFIG_FILE="/opt/app-root/src/build-config.yaml"

# Ensure ComfyUI directory exists
if [ ! -d "$COMFYUI_DIR" ]; then
    echo "Error: ComfyUI directory not found at $COMFYUI_DIR"
    exit 1
fi

# Ensure custom_nodes directory exists
mkdir -p "$COMFYUI_DIR/custom_nodes"

# Function to parse YAML and install packages
install_packages() {
    # Check if yq is installed
    if ! command -v yq &> /dev/null; then
        echo "yq is not installed. Installing..."
        wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
        chmod +x /usr/local/bin/yq
    fi

    # Get the number of packages
    local package_count=$(yq '.comfyui_packages | length' "$CONFIG_FILE")
    
    echo "Found $package_count ComfyUI packages to install"
    
    # Iterate through each package
    for ((i=0; i<$package_count; i++)); do
        local name=$(yq ".comfyui_packages[$i].name" "$CONFIG_FILE")
        local repo=$(yq ".comfyui_packages[$i].repo" "$CONFIG_FILE")
        local path=$(yq ".comfyui_packages[$i].path" "$CONFIG_FILE")
        local enabled=$(yq ".comfyui_packages[$i].enabled" "$CONFIG_FILE")
        
        # Skip if not enabled
        if [ "$enabled" != "true" ]; then
            echo "Skipping disabled package: $name"
            continue
        fi
        
        echo "Installing ComfyUI package: $name from $repo"
        
        # Clone the repository
        if [ -d "$COMFYUI_DIR/$path" ]; then
            echo "Package already exists at $path, updating..."
            cd "$COMFYUI_DIR/$path"
            git pull
        else
            echo "Cloning $repo to $path..."
            git clone "$repo" "$COMFYUI_DIR/$path"
        fi
        
        # Install Python requirements if they exist
        if [ -f "$COMFYUI_DIR/$path/requirements.txt" ]; then
            echo "Installing Python requirements for $name..."
            pip install -r "$COMFYUI_DIR/$path/requirements.txt"
        fi
    done
}

# Install packages
install_packages

echo "ComfyUI packages installation completed" 