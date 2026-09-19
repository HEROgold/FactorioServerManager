# Deploy pipeline runbook

Pipeline: label a merged PR `Major`/`Minor`/`Patch` -> `bump-version-by-labels.yml`
opens a version-bump PR -> merging it -> `release.yml` (after `Skylos Analysis`
passes on `main`) tags a GitHub Release + Sentry release -> dispatches
`deploy.yml` -> **manual approval gate** (`production` environment) -> SSH
deploy over Tailscale -> smoke test against `https://factorio.herogold.nl/`.

FSM has no Alembic/DB-migration step (SQLite via SQLAlchemy, no migration
framework in use), so the deploy job skips straight from "container up" to
smoke test.

## One-time setup required before this pipeline can run

1. **Labels**: `Major`, `Minor`, `Patch` created on this repo (`gh label create`).
2. **GitHub Environment**: create `production` in Settings -> Environments,
   with yourself as a required reviewer. This is the approval gate — do not
   skip it, even though it's a solo project (see the pipeline design doc in
   Linear: HEROgold / "DevOps Pipeline Experiment").
3. **Repo secrets**:
   - `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT` — an org-level auth
     token scoped to release creation (separate from the app's own
     `SENTRY_DSN`, which is already wired in `src/api/main.py`).
   - `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET` — a Tailscale OAuth client
     (Tailscale admin console -> Settings -> OAuth clients) scoped to a tag
     (e.g. `tag:ci`) with ACL access to the production host.
   - `PROD_HOST` — the Tailscale hostname (`ubuntu-4gb-hel1-1`).
   - `PROD_SSH_USER` — `herogold`.
   - `PROD_SSH_KEY` — a dedicated deploy keypair (don't reuse a personal key);
     add the public half to `~herogold/.ssh/authorized_keys` on the server.

None of this goes through Vault yet — the design doc's Vault/Terraform/OIDC
phases are follow-up work once this simpler pipeline is proven out (see
"Known gaps" below).

## Known gaps / follow-up (not built yet)

- **No Vault, no Terraform.** Secrets are plain GitHub encrypted secrets for
  this first pass. Wiring OIDC->Vault and Terraform-managed infra is Phase 2+
  of the design doc — deliberately deferred until this baseline pipeline
  proves useful.
- **Single environment.** There's no separate staging container yet — this
  pipeline deploys straight to the one production FSM instance. The
  approval gate is the only safety net right now, standing in for the
  staging->production promotion step in the full design.
- **Rollback is manual.** `docker compose -f docker-compose.prod.yml up -d --build
  <previous-tag>` after `git checkout <previous-good-commit>` — no automation
  for this yet.

## Incidents found while investigating this task (2026-09-19)

Discovered during read-only investigation over Tailscale SSH — **not** fixed
by this PR, flagging for follow-up:

1. **`traefik` container is crash-looping in production right now.** Logs show:
   `failed to decode configuration from flags: field not found, node: --api`
   repeating every ~60s. Likely a bad/incompatible CLI flag after the
   `traefik:latest` image was pulled (floating tag). While Traefik is down,
   every subdomain it routes (n8n, factorio, dozzle, traefik-gui) is
   unreachable from outside the tailnet. **This blocks the smoke-test step
   above from ever passing** until fixed.
2. **The server's `~/FactorioServerManager` checkout is badly stale**: `git
   diff main origin/main` shows 183 files / ~11k lines different — the whole
   `docker-socket-proxy` security architecture, `Dockerfile.backend`,
   `docker-compose.prod.yml`, and most of the current frontend don't exist in
   that checkout. The 8 running `factorioservermanager-*` containers were
   built from that old state ~2 months ago; `deploy.sh`'s `git pull --ff-only`
   will fail outright (branches have diverged, not just fallen behind).
   **This needs a deliberate, watched first upgrade** (not a blind
   `git reset --hard origin/main` inside an automated job) before `deploy.yml`
   can run successfully — recommend doing that upgrade by hand once, then
   letting the pipeline take over from a known-good state.
