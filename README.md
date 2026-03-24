# Factorio Server Manager

A modern web application for managing Factorio game servers with FastAPI backend and React frontend.

## Features

- **User Authentication**: Secure login using Factorio.com OAuth
- **Server Management**: Create, start, stop, restart, and delete Factorio servers
- **Mod Management**:
  - Search and browse mods from the Factorio mod portal
  - Batch installation of multiple mods at once
  - Enable/disable mods without uninstalling
  - View installed mods and their versions
- **Rate Limiting**: Cooldown periods for heavy operations to prevent server spam
- **Real-time Status**: Monitor server status and logs
- **Docker Integration**: All servers run in isolated Docker containers

## Architecture

### Backend (FastAPI)
- **Location**: `src/backend/`
- **Framework**: FastAPI with async support
- **Authentication**: JWT tokens + Factorio OAuth
- **Database**: SQLite with SQLAlchemy ORM
- **Rate Limiting**: In-memory rate limiter with operation cooldowns

### Frontend (React)
- **Location**: `src/frontend/`
- **Framework**: React 19 with TypeScript
- **Routing**: React Router DOM v7
- **Styling**: Tailwind CSS v4 + DaisyUI v5
- **Build Tool**: Bun
- **Form Validation**: Client-side validation with server-side enforcement

## Prerequisites

- Python 3.13+
- Bun (for frontend)
- Docker (for running Factorio servers)
- Factorio.com account

## Installation

### Backend Setup

1. Install Python dependencies:
```bash
uv sync
```

2. Run the FastAPI server:
```bash
# Development mode with auto-reload
cd src
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Frontend Setup

1. Install frontend dependencies:
```bash
cd src/frontend
bun install
```

2. Run the development server:
```bash
bun dev
```

The frontend will be available at `http://localhost:3000`

3. Build for production:
```bash
bun run build
```

## Configuration

### Environment Variables

Create a `.env` file in the project root or set environment variables:

```env
# Security (auto-generated if not provided)
FSM_SECRET_KEY=your-secret-key-here
FSM_TOKEN_KEY=your-encryption-key-here

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
SERVER_OPERATION_COOLDOWN_SECONDS=30
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with Factorio credentials
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Servers
- `GET /api/servers/` - List all servers
- `POST /api/servers/` - Create new server
- `GET /api/servers/{name}` - Get server details
- `PUT /api/servers/{name}` - Update server version
- `DELETE /api/servers/{name}` - Delete server
- `POST /api/servers/{name}/start` - Start server
- `POST /api/servers/{name}/stop` - Stop server
- `POST /api/servers/{name}/restart` - Restart server
- `GET /api/servers/{name}/status` - Get server status
- `GET /api/servers/{name}/logs` - Get server logs

### Mods
- `GET /api/mods/search` - Search mods
- `GET /api/mods/{mod_name}/details` - Get mod details
- `GET /api/mods/{server_name}/mods` - List server mods
- `POST /api/mods/{server_name}/mods/install` - Install single mod
- `POST /api/mods/{server_name}/mods/batch-install` - Install multiple mods
- `PATCH /api/mods/{server_name}/mods/toggle` - Enable/disable mod
- `DELETE /api/mods/{server_name}/mods/{mod_name}` - Uninstall mod

## User Flow

1. **Login**: Authenticate with Factorio.com credentials
2. **Create Server**: Specify server name and Factorio version
3. **Manage Server**: Start, stop, restart, or delete servers
4. **Manage Mods**:
   - Search for mods from the Factorio mod portal
   - Add mods to installation queue
   - Install multiple mods at once (batch installation)
   - Enable/disable installed mods
   - Uninstall unwanted mods

## Development

### Backend
```bash
cd src
python -m uvicorn backend.main:app --reload
```

### Frontend
```bash
cd src/frontend
bun dev
```

### Code Style

Backend:
- Linting: `ruff check src/backend/`
- Formatting: `ruff format src/backend/`

Frontend:
- TypeScript: `cd src/frontend && tsc --noEmit`

## License

MIT
