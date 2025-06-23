#!/bin/bash
echo "Status: 200"
echo "Content-type: application/json"
echo

# Get current time for last_activity
CURRENT_TIME=$(date -Iseconds)

# Try to query the ComfyUI prompt endpoint
PROMPT_STATUS=$(curl -s http://127.0.0.1:8080/prompt)
if [[ $? -eq 0 && "$PROMPT_STATUS" == *"queue_remaining"* ]]; then
    # Parse the JSON response if it contains queue_remaining
    QUEUE_REMAINING=$(echo $PROMPT_STATUS | grep -Po '"queue_remaining":\K[0-9]+' || echo "0")
    
    # Determine status based on queue_remaining
    if [ "$QUEUE_REMAINING" -gt "0" ]; then
        STATUS="busy"
    else
        STATUS="idle"
    fi
else
    # Default to idle if we can't get a valid response
    STATUS="idle"
fi

# Export in format expected by the culling engine
echo '[{"id":"comfyui","name":"comfyui","last_activity":"'$CURRENT_TIME'","execution_state":"'$STATUS'","connections":1}]'
EOF
chmod +x /tmp/access.cgi