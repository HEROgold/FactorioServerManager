from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse

app = FastAPI()

# Serve static files with Bun
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Serve React app
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    return FileResponse('frontend/build/index.html')

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Set up templates
templates = Jinja2Templates(directory="templates")

# ...existing code...
