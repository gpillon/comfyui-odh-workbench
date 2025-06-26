# TODO List

## Tasks for Tomorrow

### 0. Main Project
- [ ] Remove log message "Cleanup disabled. Set CLEANUP_USER_INPUT_OUTPUT=true to enable."

### 1. Enable EZ_INFER in the Project
- [ ] Modify the project configuration to enable the EZ_INFER functionality
- [ ] Update the build configuration or deployment scripts to include the inference service
- [ ] Test the `/ezinfer` endpoint functionality
- [ ] Verify that the `ENABLE_EZ_INFER` environment variable properly activates the service
- [ ] Ensure proper integration with the main ComfyUI container
- [ ] Convert all ezinfer strings to English (currently some are in Italian)
- [ ] Implement alternative image return format instead of base64 encoding

### 2. Create Development S3 Upload Endpoint
- [ ] Create a new endpoint for development mode usage
- [ ] Implement functionality to upload the entire development folder content to S3
- [ ] Add proper authentication/security measures for the development endpoint
- [ ] Consider compression options for efficient folder uploads
- [ ] Add configuration for S3 bucket settings (credentials, region, bucket name)
- [ ] Test the upload functionality with various file types and folder structures
- [ ] Document the new endpoint usage and configuration requirements

## Notes
- Both features should be properly documented in the README.md
- Consider adding environment variables for S3 configuration (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME, etc.)
- The development S3 upload should be optional and only enabled in development environments 

### 3. Improve API_MODE Endpoints Documentation
- [ ] Document all available API_MODE endpoints in the README.md
- [ ] Add examples for each endpoint with request/response formats
- [ ] Include authentication requirements if any
- [ ] Document query parameters and request body schemas
- [ ] Add troubleshooting section for common API usage issues
- [ ] Consider creating an OpenAPI/Swagger specification for better API documentation
- [ ] Include ezinfer image return handling in swagger documentation

