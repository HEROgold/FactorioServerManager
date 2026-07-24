# FactorioServerManager (FSM)

A web app to create, start/stop, and manage headless Factorio servers, their mods,
and settings. FastAPI backend + React (Bun) SPA. The backend spawns each Factorio
server as a container on the host Docker daemon.

- Local development and architecture notes: see [HANDOFF.md](HANDOFF.md).
- Production deployment: see below.

## Production deployment

FSM runs as a Docker Compose stack behind an **existing** Traefik reverse proxy and
is reachable at `https://<subdomain>.<your-domain>`.

### How it fits together

- **Traefik → frontend only.** Traefik routes your hostname to the Bun frontend
  (`:3000`). The frontend serves the SPA and proxies `/api/*` to the backend over an
  internal Docker network, so the backend is never exposed and there is no CORS to
  configure (single origin).
- **Backend → host Docker.** The backend spawns each Factorio server as a sibling
  container on the host. In production it reaches the daemon through a
  least-privilege `docker-socket-proxy` (only container/image operations are
  allowed) rather than mounting the raw socket, so a backend compromise cannot run
  arbitrary Docker API calls.
- **Game traffic bypasses Traefik.** Players connect over **UDP** directly to the
  host's public IP; Traefik only handles HTTP(S).

### Requirements

- A Linux host with Docker + Docker Compose.
- An existing Traefik reverse proxy running on the host (any stack), attached to a
  known Docker network. Note its network name and its entrypoint / cert-resolver
  names — you will reference them below.
- A DNS record pointing your chosen hostname (`<subdomain>.<your-domain>`) at the
  host's public IP.

### One-time host setup

Clone the repo on the host (the default deploy location is `$HOME/FactorioServerManager`;
override with the `FSM_DIR` env var). Run all commands from the repo directory.

```sh
git clone <repo-url> FactorioServerManager
cd FactorioServerManager
```

**1. Create the persistent data directories and the service user.**
The backend passes these paths to the host Docker daemon verbatim (to bind-mount
into the Factorio containers it spawns), so the host and container paths **must be
identical** — do not relocate them. Run the bootstrap script, which creates the
`fsm` service user (uid/gid `10001`), provisions the data dirs, and gives them to
that user (the id the backend runs as). It is idempotent — safe to re-run.

```sh
sudo ./scripts/setup-host.sh
# To use a different id, keep it consistent everywhere (script, .env, build args):
#   FSM_UID=1500 FSM_GID=1500 sudo -E ./scripts/setup-host.sh
```

> Prefer a nicer host path than `/app`? Make the data root configurable in
> [src/api/constants.py](src/api/constants.py) (e.g. an `FSM_DATA_DIR` env var used
> for the servers/saves/downloads dirs and the DB), then bind that path to itself
> in `docker-compose.prod.yml`. The identical host:container path is the only hard
> requirement.

**2. Configure environment and app config.**

```sh
cp .env.prod.example .env
cp config.prod.example.ini config.ini
# confkit rewrites config.ini in place at startup, so the service user must own
# it too. Re-running the setup script picks it up now that it exists:
sudo ./scripts/setup-host.sh
```

Edit `.env`:

- `FSM_UID` / `FSM_GID` — the service uid/gid (default `10001`). Only change if the
  host reserves that id; if you do, pass the same values to `setup-host.sh` above.

- `SUBDOMAIN`, `DOMAIN_NAME` — together form the public hostname.
- `TRAEFIK_NETWORK` — the existing Traefik Docker network (`docker network ls`).
- `FSM_SECRET_KEY`, `FSM_TOKEN_KEY` — generate once and keep stable:

  ```sh
  python3 -c "import secrets;print(secrets.token_hex(64))"                       # FSM_SECRET_KEY
  python3 -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"  # FSM_TOKEN_KEY
  ```

Edit `config.ini`: set `public_ip` to the host's public IP (the address players use
to connect — not `127.0.0.1`).

**3. Match your Traefik's routing names.** In `docker-compose.prod.yml`, set the
frontend's Traefik labels to your proxy's actual **entrypoint** and **cert-resolver**
names (e.g. `entrypoints=web,websecure`, `tls.certresolver=<your-resolver>`). Compare
against another service already routed by the same Traefik.

**4. Open the Factorio game-server UDP port range on the host firewall** (players
connect here; keep RCON — TCP 27015+ — closed to the internet):

