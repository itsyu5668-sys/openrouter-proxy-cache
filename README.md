# OpenRouter Proxy Cache – Free Hosted Version

A tiny, open-source proxy in front of [OpenRouter](https://openrouter.ai) that caches
**exact-match** prompts. When two requests share the same messages + model, the second
one is served from cache for free — no upstream call, no tokens billed.

## Why

AI bills scale linearly with requests, but a surprising fraction of calls are repeats
(scripts, cron jobs, retries, deterministic test prompts). This proxy catches those
repeats and returns the cached response instantly.

## Use the live hosted version (free, no sign-up)

You can use the live, free hosted version immediately – no sign-up, no credit card.
Just point your `base_url` to:

```
https://openrouter-proxy.onrender.com/v1/chat/completions
```

Drop-in compatible with any OpenAI-style client:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter-proxy.onrender.com/v1",
    api_key="any-string",  # the proxy uses its own OpenRouter key server-side
)

resp = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Say hi"}],
)
print(resp.choices[0].message.content)
```

Send the same prompt twice and watch the second response come back instantly with
`"_cache": "hit"` in the payload.

## What it does

- `POST /v1/chat/completions` — OpenAI-compatible chat endpoint.
- Reads `messages[-1].content`, estimates tokens, and logs the retail cost
  (assumes $3 / 1M tokens) of every incoming prompt.
- Checks an in-memory exact-match cache (keyed on full message list + model).
- **Cache hit** → returns cached response, logs the amount saved.
- **Cache miss** → forwards to the upstream provider, stores the response, and
  returns it.
- `GET /health` — liveness + cache size.

## Upstream provider

The proxy is provider-agnostic and defaults to **Groq** (free tier, OpenAI-compatible).
Set `UPSTREAM_PROVIDER` to switch:

| Provider | Env var with the key | Default model |
|---|---|---|
| `groq` (default) | `GROQ_API_KEY` | `llama-3.1-8b-instant` |
| `openrouter` | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` |

Because Groq and OpenRouter both speak the OpenAI API, the request/response body
is passed through unchanged — your client code doesn't care which is behind it.

## Run locally

```bash
pip install -r requirements.txt
export UPSTREAM_PROVIDER=groq
export GROQ_API_KEY=gsk-...
uvicorn main:app --host 0.0.0.0 --port 10000
```

## Deploy to Render (one click)

This repo ships a `render.yaml`. In Render: **New → Web Service → connect this repo →
"Use render.yaml"** → set your `OPENROUTER_API_KEY` env var → Deploy. See
[`DEPLOY.md`](DEPLOY.md) for the full step-by-step.

## Project layout

```
main.py            # FastAPI proxy + in-memory cache
requirements.txt   # fastapi, uvicorn, httpx, python-dotenv
render.yaml        # Render one-click deploy spec
cache.json         # placeholder (cache is in-memory at runtime)
```

## Limitations (free tier)

- Cache is in-memory and per-instance (resets on redeploy / spin-down). The paid
  version moves to persistent + semantic caching.
- Exact-match only — no fuzzy / semantic dedup in the free tier.
- No auth on the proxy itself; anyone with the URL can use it. Rotate the URL or add
  your own gateway auth if you share it.

## Enterprise / paid version

The source is open. For enterprise usage with semantic caching and a dashboard,
contact me.

## License

MIT
