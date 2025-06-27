# TODO List

## Tasks for Tomorrow

### -1. Repository
 - [ ] cleanup folder (eg. Dont push manifests!)

### 0. Main Project
- [x] Remove log message "Cleanup disabled. Set CLEANUP_USER_INPUT_OUTPUT=true to enable."
- [x] Enable gzip compression in nginx if not already enabled

### 1. Enable EZ_INFER in the Project
- [x] Modify the project configuration to enable the EZ_INFER functionality
- [x] Update the build configuration or deployment scripts to include the inference service
- [x] Test the `/ezinfer` endpoint functionality
- [x] Verify that the `ENABLE_EZ_INFER` environment variable properly activates the service
- [x] Ensure proper integration with the main ComfyUI container
- [ ] Convert all ezinfer strings to English (currently some are in Italian)
- [ ] Implement alternative image return format instead of base64 encoding

### 2. Create Development S3 Upload Endpoint
- [x] Create a new endpoint for development mode usage
- [x] Implement functionality to upload the entire development folder content to S3
- [ ] Add proper authentication/security errors for the development endpoint
- [ ] Consider compression options for efficient folder uploads
- [x] Add configuration for S3 bucket settings (credentials, region, bucket name)
- [x] Test the upload functionality with various file types and folder structures
- [ ] Document the new endpoint usage and configuration requirements

## Notes
- Both features should be properly documented in the README.md
- Consider adding environment variables for S3 configuration (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME, etc.)
- The development S3 upload should be optional and only enabled in development environments 

### 3. Improve API_MODE Endpoints Documentation
- [ ] Document all available API_MODE endpoints in the README.md
- [ ] !important Add troubleshooting section for common API usage issues
- [ ] Add examples for each endpoint (at least most important EPs) with request (response?) formats
- [ ] Document query parameters and request body schemas (Swagger?)
- [ ] Consider creating an OpenAPI/Swagger specification for better API documentation
- [ ] Include ezinfer image return handling in swagger documentation

