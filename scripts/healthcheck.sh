#!/bin/bash

# Health check script for ComfyUI
# During startup phase, it always returns success
# After startup, it checks the actual ComfyUI endpoint

# Output HTTP header for CGI
echo "Content-Type: text/plain"
echo

# Path to the marker file indicating startup completion
STARTUP_COMPLETE_MARKER="/opt/app-root/src/.startup_complete"

# Check if we're still in startup phase
if [ ! -f "$STARTUP_COMPLETE_MARKER" ]; then
    # We're still in startup phase, return success
    echo "Still in startup phase, returning success"
    exit 0
fi

# Startup is complete, check the actual ComfyUI endpoint
HEALTHCHECK_URL="http://localhost:8080/prompt"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTHCHECK_URL)

if [ "$HTTP_RESPONSE" -eq 200 ] || [ "$HTTP_RESPONSE" -eq 405 ]; then
    # HTTP 200 OK or 405 Method Not Allowed (expected for GET on /prompt endpoint)
    echo "ComfyUI is healthy"
    exit 0
else
    echo "ComfyUI health check failed with HTTP code: $HTTP_RESPONSE"
    exit 1
fi 