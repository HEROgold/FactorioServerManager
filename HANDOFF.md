# FactorioServerManager — Migration & Work Handoff

_Last updated: 2026-06-26. Branch: `React`. This document captures everything done so far and
everything still outstanding, so work can resume cleanly. Read this top-to-bottom before continuing._

## SESSION 2 UPDATE (supersedes parts of §3 below)

Completed since the doc was first written:
- **httpx → httpxyz (HTTP/2)** — `factorio_interface.py` + `version.py` use `httpxyz.AsyncClient(http2=True)`;
  mod-portal errors are `httpxyz.HTTPError`; `aiohttp` removed; `httpxyz`+`h2` added. Live-tested.
- **Secure logging** (§3a) — DONE: Sentry `send_default_pii=False` + `before_send=scrub_event`
  ([logging_security.py](src/api/logging_security.py)); httpxyz loggers forced to WARNING (mod-download URL
  carries `?token=`); redacting filter on root; safe `Base.__repr__`; frontend `sendDefaultPii: false`.
- **Server-spawning backends** (was §6 caveat) — RESOLVED: common `ServerBackend` Protocol +
  `ServerSpec` ([backends/base.py](src/api/_types/backends/base.py)), `DockerBackend` and new `K8sBackend`
  (Deployment+Service+PVC), selected by `BackendKind` enum + Confkit `AppConfig.SERVER_BACKEND`
  (`docker`|`kubernetes`), lazy factory `get_backend()`. `data.py` delegates; app no longer needs Docker at
  import. `kubernetes` added to deps.
- **Strict typing** (§3b) — DONE: `[tool.ty]` + `[tool.pyrefly]` strict config in `pyproject.toml`;
  `ty check` = **all pass**, `pyrefly check` = **0 errors**. ty/pyrefly/types-docker added as dev deps.
