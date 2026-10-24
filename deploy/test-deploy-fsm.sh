#!/usr/bin/env bash
# Tests for deploy-fsm.sh. Each case runs the script in a scratch project dir
# with a fake `docker` on PATH that records its arguments.
#   bash deploy/test-deploy-fsm.sh
# check() evals its condition later, so the conditions stay single-quoted
# (SC2016), and `status` is read only inside them (SC2034).
# shellcheck disable=SC2016,SC2034
set -uo pipefail

script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/deploy-fsm.sh"
digest_a=$(printf 'a%.0s' {1..64})
digest_b=$(printf 'b%.0s' {1..64})
backend_a="ghcr.io/herogold/factorioservermanager-backend@sha256:$digest_a"
backend_b="ghcr.io/herogold/factorioservermanager-backend@sha256:$digest_b"
frontend_a="ghcr.io/herogold/factorioservermanager-frontend@sha256:$digest_a"
frontend_b="ghcr.io/herogold/factorioservermanager-frontend@sha256:$digest_b"

failures=0
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

mkdir -p "$work/bin"
cat >"$work/bin/docker" <<'EOF'
#!/usr/bin/env bash
echo "$*" >>"$FAKE_DOCKER_LOG"
# FAKE_UP_FAILS=n fails `compose ... up` while it is at most the n-th up in this log.
if [[ "$1" == compose && " $* " == *" up "* ]]; then
  count=$(( $(cat "$FAKE_DOCKER_LOG.up" 2>/dev/null || echo 0) + 1 ))
  echo "$count" >"$FAKE_DOCKER_LOG.up"
  (( count <= ${FAKE_UP_FAILS:-0} )) && exit 1
fi
exit 0
EOF
chmod +x "$work/bin/docker"

# new_project: a fresh project dir and docker log for one case.
new_project() {
  project="$work/project-$1"
  mkdir -p "$project"
  touch "$project/.env"
  log="$project/docker.log"
}

# deploy <backend> <payload>: run the script as the verifier does.
deploy() {
  printf '%s' "$2" | PATH="$work/bin:$PATH" FAKE_DOCKER_LOG="$log" \
    FSM_PROJECT_DIR="$project" DEPLOY_IMAGE="$1" DEPLOY_REPOSITORY=HEROgold/FactorioServerManager \
    DEPLOY_SHA=abc "$script" >"$project/out.log" 2>&1
}

payload() { printf '{"image": "%s", "extra": {"frontend_image": "%s"}}' "$1" "$2"; }

check() {
  if eval "$2"; then
    echo "ok   $1"
  else
    echo "FAIL $1"
    sed 's/^/     | /' "$project/out.log"
    failures=$((failures + 1))
  fi
}

new_project deploys
deploy "$backend_a" "$(payload "$backend_a" "$frontend_a")"
check "valid images deploy" '[[ $? -eq 0 ]]'
check "writes .env.deploy with both images" \
  'grep -qx "FSM_BACKEND_IMAGE=$backend_a" "$project/.env.deploy" && grep -qx "FSM_FRONTEND_IMAGE=$frontend_a" "$project/.env.deploy" && [[ $(wc -l <"$project/.env.deploy") -eq 2 ]]'
check "pulls both images" 'grep -qx "pull --quiet $backend_a" "$log" && grep -qx "pull --quiet $frontend_a" "$log"'
check "runs compose up without building" \
  'grep -qx "compose -f docker-compose.prod.yml --env-file .env --env-file .env.deploy up -d --wait --wait-timeout 420 --pull missing --no-build" "$log"'
check "never runs git" '! grep -q git "$log"'

new_project keeps-prev
deploy "$backend_a" "$(payload "$backend_a" "$frontend_a")"
deploy "$backend_b" "$(payload "$backend_b" "$frontend_b")"
check "second deploy keeps the first in .env.deploy.prev" 'grep -qx "FSM_BACKEND_IMAGE=$backend_a" "$project/.env.deploy.prev"'
check "second deploy writes the new images" 'grep -qx "FSM_FRONTEND_IMAGE=$frontend_b" "$project/.env.deploy"'

new_project rollback
deploy "$backend_a" "$(payload "$backend_a" "$frontend_a")"
FAKE_UP_FAILS=2 deploy "$backend_b" "$(payload "$backend_b" "$frontend_b")"
status=$?
check "failed up exits non-zero" '[[ $status -ne 0 ]]'
check "failed up restores the previous images" 'grep -qx "FSM_BACKEND_IMAGE=$backend_a" "$project/.env.deploy"'
check "failed up runs up again for the rollback" '[[ $(grep -c " up " "$log") -eq 3 ]]'

for bad in \
  "ghcr.io/herogold/factorioservermanager-frontend:latest" \
  "ghcr.io/someone/factorioservermanager-frontend@sha256:$digest_a" \
  "ghcr.io/herogold/factorioservermanager-frontend@sha256:$digest_a; rm -rf /" \
  ""; do
  new_project "bad-frontend-$RANDOM"
  deploy "$backend_a" "$(payload "$backend_a" "$bad")"
  status=$?
  check "rejects frontend '$bad'" '[[ $status -ne 0 && ! -s "$log" && ! -e "$project/.env.deploy" ]]'
done

new_project no-extra
deploy "$backend_a" "{\"image\": \"$backend_a\"}"
status=$?
check "rejects a notification without extra.frontend_image" '[[ $status -ne 0 && ! -s "$log" ]]'

new_project bad-backend
deploy "ghcr.io/herogold/nota@sha256:$digest_a" "$(payload "$backend_a" "$frontend_a")"
status=$?
check "rejects a backend outside the pattern" '[[ $status -ne 0 && ! -s "$log" ]]'

if (( failures )); then
  echo "$failures failure(s)"
  exit 1
fi
echo "all passed"
