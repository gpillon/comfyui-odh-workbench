#!/usr/bin/env python3

import os
import yaml
import jinja2
import argparse
from pathlib import Path

def load_config(config_file):
    """Load the build configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def load_file_list(file_path):
    """Load a list of items from a file, one per line"""
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found")
        return []
    
    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def generate_containerfile(template_path, output_path, context):
    """Generate a Containerfile from the template and context"""
    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)
    
    # Set up Jinja2 environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Load template
    template = env.get_template(template_file)
    
    # Render template with context
    rendered = template.render(**context)
    
    # Write output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(rendered)
    
    print(f"Generated Containerfile at {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate Containerfiles from templates')
    parser.add_argument('--config', default='build-config.yaml', help='Path to build configuration file')
    parser.add_argument('--template', default='build/Containerfile.template', help='Path to Containerfile template')
    parser.add_argument('--variant', help='Specific variant to build (default: all variants)')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Get variants to process
    variants = config['variants']
    if args.variant:
        variants = [v for v in variants if v['name'] == args.variant]
        if not variants:
            print(f"Error: Variant '{args.variant}' not found in configuration")
            return 1
    
    # Process each variant
    for variant in variants:
        # Prepare context for template
        context = {
            'base_image': variant['base_image'],
            'description': variant.get('description', f"ComfyUI {variant['name']} image"),
            'comfyui_repo': config['build']['comfyui_repo'],
            'comfyui_version': config['build']['comfyui_version'],
            'port': config['build']['port'],
            'user': config['build']['user'],
        }
        
        # Load package lists
        os_packages = []
        python_packages = []
        custom_packages = []
        
        for pkg in variant.get('packages', []):
            if 'file' in pkg:
                if pkg['file'].endswith('os-packages.txt'):
                    os_packages.extend(load_file_list(pkg['file']))
                else:
                    python_packages.extend(load_file_list(pkg['file']))
            elif 'custom' in pkg:
                custom_packages.extend(pkg['custom'])
        
        context['os_packages'] = os_packages
        context['python_packages'] = python_packages
        context['custom_packages'] = custom_packages
        
        # Add environment variables
        env_vars = variant.get('env', {})
        context['env_vars'] = env_vars
        
        # Generate output path
        output_dir = 'build/containerfiles'
        output_file = f"Containerfile.{variant['name']}"
        output_path = os.path.join(output_dir, output_file)
        
        # Generate Containerfile
        generate_containerfile(args.template, output_path, context)
    
    return 0

if __name__ == '__main__':
    exit(main()) 