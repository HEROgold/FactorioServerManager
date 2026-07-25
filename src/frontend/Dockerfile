# Pin the Bun major so builds are reproducible (never `latest`).
FROM oven/bun:1

WORKDIR /app

# Copy only the manifests + lockfile first, then install. This layer stays cached
# across source changes, so `bun install` only re-runs when dependencies change.
COPY package.json bunfig.toml bun.lock ./
RUN bun install --frozen-lockfile

# Now bring in the application source. Copy only what the runtime server
# (`bun run start` -> `bun src/index.ts`) needs — the manifests are already in
# the layer above, and .dockerignore scopes the context. All assets (index.html,
# index.css, favicon.svg, ...) live under src/.
COPY src ./src
COPY tsconfig.json ./

# Drop to the unprivileged `bun` user baked into the base image.
USER bun

EXPOSE 3000

# Baked default healthcheck (compose healthchecks still override per-service).
# bun is on PATH in both dev and prod, so probe the server with it — no extra tools.
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD ["bun", "-e", "const r = await fetch('http://localhost:3000/'); process.exit(r.ok ? 0 : 1)"]

# Default to the production server (no HMR, no browser-console echo). Dev runs
# override this with `bun run dev` explicitly (see docker-compose.yml).
CMD ["bun", "run", "start"]
