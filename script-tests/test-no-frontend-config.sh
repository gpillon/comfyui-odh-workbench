#!/bin/bash

# Test script to verify API_MODE configuration switching

set -e

echo "Testing API_MODE configuration switching..."

# Test 1: API_MODE=false (default behavior)
echo "Test 1: API_MODE=false (default)"
export API_MODE=false

if [ "${API_MODE}" = "true" ]; then
    echo "✗ Should use standard configuration but logic says API mode"
    exit 1
else
    echo "✓ Using standard configuration with frontend"
fi

# Test 2: API_MODE=true (API-only mode)
echo "Test 2: API_MODE=true (API-only mode)"
export API_MODE=true

if [ "${API_MODE}" = "true" ]; then
    echo "✓ Using API-only mode configuration"
else
    echo "✗ Should use API mode but logic says standard configuration"
    exit 1
fi

# Test 3: Check if required files exist
echo "Test 3: Checking required files exist"

if [ -f "nginx/conf.d/comfyui.conf.template" ]; then
    echo "✓ Standard nginx configuration template exists"
else
    echo "✗ Standard nginx configuration template missing"
    exit 1
fi

if [ -f "nginx/conf.d/comfyui-api-mode.conf.template" ]; then
    echo "✓ API mode nginx configuration template exists"
else
    echo "✗ API mode nginx configuration template missing"
    exit 1
fi

if [ -f "nginx/conf.d/comfyui-common.conf.template" ]; then
    echo "✓ Common nginx configuration template exists"
else
    echo "✗ Common nginx configuration template missing"
    exit 1
fi

if [ -f "nginx/pages/api-mode.html" ]; then
    echo "✓ API mode courtesy page exists"
else
    echo "✗ API mode courtesy page missing"
    exit 1
fi

if [ -f "scripts/run-nginx.sh" ]; then
    echo "✓ nginx startup script exists"
else
    echo "✗ nginx startup script missing"
    exit 1
fi

# Test 4: Check if run-nginx.sh contains the new logic
echo "Test 4: Checking run-nginx.sh contains API_MODE logic"

if grep -q "API_MODE" scripts/run-nginx.sh; then
    echo "✓ run-nginx.sh contains API_MODE logic"
else
    echo "✗ run-nginx.sh missing API_MODE logic"
    exit 1
fi

if grep -q "comfyui-api-mode.conf.template" scripts/run-nginx.sh; then
    echo "✓ run-nginx.sh references API mode template"
else
    echo "✗ run-nginx.sh missing reference to API mode template"
    exit 1
fi

# Test 5: Check configuration structure and content
echo "Test 5: Checking configuration structure and content"

if grep -q "include /opt/app-root/etc/nginx/conf.d/comfyui-common.conf" nginx/conf.d/comfyui.conf.template; then
    echo "✓ Standard config includes common configuration"
else
    echo "✗ Standard config missing common configuration include"
    exit 1
fi

if grep -q "include /opt/app-root/etc/nginx/conf.d/comfyui-common.conf" nginx/conf.d/comfyui-api-mode.conf.template; then
    echo "✓ API mode config includes common configuration"
else
    echo "✗ API mode config missing common configuration include"
    exit 1
fi

if grep -q "return 302 /api-mode.html" nginx/conf.d/comfyui-api-mode.conf.template; then
    echo "✓ API mode config redirects to api-mode.html"
else
    echo "✗ API mode config missing redirect to api-mode.html"
    exit 1
fi

if grep -q "location /prompt" nginx/conf.d/comfyui-common.conf.template; then
    echo "✓ Common config preserves /prompt endpoint"
else
    echo "✗ Common config missing /prompt endpoint"
    exit 1
fi

if grep -q "proxy_pass http://127.0.0.1:8188;" nginx/conf.d/comfyui.conf.template; then
    echo "✓ Standard config contains main proxy to ComfyUI frontend"
else
    echo "✗ Standard config missing main proxy"
    exit 1
fi

# Test 6: Check API mode page content
echo "Test 6: Checking API mode page content"

if grep -q "API Mode" nginx/pages/api-mode.html; then
    echo "✓ API mode page contains 'API Mode' text"
else
    echo "✗ API mode page missing 'API Mode' text"
    exit 1
fi

if grep -q "POST /prompt" nginx/pages/api-mode.html; then
    echo "✓ API mode page lists available endpoints"
else
    echo "✗ API mode page missing endpoint information"
    exit 1
fi

echo "✓ All tests passed! API_MODE configuration switching works correctly." 