# ComfyUI for OpenDataHub

This repository contains a dynamic builder for ComfyUI images optimized for [OpenDataHub](https://opendatahub.com/) or [Red Hat OpenShift AI](https://www.redhat.com/en/products/ai/openshift-ai).

## TL;DR

```bash
# Nvidia GPU
oc apply -f https://github.com/gpillon/comfyui-odh-workbench/releases/download/v1.0.5/imagestream-nvidia.yaml -n redhat-ods-applications

# CPU Only (recommended for testing purposes only)
oc apply -f https://github.com/gpillon/comfyui-odh-notebook/releases/download/v1.0.5/imagestream-cpu.yaml -n redhat-ods-applications

# Intel GPU
oc apply -f https://github.com/gpillon/comfyui-odh-notebook/releases/download/v1.0.5/imagestream-intel.yaml -n redhat-ods-applications

# AMD GPU (still WIP)
oc apply -f https://github.com/gpillon/comfyui-odh-notebook/releases/download/v1.0.5/imagestream-amd.yaml -n redhat-ods-applications
```
And then create the Workbench in your workspace using the custom image.

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

- `quay.io/rh-ee-gpillon/comfyui-odh-workbench:<version>-nvidia` - ComfyUI with NVIDIA CUDA support
- `quay.io/rh-ee-gpillon/comfyui-odh-workbench:<version>-intel` - ComfyUI with Intel GPU support
- `quay.io/rh-ee-gpillon/comfyui-odh-workbench:<version>-amd` - ComfyUI with AMD ROCm support
- `quay.io/rh-ee-gpillon/comfyui-odh-workbench:<version>-cpu` - ComfyUI with CPU support only

## Usage

### Running locally

```bash
# NVIDIA GPU
podman run -it --rm -p 8888:8888 --gpus all quay.io/rh-ee-gpillon/comfyui-odh-workbench:v1.0.5-nvidia

# CPU only
podman run -it --rm -p 8888:8888 quay.io/rh-ee-gpillon/comfyui-odh-workbench:v1.0.5-cpu
```

Then access ComfyUI at http://localhost:8888

### Deploying on OpenDataHub

Follow the OpenDataHub documentation for deploying custom container images.

## Network Configuration

The container uses the following network configuration:

- Nginx listens on port `NGINX_PORT` (Default 8888, or 8080 for ServingRuntime) and proxies requests to ComfyUI
- ComfyUI runs on internal port 8188
- Nginx provides a mini API doc at `/api` paths
- Idle culling support is implemented through the `/api/kernels` endpoint

## Use as ServingRuntime (AKA API_MODE)
The container can be run in API-only mode by setting the `API_MODE` (ConfyUI Frontend Disabled) environment variable to `true`. This mode is optimized for use as a ServingRuntime in OpenShift AI, disabling the web UI and only exposing the API endpoints.

### File Cleanup (For ServingRuntime)

The container includes an automatic file cleanup system that can be enabled to remove old files from the input and output directories:

- Set `CLEANUP_USER_INPUT_OUTPUT=true` to enable automatic ComfyUI input and output cleanup (usually images or videos)
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

### Simple Inference Endpoint (For ServingRuntime)

When running as a ServiceRuntime, the container can provide a simple inference endpoint that allows direct workflow execution with syncronous response through HTTP requests. This feature can be enabled by setting the `ENABLE_EZ_INFER` environment variable to `true`. Very useful for demos.


### Endpoint Usage

**POST `/ezinfer`**

Send a workflow JSON directly to ComfyUI for execution. The workflow should be included in the request body as JSON.

Example request:
```bash
curl -X POST http://your-service-url/ezinfer \
  -H "Content-Type: application/json" \
  -d '{
    "4": {
      "inputs": {
        "filename_prefix": "ComfyUI",
        "images": [
          "8",
          0
        ]
      },
      "class_type": "SaveImage",
      "_meta": {
        "title": "Save Image"
      }
    },
    "8": {
      "inputs": {
        "seed": 1023641672961582,
        "strength": 1,
        "image": [
          "9",
          0
        ]
      },
      "class_type": "ImageAddNoise",
      "_meta": {
        "title": "ImageAddNoise"
      }
    },
    "9": {
      "inputs": {
        "width": 512,
        "height": 512,
        "batch_size": 1,
        "color": 0
      },
      "class_type": "EmptyImage",
      "_meta": {
        "title": "EmptyImage"
      }
    }
  }'
```

### Environment Variables

The inference endpoint supports the following environment variables:

- **`ENABLE_EZ_INFER`**: Set to `true` to enable the simple inference endpoint (default: `false`)
- **`INFERENCE_DEBUG`**: Set to `true` to enable debug logging for inference operations (default: `false`)
- **`INFERENCE_RANDOM_SEED_NODES`**: Set to `true` to automatically randomize seed values in workflows. Very useful for demos. (default: `true`) 

### ...why INFERENCE_RANDOM_SEED_NODES ... 

...and not using somethin like `cache size 0` ?

When using the ezinfer endpoint, it's important to note that ComfyUI maintains an internal cache for loaded models and other expensive operations. While you may want to generate different outputs by varying the seed value, completely invalidating the cache on each request would force ComfyUI to reload models and other cached data, significantly impacting performance. This setting (INFERENCE_RANDOM_SEED_NODES) allows ComfyUI to reuse cached models and intermediate results while is forced to generate (unique) outputs through different random seeds every endpoint call.

### Cache Avoidance

The `INFERENCE_RANDOM_SEED_NODES` environment variable is particularly useful in development environments where you might send the same workflow multiple times. When enabled (default), it automatically modifies any `seed` parameters found in the workflow with random values, preventing ComfyUI from serving cached results. This ensures that each request generates new content even when using identical workflows.

When `INFERENCE_RANDOM_SEED_NODES=true`:
- The system automatically finds nodes with `seed` inputs and replaces them with random values
- If a node has a `control_after_generate` parameter, it's set to `"randomize"`
- This behavior helps avoid ComfyUI's caching mechanism in shared development environments

Example:
```bash
# Enable inference endpoint with debug logging and cache avoidance
export ENABLE_EZ_INFER=true
export INFERENCE_DEBUG=true
export INFERENCE_RANDOM_SEED_NODES=true
```

## S3 Uploader

The container includes an S3 uploader utility that provides a web interface for uploading workspace contents to S3-compatible storage. This feature is useful for the ServingRuntime.

### Accessing the S3 Uploader

The S3 uploader is available at `/s3uploader` when the container is running. For example:
- Local development: `http://localhost:8888/s3uploader`
- OpenShift deployment: `https://your-workbench-url/s3uploader`

### Required Environment Variables

Configure S3 connection th the UI when in "Workbench mode" (aka dev mode) or set these environment variables:

```bash
export AWS_S3_ENDPOINT="https://your-s3-endpoint.com"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_S3_BUCKET="your-bucket-name"
export AWS_REGION="your-region"  # Optional, defaults to empty
```

On OpenDataHub / Openshift AI S3 variables are autoset when using a "connection"

### Optional Configuration

**Exclude Folders from Upload:**
```bash
# Space-separated list of folders to exclude (relative to /opt/app-root/src/)
export S3UPLOADER_EXCLUDE_UPLOAD="temp logs cache build"
```

### Features

- **Web Interface**: Modern, responsive web UI with real-time progress tracking
- **Automatic Exclusions**: Hidden folders (starting with `.`) and the `user/` folder are automatically excluded
- **Custom Exclusions**: Specify additional folders to exclude via environment variable
- **Progress Tracking**: Real-time upload progress with file count and data transfer metrics
- **Optimized Transfers**: Uses multipart uploads for large files and concurrent transfers for efficiency
- **Error Handling**: Graceful error handling with user-friendly messages
- **Subfolder Support**: Upload to specific subfolders within your S3 bucket

### Usage

2. **Access Web Interface**: Navigate to `https://<confyui-noteebook-url>/s3uploader` in your browser
3. **Review Configuration**: The interface displays your S3 configuration and folder size
4. **Specify Subfolder**: Enter the target subfolder path (e.g., `/confyui-model-01`, `/workspace-2024`)
5. **Start Upload**: Click "Start Upload" to begin the transfer
6. **Monitor Progress**: Watch real-time progress updates with file and data transfer metrics

### Automatic Exclusions

The following are automatically excluded from uploads:
- All hidden folders and files (starting with `.`)
- The `/opt/app-root/src/user/` folder and its contents
- Folders specified in the `S3UPLOADER_EXCLUDE_UPLOAD` environment variable

## Building Images

### Prerequisites

- Python 3.8+ (tested with Python 3.11 / 3.12)
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
- [AI on OpenShift](https://ai-on-openshift.io/)

## Dynamic ComfyUI Extensions

The container supports dynamic installation of ComfyUI extensions based on configuration in the `build-config.yaml` file. Extensions are specified in the `comfyui_packages` section:

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