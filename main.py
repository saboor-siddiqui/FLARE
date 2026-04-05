import os
import pathlib
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="FLARE — Airflow Triage Agent")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("ANTHROPIC_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

HTML_PATH = pathlib.Path(__file__).parent / "index.html"

# Reusable HTTP client with connection pooling and optimized timeouts
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create a reusable HTTP client with optimized settings."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(90.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
    return _http_client


@app.on_event("shutdown")
async def shutdown_event():
    """Close the HTTP client on shutdown."""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the PipelineGuard UI."""
    return HTMLResponse(content=HTML_PATH.read_text(encoding="utf-8"))


@app.post("/api/triage")
async def triage(request: Request):
    """Proxy to Anthropic API with the key injected server-side."""
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    # Validate required fields first (before checking API key)
    if not body.get("model"):
        raise HTTPException(status_code=400, detail="Missing required field: model")
    if not body.get("messages"):
        raise HTTPException(status_code=400, detail="Missing required field: messages")

    # Validate API key is available
    if not API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    client = get_http_client()
    
    try:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
        )
        resp.raise_for_status()
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Anthropic API error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Request failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


def _build_slack_blocks(slack: dict) -> dict:
    """Convert the FLARE slack object into Slack Block Kit payload."""
    blocks = []

    # Header
    header_text = f"{slack.get('severity_emoji', '')} {slack.get('header', 'Airflow Alert')}".strip()
    blocks.append({"type": "header", "text": {"type": "plain_text", "text": header_text, "emoji": True}})

    # Summary
    if slack.get("summary"):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": slack["summary"]}})

    blocks.append({"type": "divider"})

    # Fields (2-column)
    fields = slack.get("fields") or []
    if fields:
        field_blocks = [{"type": "mrkdwn", "text": f"*{f['label']}*\n{f['value']}"} for f in fields]
        # Slack allows max 10 fields per section; chunk if needed
        for i in range(0, len(field_blocks), 10):
            blocks.append({"type": "section", "fields": field_blocks[i:i+10]})

    # Action items
    action_items = slack.get("action_items") or []
    if action_items:
        bullet_list = "\n".join(f"• {item}" for item in action_items)
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Action Required*\n{bullet_list}"}})

    # Fix snippet
    if slack.get("fix_snippet"):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{slack['fix_snippet']}```"}})

    # Footer
    if slack.get("footer"):
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": slack["footer"]}]})

    return {"blocks": blocks}


@app.post("/api/send-slack")
async def send_slack(request: Request):
    """Post the triage Slack message to the configured Incoming Webhook."""
    if not SLACK_WEBHOOK_URL:
        raise HTTPException(status_code=503, detail="SLACK_WEBHOOK_URL not configured")

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    payload = _build_slack_blocks(body)
    client = get_http_client()

    try:
        resp = await client.post(SLACK_WEBHOOK_URL, json=payload)
        resp.raise_for_status()
        return {"ok": True}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Slack rejected the message: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Could not reach Slack: {e}")
