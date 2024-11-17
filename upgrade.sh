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
SCRIPT_VERSION="0.0.7"
SCRIPT_EXECUTABLE="./application.py"
BACKUP_DIR="$HOME/downloads/archupdater"  # Directory where the latest version is stored (locally)

# Function to display a loading animation
display_loading() {
    local speed=0.05
    local width=40
    local progress=0
    local spinner=('|' '/' '-' '\')
    local spin_index=0

    while [ $progress -le $width ]; do
        printf "\r$CAT Updating: ["
        printf "%-${width}s" "$(head -c $progress < /dev/zero | tr '\0' '#')"
        printf "] %3d%% ${spinner[$spin_index]}" $((progress * 100 / width))
        sleep $speed
        progress=$((progress + 1))
        spin_index=$(( (spin_index + 1) % 4 ))
        clear
    done
    echo ""
}

# Function to detect the operating system
detect_os() {
    case "$(uname -s)" in
        Linux*) echo "Linux";;
        Darwin*) echo "macOS";;
        CYGWIN*|MINGW*|MSYS*) echo "Windows";;
        *) echo "Unknown";;
    esac
}

# Function to get the Downloads directory based on OS
get_downloads_dir() {
    case "$1" in
        "Linux")
            command -v xdg-user-dir &>/dev/null && xdg-user-dir DOWNLOAD || echo "$HOME/Downloads"
            ;;
        "macOS") echo "$HOME/Downloads";;
        "Windows") echo ""; ;; # Not implemented for Windows
        *) echo ""; ;;
    esac
}

# Function to update the script from the local backup directory
update_script() {
    echo "$CAT Updating $SCRIPT_NAME..."

    # Step 1: Check if the backup directory contains the new version
    if [[ ! -f "$BACKUP_DIR/$SCRIPT_NAME.py" ]]; then
        echo "$ERROR Backup directory does not contain the new version of the script."
        exit 1
    fi

    # Step 2: Display loading animation while replacing the script
    display_loading

    # Step 3: Replace the old script with the new version from the backup directory
    echo "$NOTE Replacing the old script..."
    mv "$BACKUP_DIR/$SCRIPT_NAME.py" "$SCRIPT_EXECUTABLE"

    # Step 4: Restart the application using the updated script
    echo "$NOTE Restarting the application..."
    python3 "$SCRIPT_EXECUTABLE" &
    exit 0  # Exit the current instance of the script to allow the new one to start
}

# Main script execution
main() {
    display_loading
    OS=$(detect_os)
    echo "$NOTE Detected Operating System: $OS"

    if [[ "$OS" == "Unknown" ]]; then
        echo "$ERROR Unsupported Operating System: $OS"
        exit 1
    fi

    DOWNLOADS_DIR=$(get_downloads_dir "$OS")
    if [[ -z "$DOWNLOADS_DIR" ]]; then
        echo "$ERROR Could not determine the Downloads directory."
        exit 1
    fi

    SCRIPT_PATH="$DOWNLOADS_DIR/archupdater/$SCRIPT_NAME.py"

    # Check if there is a newer version of the script available in the backup directory
    if [[ -f "$BACKUP_DIR/$SCRIPT_NAME.py" ]]; then
        # Only proceed with the update if the backup version is different
        echo "$OK Found new version in the backup directory."
        update_script
    else
        echo "$OK $SCRIPT_NAME is already up-to-date Version: $SCRIPT_VERSION"
    fi

    # If no update is needed, run the existing script
    if [[ -f "$SCRIPT_EXECUTABLE" ]]; then
        echo "$NOTE Running $SCRIPT_NAME..."
        kill -9 $(pgrep -f $SCRIPT_EXECUTABLE)
        python3 "$SCRIPT_EXECUTABLE"
        exit 1 "$SCRIPT_EXECUTABLE"
    else
        echo "$ERROR $SCRIPT_EXECUTABLE not found."
        exit 1
    fi
}

# Run the main function
main