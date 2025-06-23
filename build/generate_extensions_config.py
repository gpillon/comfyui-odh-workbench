#!/usr/bin/env python3

import os
import yaml
import json
import argparse
from pathlib import Path

def load_config(config_file):
    """Load the build configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def generate_extensions_config(config, output_file):
    """Generate a JSON configuration file for ComfyUI extensions"""
    # Extract extensions from the configuration
    extensions = config.get('comfyui_packages', [])
    
    # Write the configuration to a JSON file
    with open(output_file, 'w') as f:
        json.dump(extensions, f, indent=2)
    
    print(f"Generated extensions configuration at {output_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Generate ComfyUI extensions configuration')
    parser.add_argument('--config', default='build-config.yaml', help='Path to build configuration file')
    parser.add_argument('--output', default='build/extensions/comfyui-extensions.json', help='Path to output JSON file')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Generate extensions configuration
    success = generate_extensions_config(config, args.output)
    
    return 0 if success else 1

if __name__ == '__main__':
    exit(main()) 