```sh
sudo ufw allow 61616:65565/udp   # only if ufw is enabled
```

**5. Launch:**

```sh
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

Traefik obtains a certificate for the hostname on the first request. If you were
running the plain `docker-compose.yml` (direct ports, no proxy), stop it first with
`docker compose down`.

### Auto-deploy (optional: GitHub Actions + Tailscale SSH)

[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) runs on push to
`main`: the runner joins your tailnet as an ephemeral `tag:ci` node and runs
[`deploy.sh`](deploy.sh) on the host over Tailscale SSH (`git pull` + rebuild). This
keeps the host with no public SSH port.

Configure once in the GitHub repo:

- **Secrets:** `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET` — a Tailscale OAuth client
  (tag `tag:ci`).
- **Variables:** `DEPLOY_HOST` (host's MagicDNS name), `DEPLOY_USER` (SSH user).

On the host / tailnet:

- Enable Tailscale SSH: `sudo tailscale up --ssh`.
- Add a tailnet ACL rule granting `tag:ci` SSH to the host as `DEPLOY_USER`, e.g.:

  ```jsonc
  "ssh": [
    { "action": "accept", "src": ["tag:ci"], "dst": ["tag:server"], "users": ["<deploy-user>"] }
  ]
  ```

If you prefer not to enable Tailscale SSH, swap the deploy step for key-based SSH
over the tailnet (`appleboy/ssh-action` with `host: <tailscale-ip>` and an
`SSH_PRIVATE_KEY` secret whose public key is in the host's `authorized_keys`).

If the repo is not at `$HOME/FactorioServerManager` on the host, set `FSM_DIR`
accordingly (in `deploy.sh` or the environment).

### Updating manually

```sh
ssh <deploy-user>@<host> 'bash ~/FactorioServerManager/deploy.sh'
```

### Notes / hardening

- `.env` and `config.ini` hold secrets — keep them gitignored; never commit them.
- **`FSM_SECRET_KEY` is required in production.** The backend refuses to start
  without a strong session secret rather than signing forgeable sessions with a
  default key. Generate one (see step above) and keep it stable.
- **Lock down who can log in.** By default any Factorio account that authenticates
  is admitted and gets full server-management rights. Set `auth_allowed_emails`
  (comma-separated) in `config.ini` to restrict the manager to known operators.
- **RCON** is published on `rcon_bind_host` (loopback by default), so the console
  port is not exposed publicly. When the backend runs in a container, set both
  `rcon_bind_host` and `rcon_host` to the Docker bridge gateway (e.g. `172.17.0.1`):
  RCON then stays off the public internet while the backend can still reach it.
- **Sentry** is disabled unless you set `SENTRY_DSN` (no DSN is baked into the
  image).
- **Non-root backend (root-entrypoint → gosu drop).** The container starts as root
  *only* so [`docker-entrypoint.sh`](docker-entrypoint.sh) can `chown` the managed
  data under `/app/src/api` to `FSM_UID:FSM_GID` (default `10001`), reconciling
  ownership of files the Factorio containers or older versions left behind. It then
  `exec`s the app as that unprivileged user via `gosu`, so the running process is
  never root. Capabilities are dropped to `ALL` and only the minimal set for that
  step is added back (`CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETUID`, `SETGID`);
  `no-new-privileges` is *not* set because it would block the `gosu` privilege drop.
  The Factorio containers the backend spawns are tagged with the same `PUID/PGID`,
  so all data ends up owned by one id. To use a different id, set `FSM_UID`/`FSM_GID`
  in `.env` (they drive the build args) and pass the same values to `setup-host.sh`.
- **Recovering a server that won't delete (legacy directories).** A directory whose
  files are owned by root or Factorio's default uid `845` (created before this
  ownership model) can make `DELETE` fail with `PermissionError` and leave the
  server showing in the UI. Fix: redeploy and restart the stack — the entrypoint
  re-`chown`s `/app/src/api` on startup, after which the delete succeeds. No manual
  `chown` needed.
- **Docker access is proxied.** The backend reaches the daemon only through the
  `docker-socket-proxy` (container/image ops), so it needs no `docker` group
  membership and never touches the raw socket.
- Open only the Factorio game-server **UDP** range on the host firewall; keep RCON
  (TCP) closed to the internet.
