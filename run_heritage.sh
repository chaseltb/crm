#!/usr/bin/env bash
# Heritage Landscaping demo — runs on port 8051
# Login: demo@heritagelandscaping.com / heritage2024

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CRM_CONFIG="$SCRIPT_DIR/config.heritage.yaml"
export CRM_DB="$SCRIPT_DIR/data/heritage/etherealcrm.db"
export CRM_PORT=8051

echo "Starting Heritage Landscaping demo on http://localhost:8051"
echo "Login: demo@heritagelandscaping.com / heritage2024"
echo ""

python "$SCRIPT_DIR/app.py"
