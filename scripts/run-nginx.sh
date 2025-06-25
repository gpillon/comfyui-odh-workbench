#!/bin/bash

set -e

# Make sure the nginx log directory exists
mkdir -p /tmp/log/nginx

# Initialize access logs for culling with current time
CURRENT_TIME=$(date -Iseconds)
echo '[{"id":"comfyui","name":"comfyui","last_activity":"'$CURRENT_TIME'","execution_state":"idle","connections":1}]' > /tmp/log/nginx/comfyui.access.log

# Check if NO_FRONTEND environment variable is set to enable API-only mode
if [ "${NO_FRONTEND}" = "true" ]; then
    echo "NO_FRONTEND is set to true, using API-only mode configuration"
    envsubst '${NB_PREFIX},${NGINX_PORT}' < /opt/app-root/etc/nginx/conf.d/comfyui-api-mode.conf.template > /opt/app-root/etc/nginx/conf.d/comfyui.conf
else
    echo "Using standard configuration with frontend"
    envsubst '${NB_PREFIX},${NGINX_PORT}' < /opt/app-root/etc/nginx/conf.d/comfyui.conf.template > /opt/app-root/etc/nginx/conf.d/comfyui.conf
fi

envsubst '${NB_PREFIX},${NGINX_PORT}' < /opt/app-root/etc/nginx/extra/comfyui-common.conf.template > /opt/app-root/etc/nginx/extra/comfyui-common.conf

# Start nginx with our custom configuration
exec nginx -c /opt/app-root/etc/nginx/nginx.conf -g "daemon off;"