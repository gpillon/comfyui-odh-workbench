#!/bin/bash

set -e

# Make sure the nginx log directory exists
mkdir -p /tmp/log/nginx

# Initialize access logs for culling with current time
CURRENT_TIME=$(date -Iseconds)
echo '[{"id":"comfyui","name":"comfyui","last_activity":"'$CURRENT_TIME'","execution_state":"idle","connections":1}]' > /tmp/log/nginx/comfyui.access.log

# Start nginx with our custom configuration
exec nginx -c /etc/nginx/nginx.conf -g "daemon off;" 