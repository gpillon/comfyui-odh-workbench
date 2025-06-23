#!/bin/bash

set -e

# Generate the extensions configuration file
python3 build/generate_extensions_config.py --config build-config.yaml --output /tmp/comfyui-extensions.json

# Display the generated configuration
echo "Generated ComfyUI extensions configuration:"
cat /tmp/comfyui-extensions.json

# Test parsing the configuration with the Python script from start-comfyui.sh
cat /tmp/comfyui-extensions.json | python3 -c '
import json
import sys
import os

try:
    extensions = json.load(sys.stdin)
    print("\nParsed extensions:")
    for ext in extensions:
        name = ext.get("name", "")
        repo = ext.get("repo", "")
        path = ext.get("path", "")
        enabled = ext.get("enabled", False)
        
        print(f"- {name}: repo={repo}, path={path}, enabled={enabled}")
except Exception as e:
    print(f"Error processing extensions configuration: {e}")
' 