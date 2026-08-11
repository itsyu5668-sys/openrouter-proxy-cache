# Deploy to Render — 5 steps

1. **Push the code to GitHub.** If you haven't already:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: OpenRouter proxy cache"
   git branch -M main
   git remote add origin https://github.com/your-username/openrouter-proxy-cache.git
   git push -u origin main
   ```
   (Replace `your-username` with your GitHub username.)

2. **Log into [Render.com](https://render.com)** (sign up free if needed — no credit
   card required for the free web-service tier).

3. **New Web Service → Connect this repo.** From the dashboard click
   **New + → Web Service →** select your `openrouter-proxy-cache` repo. Grant Render
   access to the repo when prompted.

4. **Choose "Use render.yaml".** Render will detect `render.yaml` and auto-fill the
   runtime, build command (`pip install -r requirements.txt`), and start command
   (`uvicorn main:app --host 0.0.0.0 --port 10000`). Don't change these.

5. **Set `OPENROUTER_API_KEY` → Deploy.** In the Environment section, set
   `OPENROUTER_API_KEY` to your real OpenRouter key (get one at
   https://openrouter.ai/keys). Leave the placeholder value behind. Click
   **Create Web Service** / **Deploy**.

Wait ~1–2 minutes for the build + deploy. Render gives you a URL like
`https://openrouter-proxy-xxxx.onrender.com`. Test it:

```bash
curl https://openrouter-proxy-xxxx.onrender.com/health
# {"status":"healthy","cache_size":0}

curl -X POST https://openrouter-proxy-xxxx.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"Say hi"}]}'
```

Send the same prompt twice — the second response returns instantly with
`"_cache": "hit"`. Done. 🎉
