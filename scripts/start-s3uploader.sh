#!/bin/bash

set -e

# Check if ENABLE_S3UPLOADER environment variable is set to true
if [ "${ENABLE_S3UPLOADER}" = "true" ]; then
    # Wait for the Python packages directory to exist
    COPY_MARKER="/opt/app-root/src/.packages_copied"
    echo "[s3uploader] Waiting for Python packages directory to be ready..."
    while [ ! -f "$COPY_MARKER" ]; do
        echo "[s3uploader] Waiting for $COPY_MARKER to exist..."
        sleep 5
    done
    echo "[s3uploader] Python packages directory is ready!"
    
    echo "[s3uploader] Starting S3Uploader service..."
    
    # Set PYTHONPATH environment variable
    export PYTHONPATH="/opt/app-root/src/.local/lib/python3.11/site-packages/:$PYTHONPATH"
    echo "PYTHONPATH set to: $PYTHONPATH"
    
    # Change to the services directory
    cd /opt/app-root/services/
    
    # Start the EzInfer Python application
    echo "[s3uploader] Starting s3uploader.py..."
    exec python3 s3uploader.py
else
    echo "[s3uploader] S3Uploader service is disabled"
    exec sleep infinity
fi 