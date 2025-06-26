#!/bin/bash

set -e

# Check if ENABLE_EZ_INFER environment variable is set to true
if [ "${ENABLE_EZ_INFER}" = "true" ]; then

    # Wait for the Python packages directory to exist
    echo "[ezinfer] Waiting for Python packages directory to be ready..."
    while [ ! -d "/opt/app-root/src/.local/lib/python3.11/site-packages/" ]; do
        echo "[ezinfer] Waiting for /opt/app-root/src/.local/lib/python3.11/site-packages/ to exist..."
        sleep 2
    done
    echo "[ezinfer] Python packages directory is ready!"

    echo "[ezinfer] Starting EzInfer service..."
    
    # Set PYTHONPATH environment variable
    export PYTHONPATH="/opt/app-root/src/.local/lib/python3.11/site-packages/:$PYTHONPATH"
    echo "PYTHONPATH set to: $PYTHONPATH"
    
    # Change to the services directory
    cd /opt/app-root/services/
    
    # Start the EzInfer Python application
    echo "[ezinfer] Starting ez_infer.py..."
    exec python3 ez_infer.py
else
    echo "[ezinfer] EzInfer service is disabled"
    exec sleep infinity
fi 