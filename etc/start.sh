#!/bin/bash
# shell script for autostart service.

# working directory should be blescan-backend (one level above)

git pull

source .venv/bin/activate

python blescan.py
