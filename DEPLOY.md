# Self-host on Render (5 steps)

openvault is meant to be self-hosted. These steps deploy your own private
instance to Render so you can run it on a cloud server instead of your laptop.

1. **Push the code to GitHub.** If you haven't already:
   ```bash
   git clone https://github.com/itsyu5668-sys/openvault.git
   cd openvault
   git remote set-url origin https://github.com/<your-username>/openvault.git
   git push -u origin main
   ```
   (Or fork it first and push your fork.)

2. **Log into [Render.com](https://render.com)** (sign up free if needed; no credit
   card required for the free web-service tier).

3. **New Web Service, then connect this repo.** From the dashboard click
   **New +**, then **Web Service**, then select your `openvault` repo. Grant
   Render access to the repo when prompted.

4. **Choose "Use render.yaml".** Render will detect `render.yaml` and auto-fill
   the runtime, build command (`pip install -r requirements.txt`), and start
   command (`uvicorn main:app --host 0.0.0.0 --port $PORT`). Do not change
   these.

5. **Set your provider key, then Deploy.** In the Environment section, set
   `GROQ_API_KEY` (or `OPENROUTER_API_KEY` if you switched
   `UPSTREAM_PROVIDER` to `openrouter`) to your real key. Leave the placeholder
   values behind. Click **Create Web Service** or **Deploy**.

Wait about 1 to 2 minutes for the build and deploy. Render gives you a URL like
`https://openvault-proxy-xxxx.onrender.com`. Test it:

```bash
curl https://openvault-proxy-xxxx.onrender.com/health
# {"status":"healthy","cache_size":0}

curl -X POST https://openvault-proxy-xxxx.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"Say hi"}]}'
```

Send the same prompt twice. The second response returns instantly with
`"_cache": "hit"`. Done.
