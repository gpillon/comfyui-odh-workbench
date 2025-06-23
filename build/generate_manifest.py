#!/usr/bin/env python3

import os
import yaml
import json
import argparse

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

def extract_package_version(package_str):
    """Extract package name and version from package string"""
    if "==" in package_str:
        parts = package_str.split("==")
        name = parts[0]
        return {"name": name, "version": parts[1]}
        # version = parts[1].split("+")[0]  # Remove any +cpu, +cu128, etc.
        # return {"name": name, "version": version}        
    return {"name": package_str, "version": "latest"}

def generate_manifest(variant, config, output_path):
    """Generate a manifest file for the variant"""
    # Create the base manifest structure
    manifest = {
        "apiVersion": "image.openshift.io/v1",
        "kind": "ImageStream",
        "metadata": {
            "labels": {
                "opendatahub.io/notebook-image": "true",
                "opendatahub.io/dashboard": "true"
            },
            "annotations": {
                "opendatahub.io/notebook-image-url": "https://github.com/comfyanonymous/ComfyUI",
                "opendatahub.io/notebook-image-name": f"ComfyUI {variant['name']}",
                "opendatahub.io/notebook-image-desc": variant.get('description', f"ComfyUI {variant['name']} image"),
                "opendatahub.io/notebook-image-order": "1"
            },
            "name": f"comfyui-{variant['name']}-notebook"
        },
        "spec": {
            "lookupPolicy": {
                "local": True
            },
            "tags": []
        }
    }
    
    # Add recommended_accelerators if present in the variant
    if 'recommended_accelerators' in variant:
        manifest["metadata"]["annotations"]["opendatahub.io/recommended-accelerators"] = variant['recommended_accelerators']
    
    # Get software packages
    software_packages = [
        {"name": "ComfyUI", "version": config['build']['comfyui_version'].replace("master", "0.3.41")}
    ]
    
    # Get Python version from base image
    if "python-311" in variant['base_image']:
        software_packages.append({"name": "Python", "version": "v3.11"})
    elif "python-310" in variant['base_image']:
        software_packages.append({"name": "Python", "version": "v3.10"})
    elif "python-39" in variant['base_image']:
        software_packages.append({"name": "Python", "version": "v3.9"})
    
    # Get CUDA version if applicable
    if "cuda_version" in variant:
        software_packages.append({"name": "CUDA", "version": variant['cuda_version']})
    
    # Get ROCm version if applicable
    if "rocm_version" in variant:
        software_packages.append({"name": "ROCm", "version": variant['rocm_version']})
    
    # Get python packages
    python_packages = []
    
    # Process packages from files and custom packages
    for pkg in variant.get('packages', []):
        if 'file' in pkg and not pkg['file'].endswith('os-packages.txt'):
            # Read requirements file
            package_list = load_file_list(pkg['file'])
            for package in package_list:
                if package and not package.startswith("--"):
                    python_packages.append(extract_package_version(package))
        elif 'custom' in pkg:
            # Process custom packages
            for package in pkg['custom']:
                if package and not package.startswith("--"):
                    python_packages.append(extract_package_version(package))
    
    # Add ComfyUI custom packages if enabled
    for pkg in config.get('comfyui_packages', []):
        if pkg.get('enabled', True):  # Default to True if 'enabled' is not specified
            software_packages.append({"name": pkg['name'], "version": pkg['version']})
    
    # Create tag
    registry = config['build']['registry']
    repository = config['build']['repository']
    tag = variant['tag']
    
    tag_entry = {
        "annotations": {
            "opendatahub.io/notebook-software": json.dumps(software_packages),
            "opendatahub.io/notebook-python-dependencies": json.dumps(python_packages),
            "openshift.io/imported-from": f"{registry}/{repository}",
            "opendatahub.io/workbench-image-recommended": "true",
            "opendatahub.io/notebook-build-commit": f"comfyui-{variant['name']}-{tag}"
        },
        "from": {
            "kind": "DockerImage",
            "name": f"{registry}/{repository}-{variant['name']}:{tag}"
        },
        "name": tag,
        "referencePolicy": {
            "type": "Source"
        }
    }
    
    manifest["spec"]["tags"].append(tag_entry)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write the manifest file
    with open(output_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    
    print(f"Generated manifest at {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate manifests for ComfyUI variants')
    parser.add_argument('--config', default='build-config.yaml', help='Path to build configuration file')
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
        # Generate output path
        output_dir = 'build/manifests'
        output_file = f"imagestream-{variant['name']}.yaml"
        output_path = os.path.join(output_dir, output_file)
        
        # Generate manifest
        generate_manifest(variant, config, output_path)
    
    return 0

if __name__ == '__main__':
    exit(main()) 