#!/bin/bash

set -e

# Set additional flags based on API_MODE
if [ "$API_MODE" = "true" ]; then
    # API mode flags
    ADDITIONAL_FLAGS="--base-directory /mnt/model --database-url sqlite:////tmp/comfyui.db"
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