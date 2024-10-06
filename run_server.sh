#!/bin/bash

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate

    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    pip install --no-cache-dir -r requirements.txt
else
    echo "Virtual environment found."
    source venv/bin/activate
fi

uvicorn main:app --host 0.0.0.0 --port 5500
