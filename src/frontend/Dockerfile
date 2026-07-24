# Pin the Bun major so builds are reproducible (never `latest`).
FROM oven/bun:1

WORKDIR /app

# Copy only the manifests + lockfile first, then install. This layer stays cached
# across source changes, so `bun install` only re-runs when dependencies change.
COPY package.json bunfig.toml bun.lock ./
RUN bun install --frozen-lockfile

# Now bring in the application source.
COPY . .

# Drop to the unprivileged `bun` user baked into the base image.
USER bun

EXPOSE 3000

# Default to the production server (no HMR, no browser-console echo). Dev runs
# override this with `bun run dev` explicitly (see docker-compose.yml).
CMD ["bun", "run", "start"]
