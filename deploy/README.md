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

Everything runs as `herogold`. The stack is `docker-compose.yml` in
`~/FactorioServerManager`, behind the existing Traefik (see the main README's
"Production deployment").

```text
~/FactorioServerManager/        this app
├── docker-compose.yml          docker-compose.yml from the deployed release
├── deploy-fsm.sh               deploy/deploy-fsm.sh (executable)
├── .env                        .env.example, filled in with the production values
├── config.ini                  config.example.ini, filled in
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

2. Compose file. Copy `docker-compose.yml` from the release you deploy, and delete the old
   `docker-compose.prod.yml`. Then add the variables that are new in `.env.example`
   (`FSM_BACKEND_IMAGE`, `FSM_FRONTEND_IMAGE`, `FSM_FRONTEND_SCRIPT`, `FSM_FRONTEND_PORT`,
   `TRAEFIK_EXTERNAL`) to `.env` with their production values. Copy the compose file again when
   it changes. The deploy doesn't update it either, and compose fails on a missing variable.

3. Registry access. After the first release pushes the two GHCR packages, set each one to
   public in its package settings. The server then pulls them without a login.

4. Deploy verifier. It already runs for HEROgold/nota. Add `[apps.fsm]` from `deploy/verifier.toml` to
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

5. GitHub. The repository needs the `production` environment and the repository secret
   `DEPLOY_URL` set to `https://deploy.herogold.nl/hooks/fsm`.

Without a token, `curl -i -X POST https://deploy.herogold.nl/hooks/fsm` answers 401.

### Leftovers from the SSH deploy

The old deploy ran `~/FactorioServerManager/deploy.sh` over Tailscale SSH. Once a release has
deployed through the notifier, remove what it used:

- the untracked `deploy.sh` and `deploy.sh.copy` on the server (back up `config.ini~` first if
  it's still needed)
- the `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_CLIENT_SECRET`, `PROD_HOST`, `PROD_SSH_USER` and
  `PROD_SSH_KEY` secrets on the `production` environment
- the CI key in the server's `~/.ssh/authorized_keys`
- `tag:ci` in the tailnet policy, if nothing else uses it

## Deploying by hand

Pick the digests from the release run's `publish` job outputs, or from the package pages:

```sh
cd ~/FactorioServerManager
printf 'FSM_BACKEND_IMAGE=%s\nFSM_FRONTEND_IMAGE=%s\n' \
  ghcr.io/herogold/factorioservermanager-backend@sha256:… \
  ghcr.io/herogold/factorioservermanager-frontend@sha256:… > .env.deploy
docker compose --env-file .env --env-file .env.deploy \
  up -d --wait --pull missing --no-build
```

To roll back by hand, `mv .env.deploy.prev .env.deploy` and run the same `up`.

## Testing the script

`bash deploy/test-deploy-fsm.sh` runs `deploy-fsm.sh` against a fake `docker` in a scratch
directory.
