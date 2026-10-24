# Deploying FSM

A release deploys itself. When `release.yml` creates a new `v<version>` tag, it dispatches
`new-release-created`, and `.github/workflows/deploy.yml` then:

1. Builds both images from the tag and pushes them to GHCR, tagged `v<version>` and
   `sha-<commit>`:
   - `ghcr.io/herogold/factorioservermanager-backend` from `Dockerfile.backend`
   - `ghcr.io/herogold/factorioservermanager-frontend` from `src/frontend/Dockerfile`
2. Waits for the `production` environment's approval, then notifies the VPS through
   [deploy-notifier](https://github.com/HEROgold/deploy-notifier) at
   `https://deploy.herogold.nl/hooks/fsm`. The backend goes as `image` and the frontend as
   `extra.frontend_image`, both pinned by digest. The verifier runs `deploy-fsm.sh`, which pulls
   both images, writes `.env.deploy` and runs `docker compose up --wait --no-build`. If that
   fails, it puts the previous `.env.deploy` back and starts that instead.
3. Retries `https://factorio.herogold.nl/` until it answers 200.

The deploy never runs `git pull` and never builds on the server.

## On the VPS

Everything runs as `herogold`. The stack is `docker-compose.prod.yml` in
`~/FactorioServerManager`, behind the existing Traefik (see the main README's
"Production deployment").

```text
~/FactorioServerManager/        this app
├── docker-compose.prod.yml
├── deploy-fsm.sh               deploy/deploy-fsm.sh (executable)
├── .env                        .env.prod.example, filled in
├── config.ini                  config.prod.example.ini, filled in
├── .env.deploy                 written by deploy-fsm.sh: FSM_BACKEND_IMAGE, FSM_FRONTEND_IMAGE
└── .env.deploy.prev            the deploy before that, for rollback
~/deploy-notifier/verifier/     the deploy verifier, a container behind Traefik
├── config.toml                 includes deploy/verifier.toml's [apps.fsm]
└── compose.override.yml        mounts ~/FactorioServerManager at the same path
```

### One-time setup

1. Deploy script. The verifier runs it as uid 1000 with the docker group:

   ```sh
   cd ~/FactorioServerManager
   cp deploy/deploy-fsm.sh deploy-fsm.sh   # or copy it over from a checkout
   chmod 755 deploy-fsm.sh
   chown herogold:herogold deploy-fsm.sh
   ```

   Copy it again when `deploy/deploy-fsm.sh` changes. The deploy doesn't update it.

2. Registry access needs no setup. Both GHCR packages are public, so the pull needs no login.
   Make each package public once in its package settings after the first release pushes it.

3. Deploy verifier. It already runs for nota. Add `[apps.fsm]` from `deploy/verifier.toml` to
   `~/deploy-notifier/verifier/config.toml`, add this mount to `compose.override.yml`, and
   recreate the verifier:

   ```yaml
   services:
     verifier:
       volumes:
         - /home/herogold/FactorioServerManager:/home/herogold/FactorioServerManager
   ```

   The mount uses the same path inside and out, because the compose file's relative binds
   (`./config.ini`) resolve on the host daemon.

4. GitHub: the `production` environment and the repository variable `DEPLOY_URL`
   (`https://deploy.herogold.nl/hooks/fsm`).

Check it: `curl -i -X POST https://deploy.herogold.nl/hooks/fsm` answers 401 without a token.

## Deploying by hand

Pick the digests from the release run's `publish` job outputs, or from the package pages:

```sh
cd ~/FactorioServerManager
printf 'FSM_BACKEND_IMAGE=%s\nFSM_FRONTEND_IMAGE=%s\n' \
  ghcr.io/herogold/factorioservermanager-backend@sha256:… \
  ghcr.io/herogold/factorioservermanager-frontend@sha256:… > .env.deploy
docker compose -f docker-compose.prod.yml --env-file .env --env-file .env.deploy \
  up -d --wait --pull missing --no-build
```

To roll back by hand, `mv .env.deploy.prev .env.deploy` and run the same `up`.

## Testing the script

`bash deploy/test-deploy-fsm.sh` runs `deploy-fsm.sh` against a fake `docker` in a scratch
directory.
