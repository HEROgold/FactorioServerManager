"""Run the FastAPI app."""
import asyncio

import uvicorn


async def main() -> None:
    """Run the FastAPI app."""
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104

if __name__ == "__main__":
    asyncio.run(main())
