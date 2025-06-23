#!/bin/bash

set -e

# Make sure the nginx log directory exists
mkdir -p /tmp/log/nginx

# Initialize access logs for culling with current time
CURRENT_TIME=$(date -Iseconds)
echo '[{"id":"comfyui","name":"comfyui","last_activity":"'$CURRENT_TIME'","execution_state":"idle","connections":1}]' > /tmp/log/nginx/comfyui.access.log

#here i want to replace the '${NB_PREFIX}' with the value of the env variable NB_PREFIX using sed, form /opt/app-root/etc/nginx/conf.d/comfyui.conf.template to /opt/app-root/etc/nginx/conf.d/comfyui.conf
sed "s|\${NB_PREFIX}|${NB_PREFIX}|g" /opt/app-root/etc/nginx/conf.d/comfyui.conf.template > /opt/app-root/etc/nginx/conf.d/comfyui.conf

# Start nginx with our custom configuration
exec nginx -c /opt/app-root/etc/nginx/nginx.conf -g "daemon off;"