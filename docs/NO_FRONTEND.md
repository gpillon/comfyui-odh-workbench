# NO_FRONTEND Environment Variable

## Overview

The `NO_FRONTEND` environment variable allows you to configure ComfyUI to run in API-only mode, disabling the web frontend and redirecting all frontend requests to a courtesy page.

## Usage

### Enable API-Only Mode

Set the `NO_FRONTEND` environment variable to `true`:

```bash
export NO_FRONTEND=true
```

Or when running with Docker:

```bash
docker run -e NO_FRONTEND=true your-comfyui-image
```

### Default Behavior (Frontend Enabled)

When `NO_FRONTEND` is not set or set to `false`, ComfyUI runs with the full web frontend:

```bash
export NO_FRONTEND=false  # or omit entirely
```

## What Happens in API-Only Mode

When `NO_FRONTEND=true`:

1. **Root Path Redirect**: All requests to `/` are redirected to `/api-mode.html`
2. **Frontend Blocking**: All other frontend paths are redirected to the courtesy page
3. **API Preservation**: All ComfyUI API endpoints remain fully functional:
   - `POST /prompt` - Submit workflows
   - `GET /view` - View generated images
   - `GET /history` - Access generation history
   - `GET /queue` - Check queue status
   - `GET /healthz` - Health check

## Courtesy Page

The API-only mode displays a professional courtesy page that:
- Explains that the frontend is not available
- Lists all available API endpoints
- Provides a modern, styled interface consistent with ComfyUI's design

## Technical Implementation

- **Configuration Structure**:
  - `comfyui-common.conf.template` - Shared configuration for both modes (API endpoints, health checks, logging)
  - `comfyui.conf.template` - Standard mode with frontend (includes common + frontend proxy)
  - `comfyui-api-mode.conf.template` - API-only mode (includes common + frontend blocking)
- **Runtime Logic**: The `run-nginx.sh` script checks the `NO_FRONTEND` variable and applies the appropriate configuration
- **Courtesy Page**: Located at `nginx/pages/api-mode.html`
- **DRY Principle**: Common configuration is shared to avoid code duplication

## Use Cases

API-only mode is ideal for:
- Headless deployments
- API-only integrations
- Microservice architectures
- Environments where the web UI is not needed
- Production deployments focused on API access

## Testing

Run the test suite to verify the functionality:

```bash
./script-tests/test-no-frontend-config.sh
```

This will verify that all components are properly configured and the environment variable switching works correctly. 