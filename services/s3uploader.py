#!/usr/bin/env python3
"""
S3 Uploader Service

Provides API endpoints for uploading local folder contents to S3-compatible storage.
This service runs behind NGINX and only provides API endpoints.
"""

import os
import sys
import threading
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from botocore.config import Config
from boto3.s3.transfer import TransferConfig

app = Flask(__name__)
CORS(app)

# Global variables for upload progress tracking
upload_progress = {
    'status': 'idle',  # idle, running, completed, error
    'current_file': '',
    'files_processed': 0,
    'total_files': 0,
    'bytes_uploaded': 0,
    'total_bytes': 0,
    'error_message': ''
}

# Source folder to upload
SOURCE_FOLDER = '/opt/app-root/src/'

def should_exclude_path(path, source_folder):
    """Check if a path should be excluded from upload and size calculation"""
    relative_path = os.path.relpath(path, source_folder)
    
    # Don't exclude the root directory itself (relative path would be '.')
    if relative_path == '.':
        return False
    
    # Exclude only top-level hidden folders (starting with . directly under source_folder)
    # this is to clone all the custom nodes git informations.
    path_parts = relative_path.split(os.sep)
    if len(path_parts) > 0 and path_parts[0].startswith('.'):
        return True
    
    # Exclude the user folder
    if relative_path.startswith('user' + os.sep) or relative_path == 'user':
        return True
    
    # Exclude folders from environment variable
    exclude_list = os.getenv('S3UPLOADER_EXCLUDE_UPLOAD', '').strip()
    if exclude_list:
        exclude_folders = exclude_list.split()
        for exclude_folder in exclude_folders:
            # Prepend source folder path and normalize
            full_exclude_path = os.path.join(source_folder, exclude_folder.strip())
            full_exclude_path = os.path.normpath(full_exclude_path)
            current_path = os.path.normpath(path)
            
            # Check if current path is the excluded folder or a subfolder of it
            if current_path == full_exclude_path or current_path.startswith(full_exclude_path + os.sep):
                return True
    
    return False

def get_s3_config():
    """Get S3 configuration from environment variables"""
    config = {
        'endpoint': os.getenv('AWS_S3_ENDPOINT'),
        'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
        'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'bucket': os.getenv('AWS_S3_BUCKET'),
        'region': os.getenv('AWS_REGION', '')
    }
    
    # Check if all required config is present
    missing = [key for key, value in config.items() if value is None and key != 'region']
    if missing:
        return None, f"Missing required environment variables: {', '.join(key.upper() for key in missing)}"
    
    return config, None

def get_optimized_transfer_config():
    """Get optimized transfer configuration for large files and many files"""
    # 100 MB multipart threshold for large files
    MB = 1024 ** 2
    
    transfer_config = TransferConfig(
        multipart_threshold=50 * MB,  # Files larger than 50MB use multipart
        max_concurrency=20,           # Increase concurrent transfers
        multipart_chunksize=50 * MB,  # 50MB chunks for multipart uploads
        use_threads=True,             # Enable threading for concurrency
        max_io_queue=1000,           # Increase I/O queue for many files
        io_chunksize=1024 * 1024     # 1MB I/O chunks
    )
    
    return transfer_config

def get_s3_client():
    """Create and return S3 client with optimized configuration"""
    config, error = get_s3_config()
    
    if error:
        return None, None, None, error
    
    # Configure S3 client with connection pooling
    s3_config = Config(
        region_name=config['region'],
        retries={'max_attempts': 3, 'mode': 'adaptive'},
        max_pool_connections=50  # Increase connection pool for concurrent uploads
    )
    
    try:
        client = boto3.client(
            's3',
            endpoint_url=config['endpoint'],
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key'],
            config=s3_config
        )
        
        transfer_config = get_optimized_transfer_config()
        return client, config['bucket'], transfer_config, None
    except Exception as e:
        return None, None, None, f"Failed to create S3 client: {str(e)}"

