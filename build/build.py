#!/usr/bin/env python3

import os
import yaml
import argparse
import subprocess
from pathlib import Path

def load_config(config_file):
    """Load the build configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def build_image(containerfile, tag, platforms=None):
    """Build a container image using podman or docker"""
    cmd = ['podman', 'build']
    
    # Add platforms if specified
    if platforms:
        platform_arg = ','.join(platforms)
        cmd.extend(['--platform', platform_arg])
    
    # Add tag
    cmd.extend(['-t', tag])
    
    # Add containerfile
    cmd.extend(['-f', containerfile, '.'])
    
    # Run the build command
    print(f"Building image: {tag}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully built image: {tag}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building image: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Build ComfyUI container images')
    parser.add_argument('--config', default='build-config.yaml', help='Path to build configuration file')
    parser.add_argument('--variant', help='Specific variant to build (default: all variants)')
    parser.add_argument('--skip-generate', action='store_true', help='Skip generating Containerfiles')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Generate Containerfiles if needed
    if not args.skip_generate:
        generate_script = Path('build/generate_containerfile.py')
        cmd = [str(generate_script), '--config', args.config]
        
        if args.variant:
            cmd.extend(['--variant', args.variant])
        
        subprocess.run(cmd, check=True)
    
    # Get variants to process
    variants = config['variants']
    if args.variant:
        variants = [v for v in variants if v['name'] == args.variant]
        if not variants:
            print(f"Error: Variant '{args.variant}' not found in configuration")
            return 1
    
    # Build each variant
    for variant in variants:
        # Get image name and tag
        registry = config['build']['registry']
        repository = config['build']['repository']
        name = variant['name']
        tag = variant['tag']
        extra_flags = variant.get('extra_flags', '')
        
        # Full image name
        image_tag = f"{registry}/{repository}-{name}:{tag}"
        
        # Containerfile path
        containerfile = f"build/containerfiles/Containerfile.{name}"
        
        # Get platforms
        platforms = config['base'].get('platforms')
        
        # Build the image
        success = build_image(containerfile, image_tag, platforms)
        if not success:
            print(f"Failed to build image: {image_tag}")
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main()) 