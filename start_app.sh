#!/bin/bash
# Start Streamlit Psychology Learning Assistant App

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -f "./venv/bin/streamlit" ]; then
    STREAMLIT_BIN="./venv/bin/streamlit"
else
    STREAMLIT_BIN="streamlit"
fi

echo "🚀 Starting Psychology Learning Assistant Web App on http://localhost:8501..."

# Kill existing instance if running
if [ -f "app.pid" ]; then
    PID=$(cat app.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
    fi
    rm -f app.pid
fi
pkill -f "streamlit run app.py" 2>/dev/null

# Launch Streamlit in background
nohup $STREAMLIT_BIN run app.py --server.port 8501 --server.headless true > app.log 2>&1 &
echo $! > app.pid

echo "✅ App started successfully (PID: $(cat app.pid))."
echo "🌐 Local URL: http://localhost:8501"
echo "🌐 Network URL: http://10.0.2.15:8501"
echo "🌐 External URL: http://157.100.108.78:8501"
