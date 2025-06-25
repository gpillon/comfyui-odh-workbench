#!/bin/bash

# Script to clean up old files in input and output directories
# Only runs if CLEANUP_USER_INPUT_OUTPUT is set to "true"

# Default to 1 hour if CLEANUP_MAX_AGE_MINUTES is not set
MAX_AGE_MINUTES=${CLEANUP_MAX_AGE_MINUTES:-60}

cleanup() {
    if [ "$CLEANUP_USER_INPUT_OUTPUT" != "true" ]; then
        echo "[$(date)] Cleanup disabled. Set CLEANUP_USER_INPUT_OUTPUT=true to enable."
        return 0
    fi
    
    echo "[$(date)] Starting cleanup of files older than ${MAX_AGE_MINUTES} minutes"
    
    # Clean input directory
    if [ -d "/opt/app-root/src/input" ]; then
        echo "[$(date)] Cleaning /opt/app-root/src/input"
        find /opt/app-root/src/input -type f -mmin +${MAX_AGE_MINUTES} -delete
    fi
    
    # Clean output directory
    if [ -d "/opt/app-root/src/output" ]; then
        echo "[$(date)] Cleaning /opt/app-root/src/output"
        find /opt/app-root/src/output -type f -mmin +${MAX_AGE_MINUTES} -delete
    fi
    
    echo "Cleanup completed"
}

# Main loop
while true; do
    cleanup
    # Sleep for 15 minutes before next cleanup
    sleep ${CLEANUP_INTERVAL_SECONDS:-900}
done 