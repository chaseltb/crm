#!/usr/bin/env bash
# NeuroInk demo — runs on port 8052
# Login: demo@neuroink.io / neuroink2024

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CRM_CONFIG="$SCRIPT_DIR/config.neuroink.yaml"
export CRM_DB="$SCRIPT_DIR/data/neuroink/etherealcrm.db"
export CRM_PORT=8052

echo "Starting NeuroInk demo on http://localhost:8052"
echo "Login: demo@neuroink.io / neuroink2024"
echo ""

python "$SCRIPT_DIR/app.py"
