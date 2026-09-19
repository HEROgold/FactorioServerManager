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

1. **Labels**: `Major`, `Minor`, `Patch` already created on this repo (also
   self-created by `herogold/bump-by-label` on first run if ever missing).
2. **Two GitHub Environments** (Settings -> Environments):
   - `release` — no protection rules needed; just scopes the Sentry
     release-creation secrets below to `release.yml`'s job.
   - `production` — **add yourself as a required reviewer**. This is the
     approval gate in `deploy.yml` — do not skip it, even though it's a
     solo project (see the pipeline design doc in Linear: HEROgold /
     "DevOps Pipeline Experiment").
3. **Environment secrets**:
   - On `release`: `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT` — an
     org-level auth token scoped to release creation (separate from the
     app's own `SENTRY_DSN`, which is already wired in `src/api/main.py`).
   - On `production`: `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_CLIENT_SECRET` — a Tailscale
     OAuth client (Tailscale admin console -> Settings -> OAuth clients)
     scoped to a tag (e.g. `tag:ci`) with ACL access to the production host;
     `PROD_HOST` (`ubuntu-4gb-hel1-1`), `PROD_SSH_USER` (`herogold`), and
     `PROD_SSH_KEY` — a dedicated deploy keypair (don't reuse a personal
     key); add the public half to `~herogold/.ssh/authorized_keys`.
4. **No test suite exists yet.** `release.yml` currently gates only on
   `Skylos Analysis`; its `REQUIRED_WORKFLOWS` list is written to be extended
   with a test workflow's name the moment one exists — no other changes
   needed to wire it in.

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

Discovered during read-only investigation over Tailscale SSH:

1. **`traefik` was crash-looping in production — fixed.** Logs showed
   `failed to decode configuration from flags: field not found, node: --api`
   repeating every ~60s. Root cause: the running container's `Cmd` had every
   flag prefixed with a literal `"- "` (e.g. `"- --api.insecure=true"`),
   even though `/home/herogold/n8n/docker-compose.yml` itself defines
   `command:` as a correct YAML list — the live container just wasn't
   created from that file as-is. Fixed by running
   `docker compose up -d --force-recreate traefik` from that directory,
   which now serves on 80/443 correctly as `n8n-traefik-1`. One remaining
   cleanup: the old, no-longer-port-bound container literally named
   `traefik` (no compose project label — orphaned) is still crash-looping
   in the background; `docker rm -f traefik` clears the log noise.
2. **The server's `~/FactorioServerManager` checkout is badly stale** (parked
   for later, not blocking this PR): `git diff main origin/main` shows 183
   files / ~11k lines different — the whole
   `docker-socket-proxy` security architecture, `Dockerfile.backend`,
   `docker-compose.prod.yml`, and most of the current frontend don't exist in
   that checkout. The 8 running `factorioservermanager-*` containers were
   built from that old state ~2 months ago; `deploy.sh`'s `git pull --ff-only`
   will fail outright (branches have diverged, not just fallen behind).
   **This needs a deliberate, watched first upgrade** (not a blind
   `git reset --hard origin/main` inside an automated job) before `deploy.yml`
   can run successfully — recommend doing that upgrade by hand once, then
   letting the pipeline take over from a known-good state.
