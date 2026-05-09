#!/bin/bash

# Engineering Incident Intelligence - Quick Run Script

echo "🚨 Engineering Incident Intelligence"
echo "=================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🚀 Launching Streamlit app..."
echo ""
echo "   📍 Open your browser to: http://localhost:8501"
echo "   📍 Press Ctrl+C to stop"
echo ""
echo "   The app includes 3 sample incidents pre-loaded!"
echo ""

# Run the app
streamlit run app.py