def calculate_folder_size(folder_path):
    """Calculate total size and file count of a folder, excluding specified folders"""
    total_size = 0
    file_count = 0
    
    if not os.path.exists(folder_path):
        return 0, 0
    
    try:
        for root, dirs, files in os.walk(folder_path):
            # Check if current directory should be excluded
            if should_exclude_path(root, folder_path):
                # Clear dirs list to prevent os.walk from descending into subdirectories
                dirs.clear()
                continue
            
            # Filter out excluded directories from dirs list
            dirs[:] = [d for d in dirs if not should_exclude_path(os.path.join(root, d), folder_path)]
            
            # Count files in current directory
            for file in files:
                file_path = os.path.join(root, file)
                # Double-check that file path is not excluded
                if not should_exclude_path(file_path, folder_path):
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except (OSError, IOError):
                        # Skip files that can't be read
                        pass
    except (OSError, IOError):
        # Skip directories that can't be accessed
        pass
    
    return total_size, file_count

def format_size(size_bytes):
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def upload_folder_to_s3(subfolder):
    """Upload folder contents to S3 with progress tracking"""
    global upload_progress
    
    try:
        # Reset progress
        upload_progress.update({
            'status': 'running',
            'current_file': '',
            'files_processed': 0,
            'total_files': 0,
            'bytes_uploaded': 0,
            'total_bytes': 0,
            'error_message': ''
        })
        
        # Get S3 client, bucket, and transfer config
        s3_client, bucket_name, transfer_config, error = get_s3_client()
        
        if error:
            upload_progress['status'] = 'error'
            upload_progress['error_message'] = error
            return
        
        # Calculate total size and file count
        total_bytes, total_files = calculate_folder_size(SOURCE_FOLDER)
        upload_progress['total_bytes'] = total_bytes
        upload_progress['total_files'] = total_files
        
        if total_files == 0:
            upload_progress['status'] = 'completed'
            return
        
        # Upload files
        for root, dirs, files in os.walk(SOURCE_FOLDER):
            # Check if current directory should be excluded
            if should_exclude_path(root, SOURCE_FOLDER):
                # Clear dirs list to prevent os.walk from descending into subdirectories
                dirs.clear()
                continue
            
            # Filter out excluded directories from dirs list
            dirs[:] = [d for d in dirs if not should_exclude_path(os.path.join(root, d), SOURCE_FOLDER)]
            
            # Upload files in current directory
            for file in files:
                if upload_progress['status'] != 'running':
                    return  # Upload was cancelled
                
                local_file_path = os.path.join(root, file)
                
                # Skip if file path should be excluded
                if should_exclude_path(local_file_path, SOURCE_FOLDER):
                    continue
                
                # Calculate relative path from source folder
                relative_path = os.path.relpath(local_file_path, SOURCE_FOLDER)
                
                # Create S3 key with subfolder
                s3_key = f"{subfolder.strip('/')}/{relative_path}".replace('\\', '/')
                
                try:
                    upload_progress['current_file'] = relative_path
                    file_size = os.path.getsize(local_file_path)
                    
                    # Create progress callback for individual file uploads
                    def progress_callback(bytes_transferred):
                        # This callback is called during file transfer
                        # Note: This is for individual file progress, not total progress
                        pass
                    
                    # Upload file with optimized configuration
                    s3_client.upload_file(
                        local_file_path, 
                        bucket_name, 
                        s3_key,
                        Config=transfer_config,
                        Callback=progress_callback
                    )
                    
                    # Update overall progress after successful upload
                    upload_progress['bytes_uploaded'] += file_size
                    upload_progress['files_processed'] += 1
                    
                except Exception as e:
                    print(f"Error uploading {relative_path}: {str(e)}")
                    # Continue with next file on error
                    continue
        
        upload_progress['status'] = 'completed'
        upload_progress['current_file'] = ''
        
    except Exception as e:
        upload_progress['status'] = 'error'
        upload_progress['error_message'] = str(e)
        print(f"Upload error: {str(e)}")

