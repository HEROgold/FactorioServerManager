#!/usr/bin/env bash
# deploy-notifier command for FSM: run the notified backend and frontend images.
# Lives in ~/FactorioServerManager on the VPS; the verifier (a container with that
# directory mounted at the same path) runs it after validating DEPLOY_IMAGE against
# [apps.fsm]'s image_pattern. It exits 0 when the deploy succeeded and non-zero otherwise.
set -euo pipefail

project_dir=${FSM_PROJECT_DIR:-/home/herogold/FactorioServerManager}
backend_pattern='^ghcr\.io/herogold/factorioservermanager-backend@sha256:[0-9a-f]{64}$'
frontend_pattern='^ghcr\.io/herogold/factorioservermanager-frontend@sha256:[0-9a-f]{64}$'

cd "$project_dir"

# The verifier already checked DEPLOY_IMAGE; checking again costs nothing.
[[ "${DEPLOY_IMAGE:-}" =~ $backend_pattern ]] || { echo "backend image '${DEPLOY_IMAGE:-}' is not a pinned FSM backend" >&2; exit 1; }

# The notification arrives on stdin. The verifier does not validate `extra`, so
# this script checks extra.frontend_image before it reaches docker or .env.deploy.
# (A valid ref never contains a quote or backslash, so no JSON parser is needed, and none is on PATH.)
frontend_image=$(grep -o '"frontend_image": *"[^"\\]*"' | sed 's/.*"\([^"\\]*\)"$/\1/' || true)
[[ "$frontend_image" =~ $frontend_pattern ]] || { echo "frontend image '$frontend_image' is not a pinned FSM frontend" >&2; exit 1; }

# The verifier runs this with no HOME. Both images are public, so a pull needs no
# login, but docker still wants a config dir.
export DOCKER_CONFIG=${DOCKER_CONFIG:-/home/herogold/.docker}

docker pull --quiet "$DEPLOY_IMAGE"
docker pull --quiet "$frontend_image"

[[ -f .env.deploy ]] && cp .env.deploy .env.deploy.prev
printf 'FSM_BACKEND_IMAGE=%s\nFSM_FRONTEND_IMAGE=%s\n' "$DEPLOY_IMAGE" "$frontend_image" >.env.deploy.tmp
mv .env.deploy.tmp .env.deploy

compose() { docker compose --env-file .env --env-file .env.deploy "$@"; }

# --wait blocks until the backend's healthcheck passes. The verifier kills this
# script after 900 s. The two waits take at most 600 s, which leaves 300 s for
# the pulls above.
if ! compose up -d --wait --wait-timeout 420 --pull missing --no-build; then
  echo "deploy of $DEPLOY_IMAGE and $frontend_image failed, rolling back" >&2
  compose logs --tail 50 backend frontend >&2 || true
  if [[ -f .env.deploy.prev ]]; then
    mv .env.deploy.prev .env.deploy
    compose up -d --wait --wait-timeout 180 --pull missing --no-build || true
  fi
  exit 1
fi
echo "deployed $DEPLOY_IMAGE and $frontend_image from ${DEPLOY_REPOSITORY:-?} at ${DEPLOY_SHA:-?}"
