#!/bin/bash
# Start the Health Insurance Platform frontend (Vite dev server)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend"
exec npm run dev
