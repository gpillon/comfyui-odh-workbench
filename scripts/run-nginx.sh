#!/bin/bash

set -e

# Make sure the nginx log directory exists
mkdir -p /var/log/nginx

# Initialize access logs for culling with current time
CURRENT_TIME=$(date -Iseconds)
echo '[{"id":"comfyui","name":"comfyui","last_activity":"'$CURRENT_TIME'","execution_state":"idle","connections":1}]' > /var/log/nginx/comfyui.access.log

# Make sure the access.cgi script is executable
chmod +x /opt/app-root/api/kernels/access.cgi

# Start nginx
exec nginx -g "daemon off;" 