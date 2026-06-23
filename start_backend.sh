#!/bin/bash
# Start the Health Insurance Platform backend
# macOS: DYLD_LIBRARY_PATH must be set via 'env' (not 'export') for WeasyPrint PDF
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"
exec env DYLD_LIBRARY_PATH=/opt/homebrew/lib \
  venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info "$@"
