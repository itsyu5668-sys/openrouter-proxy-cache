# openvault

An open-source prompt-caching proxy. It sits in front of your LLM provider and
caches **exact-match** prompts, so when two requests share the same messages and
model, the second one is served from cache instantly with no upstream call and
no tokens billed.

Self-host it for free on your own machine. That is what this repo is for.

## Why

AI bills scale linearly with requests, but a surprising fraction of calls are
repeats: cron jobs, retries, scripts, deterministic test prompts, CI pipelines
that fire the same inputs over and over. openvault catches those repeats and
returns the cached response instead of paying for the same answer twice.

## Self-host (free)

This is the intended way to use openvault. Clone it, run it, point your client
at `localhost`, keep your keys on your own machine.

```bash
git clone https://github.com/itsyu5668-sys/openvault.git
cd openvault
pip install -r requirements.txt
export UPSTREAM_PROVIDER=groq
export GROQ_API_KEY=gsk-...
uvicorn main:app --host 0.0.0.0 --port 10000
```

Then point any OpenAI-compatible client at it:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:10000/v1",
    api_key="any-string",  # openvault uses your provider key server-side
)

resp = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Say hi"}],
)
print(resp.choices[0].message.content)
```

Send the same prompt twice and the second response comes back instantly with
`"_cache": "hit"` in the payload and no upstream call.

## What it does

- `POST /v1/chat/completions` : OpenAI-compatible chat endpoint.
- Reads `messages[-1].content`, estimates tokens, and logs the retail cost
  (assumes $3 / 1M tokens) of every incoming prompt.
- Checks an in-memory exact-match cache (keyed on full message list + model).
- **Cache hit** returns the cached response and logs the amount saved.
- **Cache miss** forwards to the upstream provider, stores the response, and
  returns it.
- `GET /health` : liveness check and current cache size.

## Upstream provider

openvault is provider-agnostic and defaults to **Groq** (free tier,
OpenAI-compatible). Set `UPSTREAM_PROVIDER` to switch:

| Provider | Env var with the key | Default model |
|---|---|---|
| `groq` (default) | `GROQ_API_KEY` | `llama-3.1-8b-instant` |
| `openrouter` | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` |

Because Groq and OpenRouter both speak the OpenAI API, the request and response
body is passed through unchanged. Your client code does not care which is
behind it.

## Project layout

```
main.py            # FastAPI proxy + in-memory cache
requirements.txt   # fastapi, uvicorn, httpx, python-dotenv
render.yaml        # Render deploy spec (for self-hosting on Render)
cache.json         # placeholder (cache is in-memory at runtime)
```

## Limitations of the open-source version

These are real, and they are the reason a managed version exists. Read them
before you rely on this for anything important.

- **Cache is in-memory and per-instance.** It resets every time the process
  restarts, every redeploy, and every Render free-tier spin-down. You lose all
  cached responses on restart, so savings only accrue within a single uptime
  window.
- **Exact-match only.** There is no fuzzy or semantic deduplication. Two prompts
  that mean the same thing but differ by a single character are treated as
  different requests and both get billed upstream.
- **No persistence.** Nothing is written to disk or a database. If you need
  cache survival across restarts, you have to build that yourself.
- **No dashboard.** There is no UI for viewing hit rate, savings, or traffic.
  You get logs and the `/health` endpoint, nothing else.
- **No auth.** Anyone who can reach the port can use the proxy and burn your
  provider key. If you expose it beyond localhost, add your own gateway auth.
- **No multi-tenant isolation.** One process, one cache, one key. It is not
  built to serve multiple users or teams safely.
- **No SLA, no uptime guarantee.** It is a single process. If it crashes, your
  requests fail until you restart it.

If any of those are a problem for you, see the managed version below.

## Managed version (paid)
  coming soon……
  
- High-uptime hosted deployment instead of a laptop process.
- Persistent cache that survives restarts, so savings compound over time.
- Semantic caching that catches near-duplicate prompts, not just exact matches.
- A dashboard showing hit rate, tokens saved, and cost avoided.
- Per-user API keys and multi-tenant isolation.
- 99.99% uptime target.


## License

MIT
