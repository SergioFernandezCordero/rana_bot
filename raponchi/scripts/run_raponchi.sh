#!/usr/bin/env bash
echo "## Running Raponchi"
echo "# Activating Virtualenv"
. /opt/raponchi/venv/bin/activate && \

echo "# Run Raponchi"
python3 /opt/raponchi/raponchi.py
