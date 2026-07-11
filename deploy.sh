#!/usr/bin/env bash
# Redeploy FSM on the production host. Invoked by the GitHub Actions deploy
# workflow over Tailscale SSH, and safe to run by hand.
set -euo pipefail

REPO_DIR="${FSM_DIR:-$HOME/FactorioServerManager}"
cd "$REPO_DIR"

echo "==> Updating source"
git pull --ff-only

echo "==> Building and (re)starting containers"
docker compose -f docker-compose.prod.yml --env-file .env up -d --build

echo "==> Pruning dangling images"
docker image prune -f

echo "==> Done. Current state:"
docker compose -f docker-compose.prod.yml ps
