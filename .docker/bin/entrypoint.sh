#!/usr/bin/env bash
set -eo pipefail

function log() {
    echo "caller=entrypoint level=info msg=\"${1}\""
}

log "Running migrations"
python3 manage.py migrate

log "Starting Django"
exec "$@"
