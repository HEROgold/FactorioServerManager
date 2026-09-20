# Artifact-based deploy: ship pre-built Docker images via GitHub Releases

## Problem

Today, `release.yml` creates a GitHub Release, then dispatches `deploy.yml`,
which SSHes into the VPS (over Tailscale) and runs `./deploy.sh` there. That
script `git pull`s the full repo and runs `docker compose ... build` **on the
VPS**, which means the VPS needs: a full git checkout, `git`, and the whole
Docker build toolchain (compilers, `-dev` headers pulled at build time, etc.)
just to redeploy.

This is also currently broken/inconsistent: `deploy.sh` was removed from the
repo in commit `3df1e2c` ("remove deploy script on repo", 2026-09-20), but
`deploy.yml` still assumes it exists at `~/FactorioServerManager/deploy.sh`,
and the README still documents it as a tracked, git-pulled file.

## Goal

Build the backend and frontend Docker images once, in CI. Attach them to the
GitHub Release as downloadable assets. The VPS never builds anything and never
needs a git checkout — it downloads the pre-built images for the release
being deployed and loads them straight into its local Docker daemon.

## Design

### 1. Build & package (`release.yml`)

After `version-check` confirms a new version, before/alongside creating the
GitHub Release:

1. `docker/setup-buildx-action` to get a buildx builder.
2. Build both images with `docker/build-push-action`, `output: type=docker`
   (loads into the runner's local daemon; nothing is pushed to any registry),
   tagged `fsm-backend:v${VERSION}` and `fsm-frontend:v${VERSION}`.
   Use `cache-from`/`cache-to: type=gha` so repeat builds reuse layers.
3. `docker save fsm-backend:v${VERSION} | gzip > fsm-backend-v${VERSION}.tar.gz`
   (same for frontend).
4. Pass both `.tar.gz` files to `softprops/action-gh-release` via its `files:`
   input, in the same step that creates the release — they become downloadable
   release assets. `generate_release_notes` stays as-is.
5. The `repository-dispatch` trigger to `deploy.yml` is unchanged; the version
   is already in its payload.

The backend image build args `FSM_UID`/`FSM_GID` are dropped from the compose
file (see §3) since the release image is fixed at uid/gid 10001 — no more
per-deploy customization of these (accepted trade-off: anyone needing a
different id builds from source instead of using the release artifact).

### 2. Deploy (`deploy.yml`)

The SSH step no longer contains any deploy mechanics — it just invokes the
`deploy.sh` that already lives on the VPS (out of band, not git-tracked, per
the recent removal), passing the version:

```yaml
- name: Deploy over SSH
  uses: appleboy/ssh-action@...
  with:
    host: ${{ secrets.PROD_HOST }}
    username: ${{ secrets.PROD_SSH_USER }}
    key: ${{ secrets.PROD_SSH_KEY }}
    script: |
      set -euo pipefail
      ./deploy.sh v${{ github.event.client_payload.version }}
```

The smoke-test step is unchanged.

### 3. `docker-compose.prod.yml` (VPS-only; see §7 — no longer tracked in git)

On the VPS's existing copy, replace each service's `build:` block with a
fixed image reference driven by an `FSM_VERSION` env var:

```yaml
backend:
  image: fsm-backend:v${FSM_VERSION}
  # (build: block and its args removed entirely)
  ...

frontend:
  image: fsm-frontend:v${FSM_VERSION}
  ...
```

`FSM_VERSION` is a new required var in the VPS's `.env`, written by
`deploy.sh` each run (see §5) before `docker compose up -d`. This is a
hand-edit on the VPS, done once when this change lands, since the file isn't
in git (§7). The `FSM_UID`/`FSM_GID` vars in `.env` stay only as the fixed
default `setup-host.sh` used for host directory ownership (they no longer
flow into an image build, since there isn't one anymore).

### 4. VPS host setup / README

- The VPS needs, once, by hand (e.g. `scp`): `docker-compose.prod.yml`,
  `.env`, `config.ini`, `scripts/setup-host.sh`, and `deploy.sh`. No git
  checkout, no `git`, no build toolchain.
- README's "One-time host setup" section drops the `git clone` framing —
  instructions become "copy these files to the host" instead of "clone the
  repo".
- README's "Auto-deploy" section is rewritten to describe the
  curl-release-asset-then-`docker load` flow instead of `git pull` + rebuild.
- A `deploy.sh.example` is added to the repo (tracked in git, following the
  existing `.env.prod.example` / `config.prod.example.ini` pattern) purely as
  a reference for what `deploy.sh` should look like — the live `deploy.sh` on
  the VPS already exists and is maintained by hand, not copied from this file
  automatically.

### 5. `deploy.sh.example` (reference only; VPS's real `deploy.sh` is separate)

```bash
#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:?usage: deploy.sh vX.Y.Z}"
REPO="HEROgold/FactorioServerManager"

for service in backend frontend; do
  curl -fL "https://github.com/${REPO}/releases/download/${VERSION}/fsm-${service}-${VERSION}.tar.gz" \
    | gunzip | docker load
done

sed -i "s/^FSM_VERSION=.*/FSM_VERSION=${VERSION#v}/" .env
docker compose -f docker-compose.prod.yml --env-file .env up -d
docker image prune -f
docker compose -f docker-compose.prod.yml ps
```

### 6. Error handling / rollback

- `curl -f` fails the script (and the SSH step, and the job) on a bad or
  missing download — no partial deploy from a half-fetched image.
- Previous version's image tag is left in place (`docker image prune -f` only
  removes dangling/untagged layers, never a tagged image) — rollback is a
  manual `./deploy.sh v<previous-version>` re-run, which re-downloads that
  version's assets (release assets are immutable, so this is always safe) and
  re-tags/restarts.
- The smoke-test step in `deploy.yml` is unchanged: if it fails, the workflow
  goes red but the new container is already running (no auto-rollback) —
  matches today's behavior, which has none either.

### 7. Remove prod environment details from the repo

The repo should assume only `docker-compose.yml` (dev). All prod-specific
config and docs move out (VPS-only, hand-maintained, consistent with §2's
`deploy.sh` precedent):

- **Delete from git**: `docker-compose.prod.yml`, `.env.prod.example`,
  `config.prod.example.ini`, `scripts/setup-host.sh`. These become VPS-only
  files maintained by hand, like `deploy.sh` already is.
- **README.md**: remove the entire "Production deployment" section (current
  lines ~10-189: "How it fits together" through "Notes / hardening").
  Replace with a short pointer, e.g. "Production deployment is documented
  and maintained separately (not in this repo)." The rest of the README
  (local dev, architecture notes pointer to HANDOFF.md) is untouched.
- **HANDOFF.md**: remove §5c ("Local Kubernetes") and §6 ("REAL deployment
  (Kubernetes) — TODO, scaffold below"), plus the related open question in
  §8 ("K8s vs Docker for server spawning"). This is stale, unimplemented
  planning for a deploy path that doesn't match the actual Compose+Traefik
  setup and isn't referenced elsewhere.
- **`deploy.yml` smoke test**: replace the hardcoded
  `https://factorio.herogold.nl/` with a repo variable, e.g.
  `${{ vars.PROD_SMOKE_URL }}`, set once in GitHub repo settings. The
  workflow YAML no longer names the domain.

Net effect: the only prod-environment artifacts left in git are the CI
workflows themselves (`release.yml`, `deploy.yml`) and `deploy.sh.example`
as a reference — no compose file, no example configs, no host script, no
hostnames, no prod walkthrough.

## Out of scope

- Multi-arch images (VPS is assumed linux/amd64 only, matching today).
- Pushing to a container registry (GHCR etc.) — explicitly using release
  assets instead, per requirements.
- Automating the one-time copy of `deploy.sh`/`docker-compose.prod.yml`/etc.
  to the VPS — remains a manual, infrequent step.
- Auto-rollback on smoke-test failure.

## Testing plan

- `release.yml`: verify the build+save+attach steps locally is not practical
  (no VPS in CI); validate by dry-running `docker buildx build` +
  `docker save` + `gzip` locally against the current Dockerfiles, and by a
  real `workflow_dispatch` run against a throwaway tag once implemented.
- `deploy.yml`: exercised end-to-end on the next real release once the VPS's
  `deploy.sh` and `docker-compose.prod.yml` are updated by hand to match §3
  and §5's logic (outside this repo's control, done manually by the
  maintainer). `docker compose -f docker-compose.prod.yml config` on the VPS
  confirms it still parses after switching to `image:` refs.
- §7 removals: confirm nothing in the repo still references the deleted
  files (`grep -r` for `docker-compose.prod.yml`, `setup-host.sh`,
  `config.prod.example.ini`, `.env.prod.example`, `factorio.herogold.nl`
  after the change).
