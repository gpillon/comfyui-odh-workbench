#!/bin/bash
echo "Status: 200"
echo "Content-type: application/json"
echo

# Python script to parse the nginx log and get last activity
python3 << 'PYTHON_EOF'
import re
import json
from datetime import datetime
import sys
import os
import urllib.request
import urllib.error

STARTUP_COMPLETE_MARKER="/tmp/.startup_complete"
UUID_FILE="/tmp/comfyui_uuid"

def get_comfyui_id():
    """Get the ComfyUI UUID from file, or return all-zeros UUID if not found"""
    try:
        if os.path.exists(UUID_FILE):
            with open(UUID_FILE, 'r') as f:
                return f.read().strip()
        else:
            return "00000000-0000-0000-0000-000000000000"
    except Exception:
        return "00000000-0000-0000-0000-000000000000"

def get_last_activity_from_log():
    log_file = "/tmp/log/nginx/comfyui.access.log"
    
    # Check if log file exists
    if not os.path.exists(log_file):
        # If no log file, return current time
        return datetime.now().isoformat() + "Z"
    
    try:
        # Read the last line of the log file (most recent activity)
        with open(log_file, 'rb') as f:
            # Seek to end and read backwards to get last line efficiently
            f.seek(-2, 2)  # Jump to the second last byte
            while f.read(1) != b"\n":
                f.seek(-2, 1)  # Keep jumping back until we find a newline
            last_line = f.readline().decode('utf-8').strip()
        
        # Parse timestamp from log line format: [02/Jul/2025:10:49:49 +0000]
        timestamp_match = re.search(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}) ([+-]\d{4})\]', last_line)
        
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            timezone_str = timestamp_match.group(2)
            
            # Parse the timestamp
            dt = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S')
            
            # Convert to ISO format with Z suffix (assuming UTC)
            iso_timestamp = dt.isoformat() + ".000000Z"
            return iso_timestamp
        else:
            # If can't parse timestamp, return current time
            return datetime.now().isoformat() + "Z"
            
    except Exception:
        # If any error reading log, return current time
        return datetime.now().isoformat() + "Z"

def get_execution_state():
    log_file = "/tmp/log/nginx/comfyui.access.log"
    
    # If startup is not complete, return "starting"
    if not os.path.exists(STARTUP_COMPLETE_MARKER):
        return "starting"
    
    # If log file doesn't exist but startup is complete, return "idle"
    if not os.path.exists(log_file):
        return "idle"
    
    # If log file exists and startup is complete, check ComfyUI status
    try:
        # Try to query the ComfyUI prompt endpoint using urllib
        req = urllib.request.Request('http://127.0.0.1:8188/prompt')
        req.add_header('User-Agent', 'ComfyUI-Status-Check')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            response_text = response.read().decode('utf-8')
            
            # Parse JSON response
            try:
                data = json.loads(response_text)
                queue_remaining = data.get('exec_info', {}).get('queue_remaining', 0)
                return "busy" if queue_remaining > 0 else "idle"
            except json.JSONDecodeError:
                return "idle"
                
    except (urllib.error.URLError, urllib.error.HTTPError, Exception):
        return "idle"

# Get ComfyUI ID, last activity and execution state
comfyui_id = get_comfyui_id()
last_activity = get_last_activity_from_log()
execution_state = get_execution_state()

# Output the expected format
output = [{
    "id": comfyui_id,
    "name": "python3",
    "last_activity": last_activity,
    "execution_state": execution_state,
    "connections": 1
}]

print(json.dumps(output))

PYTHON_EOF