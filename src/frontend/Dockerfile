FROM oven/bun:latest

WORKDIR /app

# Copy package files and install dependencies
COPY package.json bunfig.toml ./
COPY . .

RUN bun install

EXPOSE 3000

# Default to the production server (no HMR, no browser-console echo). Dev runs
# override this with `bun run dev` explicitly (see docker-compose.yml).
CMD ["bun", "run", "start"]
