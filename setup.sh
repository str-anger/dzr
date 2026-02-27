#!/bin/bash

if [ ! -d .venv ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi
source .venv/bin/activate
# for reverse proxy: base URL;
# for local server: port number.
python server.py https://example.com/dzr/ 5000