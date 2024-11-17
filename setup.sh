#!/bin/bash

# Check if a file is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

# Try to make the file executable
chmod +x "$1"

# Check if chmod was successful
if [ $? -eq 0 ]; then
    echo "The file '$1' is now executable."
else
    echo "Failed to make '$1' executable."
fi