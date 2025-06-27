#!/bin/bash

set -e

# Set additional flags based on API_MODE
if [ "$API_MODE" = "true" ]; then
     mkdir -p /tmp/comfyui

    # Copy all folders from ComfyUI except models to /tmp/comfyui
    cd /mnt/models
    for item in *; do
        if [ "$item" != "models" ] && [ "$item" != "output" ] && [ -d "$item" ]; then
            cp -r "$item" /tmp/comfyui/
        fi
    done

    # Create extra_model_paths.yaml to point to the correct directories
    echo "comfyui:" > /tmp/comfyui/extra_model_paths.yaml && \
    echo "  is_default: false" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  checkpoints: /mnt/models/models/checkpoints/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  clip: /mnt/models/models/clip/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  clip_vision: /mnt/models/models/clip_vision/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  configs: /mnt/models/models/configs/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  controlnet: /mnt/models/models/controlnet/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  diffusion_models: |" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "    /mnt/models/models/diffusion_models" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "    /mnt/models/models/unet" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  embeddings: /mnt/models/models/embeddings/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  loras: /mnt/models/models/loras/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  upscale_models: /mnt/models/models/upscale_models/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  vae: /mnt/models/models/vae/" >> /tmp/comfyui/extra_model_paths.yaml && \
    echo "  gligen: /mnt/models/models/gligen/" >> /tmp/comfyui/extra_model_paths.yaml

    # API mode flags
    ADDITIONAL_FLAGS="--base-directory /tmp/comfyui --database-url sqlite:///:memory: --extra-model-paths-config /tmp/comfyui/extra_model_paths.yaml"
else
    # Non-API mode flags (default)
    ADDITIONAL_FLAGS="--base-directory /opt/app-root/src --database-url sqlite:////opt/app-root/src/user/comfyui.db --multi-user"
fi

# Set RUNTIME_FLAGS from command-line arguments and additional flags
if [ $# -gt 0 ]; then
    export RUNTIME_FLAGS="$@ $ADDITIONAL_FLAGS"
else
    export RUNTIME_FLAGS="$ADDITIONAL_FLAGS"
fi

# Start nginx and supervisord
/opt/app-root/scripts/run-nginx.sh &
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf &

# Keep the container running
tail -f /dev/null 