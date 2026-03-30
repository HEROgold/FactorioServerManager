FROM oven/bun:latest

WORKDIR /app

# Copy package files and install dependencies
COPY package.json bunfig.toml ./
COPY . .

RUN bun install

EXPOSE 3000

CMD ["bun", "run", "dev", "--host", "0.0.0.0"]
