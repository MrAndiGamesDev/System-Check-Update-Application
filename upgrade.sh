#!/bin/bash

# Text formatting
OK="$(tput setaf 2)[OK]$(tput sgr0)"
ERROR="$(tput setaf 1)[ERROR]$(tput sgr0)"
NOTE="$(tput setaf 3)[NOTE]$(tput sgr0)"
WARN="$(tput setaf 5)[WARN]$(tput sgr0)"
CAT="$(tput setaf 6)[ACTION]$(tput sgr0)"
RESET=$(tput sgr0)

# Script metadata
SCRIPT_NAME="application"
SCRIPT_VERSION="0.1.0"
SCRIPT_EXECUTABLE="./$SCRIPT_NAME.py"

# Function to display a loading animation
display_loading() {
    local speed=0.05
    local width=40
    local progress=0
    local spinner=('|' '/' '-' '\')
    local spin_index=0

    while [ $progress -le $width ]; do
        printf "\r$CAT Loading: ["
        printf "%-${width}s" "$(head -c $progress < /dev/zero | tr '\0' '#')"
        printf "] %3d%% ${spinner[$spin_index]}" $((progress * 100 / width))
        sleep $speed
        progress=$((progress + 1))
        spin_index=$(( (spin_index + 1) % 4 ))
        clear
    done
    echo ""
}

# Function to terminate processes safely
terminate_processes() {
    TARGET_PROCESSES=("$SCRIPT_EXECUTABLE")  # Add related scripts if needed

    for PROC in "${TARGET_PROCESSES[@]}"; do
        EXISTING_PROCESS=$(pgrep -f $PROC)
        if [[ -n "$EXISTING_PROCESS" ]]; then
            echo "$WARN Terminating existing instances of $PROC..."
            kill $EXISTING_PROCESS
            sleep 2  # Allow time for processes to exit gracefully
            if pgrep -f $PROC > /dev/null; then
                echo "$WARN Forcefully terminating remaining processes of $PROC..."
                kill -9 $EXISTING_PROCESS
            fi
        else
            echo "$OK No running instances of $PROC found."
        fi
    done
}

# Function to start the script
start_script() {
    if [[ -f "$SCRIPT_EXECUTABLE" ]]; then
        echo "$NOTE Running $SCRIPT_NAME..."
        python3 "$SCRIPT_EXECUTABLE" &
        exit 0
    else
        echo "$ERROR $SCRIPT_EXECUTABLE not found."
        exit 1
    fi
}

# Main script execution
main() {
    display_loading
    echo "$NOTE Ensuring no other instances of $SCRIPT_NAME are running..."
    terminate_processes
    echo "$NOTE Starting $SCRIPT_NAME (Version: $SCRIPT_VERSION)..."
    start_script
}

# Run the main function
main
