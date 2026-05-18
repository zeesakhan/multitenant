#!/usr/bin/env bash
# Generate cryptographically secure secrets for .env configuration.
# Usage: bash scripts/generate_secrets.sh
set -euo pipefail

echo "# Generated secrets — paste into your .env file"
echo ""
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
echo "ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
