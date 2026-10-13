#!/bin/bash
# Stop Streamlit Psychology Learning Assistant App

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🛑 Stopping Psychology Learning Assistant Web App..."

if [ -f "app.pid" ]; then
    PID=$(cat app.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo "Stopped process $PID."
    fi
    rm -f app.pid
fi

# Fallback cleanup for any running Streamlit app.py processes
pkill -f "streamlit run app.py" 2>/dev/null

echo "✅ App stopped successfully."
