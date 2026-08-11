"""OpenRouter Proxy Cache - free hosted version.

Caches exact-match prompts to cut AI costs. Forwards misses to OpenRouter.
"""
import os
import json
import logging
import time
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("proxy")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Retail pricing assumption for cost logging: $3 per 1M tokens.
COST_PER_1M_TOKENS = 3.0

app = FastAPI(title="OpenRouter Proxy Cache")

# In-memory exact-match cache: prompt_hash -> response payload.
cache: dict[str, dict[str, Any]] = {}


def estimate_tokens(text: str) -> int:
    """Rough 4-chars-per-token estimate. Good enough for cost logging."""
    return max(1, len(text) // 4)


def retail_cost(text: str) -> float:
    return (estimate_tokens(text) / 1_000_000) * COST_PER_1M_TOKENS


def cache_key(messages: list[dict[str, Any]], model: str) -> str:
    # Exact-match: hash the full message list + model.
    import hashlib
    payload = json.dumps({"m": messages, "model": model}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


@app.get("/")
def root():
    return {"status": "ok", "service": "openrouter-proxy-cache"}


@app.get("/health")
def health():
    return {"status": "healthy", "cache_size": len(cache)}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid JSON body"})

    messages = body.get("messages", [])
    model = body.get("model", "openai/gpt-4o-mini")
    if not messages:
        return JSONResponse(status_code=400, content={"error": "messages is required"})

    prompt = messages[-1].get("content", "") if isinstance(messages[-1], dict) else ""
    prompt_cost = retail_cost(prompt)
    log.info("incoming model=%s est_tokens=%d retail_cost=$%.6f", model, estimate_tokens(prompt), prompt_cost)

    key = cache_key(messages, model)
    if key in cache:
        hit = cache[key]
        log.info("CACHE HIT saved=$%.6f", prompt_cost)
        resp = dict(hit["response"])
        resp["_cache"] = "hit"
        return JSONResponse(content=resp)

    log.info("CACHE MISS forwarding to OpenRouter")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if referer := request.headers.get("referer"):
        headers["HTTP-Referer"] = referer
    if title := request.headers.get("x-title"):
        headers["X-Title"] = title

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(OPENROUTER_URL, headers=headers, json=body)
    except httpx.RequestError as e:
        log.error("upstream error: %s", e)
        return JSONResponse(status_code=502, content={"error": f"upstream error: {e}"})

    if r.status_code >= 400:
        log.error("upstream status=%d body=%s", r.status_code, r.text[:500])
        return JSONResponse(status_code=r.status_code, content={"error": r.text})

    try:
        upstream_json = r.json()
    except Exception:
        return JSONResponse(status_code=502, content={"error": "non-JSON upstream response"})

    cache[key] = {"response": upstream_json, "ts": time.time()}
    log.info("stored cache entry (size=%d)", len(cache))
    out = dict(upstream_json)
    out["_cache"] = "miss"
    return JSONResponse(content=out)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
