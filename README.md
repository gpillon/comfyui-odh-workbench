# ComfyUI for OpenDataHub

This repository contains a dynamic builder for ComfyUI images optimized for OpenDataHub on OpenShift AI.

## TL;DR: Quickstart

```bash
# NVIDIA GPU
oc apply -f https://github.com/gpillon/comfyui-odh-notebook/releases/download/v1.0.1/imagestream-nvidia.yaml -n redhat-ods-applications
# INTEL
oc apply -f https://github.com/gpillon/comfyui-odh-notebook/releases/download/v1.0.1/imagestream-intel.yaml -n redhat-ods-applications
# CPU
oc apply -f https://github.com/gpillon/comfyui-odh-notebook/releases/download/v1.0.1/imagestream-cpu.yaml -n redhat-ods-applications
# AMD (WIP)
oc apply -f https://github.com/gpillon/comfyui-odh-notebook/releases/download/v1.0.1/imagestream-amd.yaml -n redhat-ods-applications
```

## Overview

ComfyUI is a powerful and modular stable diffusion GUI and backend with a node-based interface. This project creates container images of ComfyUI that are ready to use in OpenDataHub/OpenShift AI environments.

## Features

- Dynamic image building based on YAML configuration
- Multiple variants (NVIDIA CUDA, CPU)
- Pre-installed ComfyUI Manager
- Optimized for Openshfit AI / OpenDataHub deployment
- Nginx proxy for OpenShift compatibility and idle culling support

## Available Images

Images are built and published to the GitHub Container Registry:

- `ghcr.io/gpillon/comfyui-nvidia:<version>` - ComfyUI with NVIDIA CUDA support
- `ghcr.io/gpillon/comfyui-cpu:<version>` - ComfyUI with CPU support only

## Usage

### Running locally

```bash
# NVIDIA GPU
podman run -it --rm -p 8888:8888 --gpus all ghcr.io/gpillon/comfyui-nvidia:v1.0.1

# CPU only
podman run -it --rm -p 8888:8888 ghcr.io/gpillon/comfyui-cpu:v1.0.1
```

Then access ComfyUI at http://localhost:8888

### Deploying on OpenDataHub

Follow the OpenDataHub documentation for deploying custom container images.

## Network Configuration

The container uses the following network configuration:

- Nginx listens on port 8888 and proxies requests to ComfyUI
- ComfyUI runs on internal port 8188
- Nginx provides OpenShift compatibility endpoints at `/api` paths
- Idle culling support is implemented through the `/api/kernels` endpoint

## File Cleanup (For ServingRuntime)

The container includes an automatic file cleanup system that can be enabled to remove old files from the input and output directories:

- Set `CLEANUP_USER_INPUT_OUTPUT=true` to enable automatic cleanup
- By default, files older than 60 minutes will be removed
- Customize the retention time by setting `CLEANUP_MAX_AGE_MINUTES` to the desired value in minutes
- Only files are deleted, directories are preserved
- Cleanup runs every 15 minutes

Example:
```bash
# Enable cleanup with default settings (60 minutes)
export CLEANUP_USER_INPUT_OUTPUT=true

# Enable cleanup, set custom retention time (1 hour), run check every 900 seconds
export CLEANUP_USER_INPUT_OUTPUT=true
export CLEANUP_MAX_AGE_MINUTES=60 
export CLEANUP_INTERVAL_SECONDS
```

## Building Images

### Prerequisites

- Python 3.8+
- podman or docker
- PyYAML and Jinja2 Python packages

### Build Configuration

Edit the `build-config.yaml` file to customize your build:

```yaml
variants:
  - name: "nvidia"
    tag: "vX.Y.Z"
    base_image: "nvidia/cuda:11.8.0-runtime-ubuntu22.04"
    # additional configuration...


### Building Images

Prepare env:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install pyyaml jinja2
```


Build all variants:

```bash
python build/build.py
```

Build a specific variant:

```bash
python build/build.py --variant nvidia
```

## Development

1. Clone this repository
2. Modify the configuration in `build-config.yaml`
3. Run the build script

## License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

## Acknowledgements

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - The original ComfyUI project
- [OpenDataHub](https://opendatahub.io/) - Open source end-to-end AI/ML platform on OpenShift

## Dynamic ComfyUI Extensions

The container now supports dynamic installation of ComfyUI extensions based on configuration in the `build-config.yaml` file. Extensions are specified in the `comfyui_packages` section:

```yaml
comfyui_packages:
  - name: "ComfyUI-Manager"
    version: "3.33"
    repo: "https://github.com/ltdrdata/ComfyUI-Manager.git"
    path: "custom_nodes/ComfyUI-Manager"
    enabled: true
  # Add more packages as needed following the same format:
  # - name: "Package-Name"
  #   repo: "https://github.com/author/repo.git"
  #   path: "custom_nodes/Package-Name"
  #   enabled: true
```

During the build process:
1. The `build/generate_extensions_config.py` script generates a JSON configuration file from the YAML
2. This JSON file is copied to `/opt/app-root/etc/comfyui-extensions.json` in the container
3. At startup, the `start-comfyui.sh` script reads this file and installs the specified extensions

If no extensions configuration is found, the script falls back to installing ComfyUI Manager (unless disabled with the `DISABLE_MANAGER=true` environment variable).