"""Run the FastAPI app."""
import uvicorn
from app import app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)  # noqa: S104
