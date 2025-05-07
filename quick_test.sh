#!/bin/bash

# Quick test script for GitHub Documentation Generator
# Tests the API with a GitHub repository and opens the generated overview file
# Usage: ./quick_test.sh [github_url]
# If no URL is provided, it will use the default demo URL

# Default demo URL
DEFAULT_URL="https://github.com/openai/openai-agents-python"

# Get the URL from command line argument or use default
REPO_URL=${1:-$DEFAULT_URL}

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Check if the server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "Starting the FastAPI server..."
    uvicorn src.main:app --reload &
    SERVER_PID=$!
    
    # Wait for server to start
    echo "Waiting for server to start..."
    sleep 5
fi

# Create docs directory if it doesn't exist
mkdir -p docs

# Make the API request with proper JSON formatting
echo "Generating documentation for $REPO_URL..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/generate-docs" \
    -H "Content-Type: application/json" \
    -d "{\"repo_url\": \"$REPO_URL\", \"diagram\": false}")

# Print the full response for debugging
echo "Response received:"
echo "$RESPONSE"

# Check if the response contains "ok":true
if [[ $RESPONSE == *"\"ok\":true"* ]]; then
    echo "Documentation generated successfully!"
    
    # Extract the path to the OVERVIEW.md file using a more robust approach
    OVERVIEW_PATH=$(echo "$RESPONSE" | grep -o '"/[^"]*OVERVIEW.md"' | tr -d '"')
    
    # Check if the file exists
    if [ -f "$OVERVIEW_PATH" ]; then
        echo "Opening $OVERVIEW_PATH..."
        open "$OVERVIEW_PATH"  # For macOS
        # For Linux, use: xdg-open "$OVERVIEW_PATH"
    else
        echo "Overview file not found at $OVERVIEW_PATH"
        echo "Generated files:"
        echo "$RESPONSE" | grep -o '"/[^"]*\.md"' | tr -d '"'
    fi
else
    echo "Error generating documentation:"
    echo "$RESPONSE"
fi

# Kill the server process if we started it
if [ ! -z "$SERVER_PID" ]; then
    echo "Stopping the server..."
    kill $SERVER_PID
fi
