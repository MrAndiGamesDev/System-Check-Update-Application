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
SCRIPT_VERSION="0.0.5"
SCRIPT_EXECUTABLE="./application.py"

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
        "Windows") echo ""; ;; # Not implemented
        *) echo ""; ;;
    esac
}

# Function to get the current version of the script
get_current_version() {
    if command -v conda &>/dev/null; then
        conda list | grep -i "$SCRIPT_NAME" | awk '{print $2}'
    elif command -v pip &>/dev/null; then
        pip show "$SCRIPT_NAME" 2>/dev/null | grep Version | awk '{print $2}'
    else
        echo ""
    fi
}

# Main script execution
main() {
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

    current_version=$(get_current_version)
    if [[ "$current_version" == "$SCRIPT_VERSION" ]]; then
        echo "$OK $SCRIPT_NAME is already up-to-date ($SCRIPT_VERSION)."
        exit 0
    fi

    new_version=$(get_current_version)
    if [[ "$new_version" == "$SCRIPT_VERSION" ]]; then
        echo "$OK $SCRIPT_NAME successfully upgraded to version $SCRIPT_VERSION."
    else
        echo "$ERROR $SCRIPT_NAME upgrade failed. Current version: $new_version"
        exit 1
    fi

    # Run the updated script
    if [[ -f "$SCRIPT_EXECUTABLE" ]]; then
        echo "$NOTE Running $SCRIPT_NAME..."
        python3 "$SCRIPT_EXECUTABLE"
    else
        echo "$ERROR $SCRIPT_EXECUTABLE not found."
        exit 1
    fi
}

# Run the main function
main