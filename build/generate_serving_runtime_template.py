#!/usr/bin/env python3

import os
import yaml
import argparse
from pathlib import Path

def load_config(config_file):
    """Load the build configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def generate_serving_runtime_template(variant, config, output_path):
    """Generate a serving runtime template for the variant"""
    
    # Get registry and repository info
    registry = config['build']['registry']
    repository = config['build']['repository']
    tag = variant['tag']
    
    # Create the serving runtime template structure
    template = {
        "apiVersion": "template.openshift.io/v1",
        "kind": "Template",
        "metadata": {
            "annotations": {
                "description": f"ComfyUI {variant['name'].upper()} ServingRuntime for KServe in Red Hat OpenShift AI",
                "opendatahub.io/apiProtocol": "REST",
                "opendatahub.io/modelServingSupport": '["single"]',
                "openshift.io/display-name": f"ComfyUI {variant['name'].upper()} (ServingRuntime for KServe)",
                "openshift.io/provider-display-name": "GPillon",
                "tags": "rhods,rhoai,kserve,servingruntime,comfyui",
                "template.openshift.io/documentation-url": "https://github.com/gpillon/comfyui-odh-notebook",
                "template.openshift.io/long-description": f"This template defines resources needed to deploy ComfyUI {variant['name'].upper()} ServingRuntime with KServe in Red Hat OpenShift AI"
            },
            "labels": {
                "opendatahub.io/dashboard": "true"
            },
            "name": f"comfyui-{variant['name']}-runtime-template"
        },
        "objects": [
            {
                "apiVersion": "serving.kserve.io/v1alpha1",
                "kind": "ServingRuntime",
                "metadata": {
                    "annotations": {
                        "openshift.io/display-name": f"ComfyUI {variant['name'].upper()} ServingRuntime for KServe"
                    },
                    "labels": {
                        "opendatahub.io/dashboard": "true"
                    },
                    "name": f"comfyui-{variant['name']}-runtime"
                },
                "spec": {
                    "annotations": {},
                    "containers": [
                        {
                            "args": [],
                            "command": [],
                            "env": [
                                {
                                    "name": "NGINX_PORT",
                                    "value": "8080"
                                },
                                {
                                    "name": "ENABLE_EZ_INFER",
                                    "value": "true"
                                },
                                {
                                    "name": "API_MODE",
                                    "value": "true"
                                },
                                {
                                    "name": "ENABLE_S3UPLOADER",
                                    "value": "false"
                                }
                            ],
                            "image": f"{registry}/{repository}-{variant['name']}:{tag}",
                            "name": "kserve-container",
                            "ports": [
                                {
                                    "containerPort": 8080,
                                    "protocol": "TCP"
                                }
                            ]
                        }
                    ],
                    "multiModel": False,
                    "supportedModelFormats": [
                        {
                            "autoSelect": True,
                            "name": "ComfyUI"
                        }
                    ]
                }
            }
        ]
    }
    
    # Add resource requirements for GPU variants
    if variant['name'] in ['nvidia', 'amd', 'intel']:
        container = template["objects"][0]["spec"]["containers"][0]
        
        if variant['name'] == 'nvidia':
            container["resources"] = {
                "limits": {
                    "nvidia.com/gpu": 1
                },
                "requests": {
                    "nvidia.com/gpu": 1
                }
            }
        elif variant['name'] == 'amd':
            container["resources"] = {
                "limits": {
                    "amd.com/gpu": 1
                },
                "requests": {
                    "amd.com/gpu": 1
                }
            }
        elif variant['name'] == 'intel':
            container["resources"] = {
                "limits": {
                    "intel.com/gpu": 1
                },
                "requests": {
                    "intel.com/gpu": 1
                }
            }
    
    # Add variant-specific environment variables if they exist
    if 'env' in variant:
        container_env = template["objects"][0]["spec"]["containers"][0]["env"]
        for key, value in variant['env'].items():
            # Skip if already exists
            if not any(env_var['name'] == key for env_var in container_env):
                container_env.append({
                    "name": key,
                    "value": str(value)
                })
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write the template file
    with open(output_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated serving runtime template at {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate serving runtime templates for ComfyUI variants')
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
        output_file = f"serving-runtime-template-{variant['name']}.yaml"
        output_path = os.path.join(output_dir, output_file)
        
        # Generate serving runtime template
        generate_serving_runtime_template(variant, config, output_path)
    
    return 0

if __name__ == '__main__':
    exit(main()) 