- **Settings → Factorio 2.1** (§3d) — DONE via the chosen approach (**Confkit + a custom JSON parser**):
  [json_parser.py](src/api/_types/json_parser.py) implements the `ConfkitParser` protocol (stdlib json,
  nested dot-section support). [settings.py](src/api/_types/settings.py) rewritten to the exact 2.1 schema
  (ServerSettings/MapGenerationSettings/MapSettings incl. new `auto_pause_when_players_connect`,
  segment-size quartet, `max_heartbeats_per_second`, `asteroids`, hyphenated autoplace keys). Round-trip
  verified against the real `factoriotools/factorio:2.1.8` example files. `Server.create()` now writes the
  real `server-settings.json` / `map-settings.json` / `map-gen-settings.json`. `port` moved off
  ServerSettings onto `Server` (it's a launch param, not a 2.1 setting).

Also DONE (frontend):
- **Settings form → 2.1 shape** — [Settings.tsx](src/frontend/src/forms/Settings.tsx) rewritten to the nested
  `visibility` + 2.1 field set (dropped steam/whitelist/authserver-bans/admins; added segment/heartbeat/
  autosave-slots/auto_pause_when_players_connect). Submits the flat `visibility_public`/`visibility_lan` the
  PATCH endpoint expects.
- **Custom-tags SKILL.md** (§3c) — applied. New barebones, style-free tags added under
  `src/frontend/src/components/tags/` (Button, Select, Section, Pre, Code, Fieldset) each with the skill's
  "TODO: port CSS" note; authored pages (StatusBox, Logs, Rcon, mods/*, Install, Settings) now use the
  existing/new tags (Input, Select, Button, ButtonGhost, Card, Placeholder, Section, Pre, Code, Fieldset)
  instead of raw elements. `tsc` clean, bundle OK.

NOTHING outstanding from §3 remains. The rest of this document (§4 schema, §5 local run, §6 K8s deploy minus
the resolved server-spawning caveat) is still valid. Remaining big-picture item: write the actual `k8s/`
manifests for a real deploy (§6) when you're ready.

---

---

## 1. Big picture

The project was migrated from a monolithic Flask app (`src/fsm`) to:
- **`src/api`** — FastAPI backend (self-contained; `src/fsm` is deleted).
- **`src/frontend`** — React 19 + Bun SPA, talks to the API (Bun dev server proxies `/api/*`).

Entry points:
- Backend: `python -m api.main` (or `uvicorn api.main:app`), from `src/` with `PYTHONPATH=src`.
- Frontend dev: `cd src/frontend && bun dev` (proxies `/api` → `API_TARGET`, default `http://127.0.0.1:8000`).

---

## 2. DONE (verified)

1. **`src/fsm` → `src/api` + `src/frontend` migration** — complete. Domain code lives in
   `src/api/_types/`, `src/api/security.py`, `src/api/constants.py`, `src/api/utils.py`.
   20 API routes register; backend imports clean; frontend `tsc` passes and bundles.
2. **Dependency fixes**: replaced defunct `jose` with `python-jose`; added `email-validator`.
   Removed Flask deps. `uv.lock` refreshed.
3. **Factorio API currency**:
   - Auth `api_version` `4 → 6` ([constants.py](src/api/constants.py)); robust response parsing for
     `{token,username}` / email-auth error / legacy list in
     [factorio_interface.py](src/api/_types/factorio_interface.py); fixed login check ordering in
     [login.py](src/api/routers/login.py).
   - Mod portal **`q` search no longer works server-side** → now fetches full list (`page_size=max`)
     and filters client-side in `ModsInterface.search`.
4. **HTTP client migration aiohttp → httpxyz (HTTP/2)** — DONE & live-tested.
   - `httpxyz.AsyncClient(http2=True, ...)` in [factorio_interface.py](src/api/_types/factorio_interface.py)
     and [version.py](src/api/routers/version.py); exceptions are `httpxyz.HTTPError` in
     [mods.py](src/api/routers/mods.py). Added `httpxyz` + `h2` to `pyproject.toml`; removed `aiohttp`.
   - Verified: `/versions` scrape works over HTTP/2 (117 versions; latest is **2.1.8**).
   - NOTE: `httpx`/`httpcore` were uninstalled; we use **`httpxyz`** (pulled via `herogold`). For test
     clients use `httpxyz` directly — FastAPI's `TestClient` requires the literal `httpx` module and
     will not work.
5. **Factorio 2.1 settings ground-truth captured** — booted `factoriotools/factorio:2.1.8`, generated
   real config, extracted the canonical example files. See §4 for the data (this is the spec to align to).

---

## 3. OUTSTANDING WORK (resume here)

### 3a. Secure logging for sensitive data  — IN PROGRESS, not yet applied
The user flagged `logs/_global.log` and asked to ensure tokens/passwords/PII are never logged.
**Concrete fixes required (none applied yet):**
1. **Sentry PII (backend)** — [main.py](src/api/main.py) calls `sentry_sdk.init(send_default_pii=True)`.
   This ships request headers + **cookies (the `fsm_session` JWT)** to Sentry. Set
   `send_default_pii=False` and add a `before_send` hook that scrubs `Cookie`/`Authorization` headers
   and any `token`/`password`/`factorio_token` fields.
2. **Sentry PII (frontend)** — [frontend.tsx](src/frontend/src/frontend.tsx) sets `sendDefaultPii: true`.
   Set to `false` (login password could land in breadcrumbs/replays).
3. **httpxyz request-URL logging** — httpxyz logs `HTTP Request: GET <url>` at INFO. The mod download
   call passes credentials as **query params** (`?username=...&token=...`) in
   `ModsInterface.download_release`, so the token would be written to logs. Fix: set
   `logging.getLogger("httpxyz").setLevel(logging.WARNING)` at startup (in `main.py`), and/or redact.
4. **Model `__repr__` leak** — `Base.__repr__` in [database.py](src/api/_types/database.py) returns
   `str(self.__dict__)`, which for `User` includes the **password hash** and
   `factorio_token_encrypted`. Add a safe `__repr__` that omits `password`, `factorio_token_encrypted`.
   Also confirm `factorio_token` (decrypted property) is never passed to a logger.
5. Add a redacting `logging.Filter` (covers `token`, `password`, `api-login` bodies) attached to the
   root/herogold handler as defense-in-depth.

### 3b. Strict typing: `ty` + `pyrefly` — NOT STARTED
User wants **all** `ty` and `pyrefly` issues fixed at the **strictest** settings; do not ignore any.
1. `pyrefly` likely needs a config — add `[tool.pyrefly]` to `pyproject.toml` (or `pyrefly.toml`) with
   strict settings, project root `src`.
2. Run `ty check src/api` and `pyrefly check src/api`; fix every diagnostic.
   - Known recurring issue: many handlers/functions return bare `-> dict`. Replace with precise types
     (`dict[str, Any]`, `TypedDict`, or Pydantic response models). The settings rework (§3d) should use
     typed models too.
   - The `bs4` `tag.get("value")` in `factorio_interface.py` returns `str | AttributeValueList | None`;
     narrow it before constructing `CSRFToken`.
3. Frontend: keep `tsc --noEmit --ignoreDeprecations 6.0` green (a `declare module "*.css";` shim was
   added to `bun-env.d.ts`). `typescript` is a devDependency now.

### 3c. Frontend custom-tags skill ([skills/agent-customization/SKILL.md](skills/agent-customization/SKILL.md)) — NOT STARTED
The skill says: when building UI, **prefer existing custom tags** in
`src/frontend/src/components/tags/` (Input, ButtonGhost, Card, Chip, Pill, Placeholder, SearchInput,
Toast, VersionPill, InstalledCard); if a needed semantic tag is missing, create a **barebones,
style-free** `tags/<TagName>.tsx` that maps to a semantic element and forwards props/children.
**Action:** audit the pages I added/edited (Logs, Rcon, mods/*, Settings, Install, Overview, Manage)
which use raw `<button>/<input>/<select>/<table>/<section>/<pre>`, and:
- Replace raw inputs with the existing `Input`/`SearchInput` tags.
- Use `Placeholder` for empty states (mods search/detail placeholders already match its intent).
- Create minimal style-free tags for repeated primitives (e.g. `Button`, `Section`, `Pre`, `Table`)
  per the SKILL template, then use them. Add the follow-up TODO comment to port CSS later (per skill §5).

### 3d. ServerSettings/Map settings rework for 2.1 — BLOCKED ON A DECISION (must ask user)
Our settings models in [settings.py](src/api/_types/settings.py) are **significantly out of date** with
Factorio 2.1 (see §4 for exact diffs). Before rewriting, the user asked to **research two approaches and
ask which to use**:
- **Option A — Confkit with a JSON parser.** Already a project dep; consistent with `AppConfig`. Caveat
  (user-noted): confkit requires specifying the file per config, which is awkward for **per-server**
  settings files (each server has its own `server-settings.json`). Confkit is oriented to a single
  app-wide config file, not many instance files. Validation is weaker.
- **Option B — Pydantic models for the settings files.** Already a dep (FastAPI). Strong **validation**
  + great typing (aligns with §3b strict-typing goal), `model_validate_json` / `model_dump_json` per
  file path, easy per-server instances. Caveat: another modeling layer beside confkit.
- **Recommendation to surface:** Pydantic (Option B) — per-file/per-instance fit + validation + typing.
  **STILL ASK THE USER** before implementing (this was an explicit instruction). Use `AskUserQuestion`.

After the decision: rewrite `ServerSettings`, `MapSettings`, `MapGenerationSettings` to match §4, make
`Server.create()` actually **write a real `server-settings.json`** (currently it writes
`custom-settings.json`, which Factorio does NOT read), and update the React Settings form
([Settings.tsx](src/frontend/src/forms/Settings.tsx)) to the corrected fields (drop steam/whitelist/
authserver-bans/admins; add the new 2.1 fields). Keep all examples valid.

---

## 4. Factorio 2.1.8 settings — ground truth (extracted from `factoriotools/factorio:2.1.8`)

### server-settings.json (canonical top-level keys)
`name`, `description`, `tags` (array), `max_players` (0=unlimited), `visibility` `{public, lan}` (NO
`steam`), `username`, `password`, `token`, `game_password`, `require_user_verification`,
`max_upload_in_kilobytes_per_second` (0=unlimited), `max_upload_slots` (5),
`minimum_latency_in_ticks` (0), `max_heartbeats_per_second` (60, range 6–240),
`ignore_player_limit_for_returning_players`, `allow_commands` (`true`/`false`/`admins-only`),
`autosave_interval` (minutes, 10), `autosave_slots` (5), `afk_autokick_interval` (0=never),
`auto_pause`, `auto_pause_when_players_connect` (false, **new**), `only_admins_can_pause_the_game`,
`autosave_only_on_server`, `non_blocking_saving`, `minimum_segment_size` (25),
`minimum_segment_size_peer_count` (20), `maximum_segment_size` (100),
`maximum_segment_size_peer_count` (10).

**Our `ServerSettings` diffs to fix:**
- REMOVE (not real server-settings fields): `visibility_steam`, `use_authserver_bans`, `whitelist`
  (separate `server-whitelist.json`), `admins` (separate `server-adminlist.json`),
  `ignore_limit_returning` (duplicate/misnamed).
- ADD: `username`, `password`, `token`, `minimum_latency_in_ticks`, `max_heartbeats_per_second`,
  `autosave_slots`, `auto_pause_when_players_connect`, `minimum_segment_size`,
  `minimum_segment_size_peer_count`, `maximum_segment_size`, `maximum_segment_size_peer_count`.
- `tags` should be a **list[str]**, not a comma string. `port` is a launch param, not a server setting —
  keep it as our own metadata, separate from the JSON we write for Factorio.

### map-gen-settings.json
`width`, `height`, `starting_area`, `peaceful_mode`, `autoplace_controls` (`coal`, `stone`,
`copper-ore`, `iron-ore`, `uranium-ore`, `crude-oil`, `water` {freq,size only}, `trees`, `enemy-base`),
`cliff_settings` {`name`, `cliff_elevation_0`, `cliff_elevation_interval`, `richness`},
`property_expression_names` {`control:moisture:frequency`, `control:moisture:bias`,
`control:aux:frequency`, `control:aux:bias`}, `starting_points` [{x,y}], `seed`.
**Our `MapGenerationSettings` diffs:** has bogus top-level `terrain_segmentation` and `water`; autoplace
keys use underscores and omit `water`. Keys must be **hyphenated** to match Factorio.

### map-settings.json
`difficulty_settings` {`technology_price_multiplier`, `spoil_time_modifier`} — our `DifficultySettings`
still has 2.0-removed fields (`recipe_difficulty`, `technology_difficulty`, `research_queue_setting`).
`pollution`, `enemy_evolution`, `enemy_expansion` (adds `min_expansion_distance`,
`evolution_group_size_factor`), `unit_group`, `steering`, `path_finder`, `max_failed_behavior_count`.

Reference copies saved to scratchpad: `…/scratchpad/factorio-2.1/{server-settings,map-gen-settings,map-settings,server-whitelist}.example.json`.
(Re-extract anytime: `docker run --rm --entrypoint /bin/cat factoriotools/factorio:2.1.8 /opt/factorio/data/server-settings.example.json`.)

---

## 5. Run & test LOCALLY first

### 5a. Quickest: two processes
```sh
# Backend (Docker must be running; it manages Factorio containers)
cd src && PYTHONPATH=$PWD python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
# Frontend (separate shell) — proxies /api -> 127.0.0.1:8000
cd src/frontend && bun install && bun dev   # serves on :3000
```
Open http://localhost:3000. Login needs real Factorio.com credentials. Create/start/stop a server needs
Docker. Smoke checks: `GET /api/me` → 401 unauthenticated; `GET /api/versions` → list incl. 2.1.x.

### 5b. docker compose (closer to prod)
```sh
docker compose build && docker compose up
# backend :8000, frontend :3000. Healthcheck hits /openapi.json.
```
Note: server data persists under `src/api/servers` (bind-mounted; gitignored).

### 5c. Local Kubernetes (test the manifests before real deploy)
Use a local cluster (Docker Desktop's K8s, kind, or minikube). Example smoke deploy (the user's example):
```sh
kubectl create deployment my-app --image=nginx   # sanity-check the cluster works
kubectl delete deployment my-app
```
Then build & load our images into the local cluster and apply our manifests (see §6 — manifests are
TODO). With kind: `kind load docker-image fsm-backend:dev fsm-frontend:dev`. With Docker Desktop K8s the
local image is already available (set `imagePullPolicy: IfNotPresent`).

---

## 6. REAL deployment (Kubernetes) — TODO, scaffold below

Manifests are **not yet written**. Create `k8s/` with:
- `backend-deployment.yaml` + `backend-service.yaml` (port 8000). The backend talks to the Docker daemon
  today (`docker.from_env()`), which is a problem in K8s — see caveat below.
- `frontend-deployment.yaml` + `frontend-service.yaml` (port 3000, env `API_TARGET` → backend service
  DNS, e.g. `http://fsm-backend:8000`).
- `ingress.yaml` routing `/api` → backend, `/` → frontend (or let the frontend proxy `/api`).
- `secret.yaml` for `FSM_SECRET_KEY`, `FSM_TOKEN_KEY`, Sentry DSN (do **not** bake into images).
- `pvc.yaml` for server data (replaces the `src/api/servers` bind mount).

Rough flow:
```sh
docker build -f Dockerfile.backend -t <registry>/fsm-backend:<tag> .
docker build -f src/frontend/Dockerfile -t <registry>/fsm-frontend:<tag> src/frontend
docker push <registry>/fsm-backend:<tag> && docker push <registry>/fsm-frontend:<tag>
kubectl apply -f k8s/
kubectl rollout status deployment/fsm-backend
```

**MAJOR caveat to resolve before real deploy:** the backend currently spawns Factorio servers by talking
to the **local Docker daemon** ([data.py](src/api/_types/data.py) `docker.from_env()`). In Kubernetes
there is no local Docker daemon. Options: (a) run the backend with access to a Docker/containerd socket
(not recommended), (b) refactor `Server.create/start/stop` to create **Kubernetes Jobs/Deployments**
(via the k8s API) instead of Docker containers, or (c) keep Docker-based deploy (compose/Swarm) instead
of K8s for the server-spawning component. This is a design decision the user must weigh in on.

---

## 7. Verification checklist (run after each chunk)
- Backend imports: `cd src && PYTHONPATH=$PWD python -c "import api.main"` (no errors).
- Routes: `python -c "import api.main as m; print(len(m.app.openapi()['paths']))"` → 20 (will grow with
  settings endpoints).
- Types: `ty check src/api` and `pyrefly check src/api` clean; `cd src/frontend && bunx tsc --noEmit --ignoreDeprecations 6.0` clean.
- No secrets in logs: grep `logs/` for any token/password substrings after a login + mod action.
- Frontend builds: `cd src/frontend && bun build ./src/index.html --outdir=dist`.

---

## 8. Open questions for the user
1. **Settings modeling**: Confkit-JSON vs Pydantic (recommend Pydantic). _Must ask before implementing §3d._
2. **K8s vs Docker for server spawning**: how should the backend launch Factorio servers in production
   (refactor to K8s API, or keep Docker)? Blocks §6.
