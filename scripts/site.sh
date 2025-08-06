#!/usr/bin/env bash
set -eo pipefail
readonly rootDir="$(dirname "$(realpath "${0}")")/.."

# Ensure that Docker is running...
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running." >&2
  exit 1
fi

function _showHelp() {
  cat <<EOF
##########################
##  BTS Asset Database  ##
##########################

This scripts provides some helpful utility functions for interacting with the local Docker container, to aid with local
development.

Commands:
  docker [OPTIONS] COMMAND
    Run any normal docker-compose command.
  start
    Start the site and dependencies.
  stop
    Stop the site and dependencies.
  reset
    Stop the site and dependencies, clears the database, and restarts the site and dependencies.
  status
    View the status of the docker containers.
  rebuild
    Pull the latest base image and rebuild the site's docker image and container.
  exec COMMAND
    Run any command inside the container.
  pipenv [OPTIONS] COMMAND
    Run any pipenv command (alias for pipenv run).
  npm [OPTIONS] COMMAND
    Run any npm script (alias for npm run).
  install [--update]
    Install both the Python and JavaScript dependencies. Use the --update flag to update the dependencies to their
    latest versions.
  update
    Update your local copy of the site, including installing any new dependencies and running any new migrations.
  help
    Show this information.
EOF
}

function _docker() {
  docker compose -f "$rootDir/docker-compose.yml" "$@"
}

function _start() {
  _docker up -d
}

function _stop() {
  _docker stop
}

function _reset() {
  _docker down
  _start
}

function _requireRunning() {
  _docker ps | grep site &>/dev/null || {
    echo "Site not running. Run start and try again." >&2
    exit 2
  }
}

function _status() {
  _docker ps
}

function _rebuild() {
  # Stop the network
  _stop

  # Pull the base image
  _docker pull site

  # Rebuild the site
  _docker build \
    --build-arg="USER_ID=$(id -u "$USER")" \
    --build-arg="GROUP_ID=$(id -g "$USER")" \
    site

  # Start
  _start
}

function _exec() {
  _requireRunning
  _docker exec --user www-data:www-data site "$@"
}

function _pipenv() {
  _exec pipenv run "$@"
}

function _npm() {
  _exec npm run "$@"
}

function _install() {
  _requireRunning

  if [[ "${1}" == "--update" ]]; then
    _exec pipenv update
    _exec npm update
  else
    _exec pipenv sync
    _exec npm install
  fi
}

function _update() {
  _requireRunning

  pushd "${rootDir}" &>/dev/null

  if [[ ! $(ssh-keygen -F github.com) ]]; then
      echo "=> Adding SSH keys for github.com"
      ssh-keyscan -H github.com >> ~/.ssh/known_hosts
  fi

  echo "=> Updating your local copy ..."
  git pull --ff-only &>/dev/null

  echo "=> Installing dependencies ..."
  _install &>/dev/null

  echo "=> Running migrations"
  _pipenv python3 manage.py migrate

  echo "=> Done."

  popd &>/dev/null
}

function _logs() {
  docker compose logs -f site
}

readonly cmd="${1}"
shift

case $cmd in
docker)
  _docker "$@"
  ;;
start)
  _start
  ;;
stop)
  _stop
  ;;
reset)
  _reset
  ;;
status)
  _status
  ;;
rebuild)
  _rebuild
  ;;
logs)
  _logs
  ;;
exec)
  _exec "$@"
  ;;
pipenv)
  _pipenv "$@"
  ;;
npm)
  _npm "$@"
  ;;
install)
  _install "$@"
  ;;
update)
  _update
  ;;
help)
  _showHelp
  ;;
*)
  _showHelp
  ;;
esac