@app.route('/s3uploader/healthz', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/s3uploader/s3config', methods=['GET'])
def get_s3_configuration():
    """Get S3 configuration info"""
    try:
        config, error = get_s3_config()
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 500
            
        return jsonify({
            'success': True,
            'endpoint': config['endpoint'],
            'bucket': config['bucket'],
            'region': config['region']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/s3uploader/foldersize', methods=['GET'])
def get_folder_size():
    """Get size and file count of the source folder"""
    try:
        size_bytes, file_count = calculate_folder_size(SOURCE_FOLDER)
        
        # Add debug information
        debug_info = {
            'folder_exists': os.path.exists(SOURCE_FOLDER),
            'exclude_env': os.getenv('S3UPLOADER_EXCLUDE_UPLOAD', ''),
        }
        
        # Check if folder exists and add some basic info
        if os.path.exists(SOURCE_FOLDER):
            try:
                # Get basic directory listing
                dir_contents = os.listdir(SOURCE_FOLDER)
                debug_info['direct_subdirs'] = [d for d in dir_contents if os.path.isdir(os.path.join(SOURCE_FOLDER, d))]
                debug_info['direct_files'] = [f for f in dir_contents if os.path.isfile(os.path.join(SOURCE_FOLDER, f))]
            except Exception as e:
                debug_info['listing_error'] = str(e)
        
        return jsonify({
            'success': True,
            'size_bytes': size_bytes,
            'size_formatted': format_size(size_bytes),
            'file_count': file_count,
            'folder_path': SOURCE_FOLDER,
            'debug': debug_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/s3uploader/upload', methods=['POST'])
def start_upload():
    """Start upload process"""
    try:
        data = request.get_json()
        subfolder = data.get('subfolder', '').strip()
        
        # Validate subfolder
        if not subfolder or subfolder == '/':
            return jsonify({
                'success': False,
                'error': 'Subfolder cannot be empty or just "/"'
            }), 400
        
        # Check if upload is already running
        if upload_progress['status'] == 'running':
            return jsonify({
                'success': False,
                'error': 'Upload is already in progress'
            }), 409
        
        # Start upload in background thread
        upload_thread = threading.Thread(
            target=upload_folder_to_s3, 
            args=(subfolder,),
            daemon=True
        )
        upload_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Upload started'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/s3uploader/upload/progress', methods=['GET'])
def get_upload_progress():
    """Get current upload progress"""
    return jsonify({
        'success': True,
        'progress': upload_progress.copy()
    })

@app.route('/s3uploader/upload/cancel', methods=['POST'])
def cancel_upload():
    """Cancel current upload"""
    global upload_progress
    
    if upload_progress['status'] == 'running':
        upload_progress['status'] = 'cancelled'
        return jsonify({
            'success': True,
            'message': 'Upload cancelled'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No upload in progress'
        }), 400

@app.route('/s3uploader/debug', methods=['GET'])
def debug_folder_scan():
    """Debug endpoint to show what files are found and excluded"""
    try:
        debug_info = {
            'source_folder': SOURCE_FOLDER,
            'source_exists': os.path.exists(SOURCE_FOLDER),
            'found_files': [],
            'excluded_files': [],
            'found_dirs': [],
            'excluded_dirs': [],
            'total_size': 0,
            'file_count': 0,
            'exclude_env': os.getenv('S3UPLOADER_EXCLUDE_UPLOAD', ''),
        }
        
        if not os.path.exists(SOURCE_FOLDER):
            debug_info['error'] = f"Source folder {SOURCE_FOLDER} does not exist"
            return jsonify(debug_info)
        
        # Walk through the directory and log everything
        for root, dirs, files in os.walk(SOURCE_FOLDER):
            relative_root = os.path.relpath(root, SOURCE_FOLDER)
            
            # Check if current directory is excluded
            is_root_excluded = should_exclude_path(root, SOURCE_FOLDER)
            
            if is_root_excluded:
                debug_info['excluded_dirs'].append({
                    'path': relative_root,
                    'full_path': root,
                    'reason': 'directory excluded'
                })
                continue
            else:
                debug_info['found_dirs'].append(relative_root)
            
            # Check each file
            for file in files:
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, SOURCE_FOLDER)
                
                is_file_excluded = should_exclude_path(file_path, SOURCE_FOLDER)
                
                try:
                    file_size = os.path.getsize(file_path)
                except (OSError, IOError):
                    file_size = 0
                
                if is_file_excluded:
                    debug_info['excluded_files'].append({
                        'path': relative_file_path,
                        'size': file_size,
                        'reason': 'file excluded'
                    })
                else:
                    debug_info['found_files'].append({
                        'path': relative_file_path,
                        'size': file_size
                    })
                    debug_info['total_size'] += file_size
                    debug_info['file_count'] += 1
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Check if source folder exists
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Warning: Source folder {SOURCE_FOLDER} does not exist")
    
    # Check S3 configuration but don't crash if missing
    config, error = get_s3_config()
    if error:
        print(f"Warning: S3 configuration issue: {error}")
        print("Application will start but S3 functionality will not work until configuration is fixed")
    else:
        print("S3 configuration validated successfully")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False) 