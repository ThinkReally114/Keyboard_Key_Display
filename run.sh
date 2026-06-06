#!/bin/bash

echo "  Keyboard Key Display by ThinkReally"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python not found. Please install Python first."
    exit 1
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Error: The tkinter module was not found."
    echo "Please use the following command to install tkinter: sudo apt install python3-tk (Debian/Ubuntu)"
    exit 1
fi

if [ ! -r /dev/input/event0 ]; then
    echo "Tip: Root permission is required to listen for keyboard events"
    
    if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
        echo "Tip: Detected a Wayland session, window transparency may not work. Please try X11 session"
        echo ""
    fi
    
    echo "Starting with sudo to..."
    echo ""
    sudo -E python3 key_display.py
else
    echo "Starting application..."
    echo ""
    python3 key_display.py
fi
