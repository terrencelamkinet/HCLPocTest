#!/usr/bin/env bash
# dev-login — get JWT token for dev, no OTP needed
# Usage: ./dev-login.sh [email] [password]
#   --browser : output JS snippet for browser_console injection

cd "$(dirname "$0")/.."
python3 backend/scripts/dev_login.py "$@"
