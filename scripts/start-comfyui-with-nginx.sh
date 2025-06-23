#!/bin/bash

set -e

# Set RUNTIME_FLAGS from command-line arguments
if [ $# -gt 0 ]; then
    export RUNTIME_FLAGS="$@"
fi

# Start nginx and supervisord
/opt/app-root/scripts/run-nginx.sh &
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf &

# Start ComfyUI with runtime flags
/opt/app-root/scripts/start-comfyui.sh $RUNTIME_FLAGS $EXTRA_FLAGS &

# Keep the container running
tail -f /dev/null 