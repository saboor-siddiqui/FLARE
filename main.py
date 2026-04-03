import os
import pathlib
import httpx
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="PipelineGuard — Airflow Triage Agent")

API_KEY = os.environ["ANTHROPIC_API_KEY"]  # loaded from .env
HTML_PATH = pathlib.Path(__file__).parent / "index.html"


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the PipelineGuard UI."""
    return HTMLResponse(content=HTML_PATH.read_text(encoding="utf-8"))


@app.post("/api/triage")
async def triage(request: Request):
    """Proxy to Anthropic API with the key injected server-side."""
    body = await request.json()

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
        )

    return JSONResponse(content=resp.json(), status_code=resp.status_code)
