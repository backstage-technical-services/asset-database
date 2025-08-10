#!/usr/bin/env bash
set -eo pipefail

function log() {
    echo "level=INFO caller=entrypoint msg=\"${1}\""
}

if [[ ! -d .venv ]]; then
  log "Installing Python dependencies"
  pipenv sync
fi

if [[ ! -d node_modules ]]; then
  log "Installing Node.js dependencies"
  npm install
fi

log "Starting the app"
exec "$@"
