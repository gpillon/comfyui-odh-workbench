#!/bin/bash
echo "Status: 200"
echo "Content-type: application/json"
echo

# Query the ComfyUI prompt endpoint
PROMPT_STATUS=$(curl -s http://127.0.0.1:8080/prompt)
QUEUE_REMAINING=$(echo $PROMPT_STATUS | grep -Po '"queue_remaining":\K[0-9]+' || echo "0")

# Get current time for last_activity
CURRENT_TIME=$(date -Iseconds)

# Determine status based on queue_remaining
if [ "$QUEUE_REMAINING" -gt "0" ]; then
    STATUS="busy"
else
    STATUS="idle"
fi

# Export in format expected by the culling engine
echo '[{"id":"comfyui","name":"comfyui","last_activity":"'$CURRENT_TIME'","execution_state":"'$STATUS'","connections":1}]' 