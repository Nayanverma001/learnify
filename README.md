# Learnify AI

A student-focused AI learning workspace: upload study material → get structured topics, teacher-style lessons, quizzes, an AI Tutor, and notes-to-video generation.

This is **one project that runs two ways**, with no API keys required either way. When Ollama is available, it powers the AI generation. When it is not available, the app uses a deterministic offline fallback so uploads, lessons and video creation still complete instead of showing a connection error.

- `frontend/` — React + Vite student interface
- `backend/` — Express server, MongoDB models, auth, Ollama integration (`backend/lib/local-ai.js`)
- `api/` — the same backend logic, wrapped as Vercel serverless functions
- `video-service/` — Python/FastAPI notes-to-video pipeline (Ollama + offline TTS + MoviePy/FFmpeg)

## Mode 1 — Run 100% locally (no API keys, no cloud)

**Requirements:** Node.js 20+, Python 3.10+, MongoDB running locally, and FFmpeg. Ollama is optional but recommended for richer AI explanations. The video service also benefits from `espeak-ng`/`espeak` for spoken narration.

1. **Optional: install and start Ollama for full AI generation:**
   ```bash
   ollama pull qwen2.5:7b     # or qwen2.5:3b on lower-RAM machines
    ollama serve
   ```
2. **Backend:**
   ```bash
   cp .env.example .env      # defaults already point at localhost
    npm install
    npm start                 # http://localhost:5000
   ```
3. **Frontend** (new terminal):
   ```bash
   cd frontend
   npm install
   echo "VITE_API_URL=http://localhost:5000/api" > .env
   npm run dev                # http://localhost:5173
   ```
4. **Video service** (new terminal):
   ```bash
   cd video-service
   python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn server:app --host 0.0.0.0 --port 8000
   ```
   Add `VITE_VIDEO_API_URL=http://localhost:8000` to `frontend/.env` if you want notes-to-video in local dev.

Everything uses the local Ollama model when it is reachable. No Gemini/OpenAI/Anthropic key is used anywhere in this code. If Ollama is offline, topic extraction, lessons and tutor answers use an offline fallback; video narration falls back to the uploaded text and can still render a video.

## Mode 2 — Deploy to Vercel

Vercel can host the frontend + the lightweight API routes (`api/`), but **cannot** run Ollama itself or the video-rendering pipeline (no persistent process, no FFmpeg/MoviePy support in serverless functions). So:

1. **Get Ollama running somewhere always-on** — a small VPS (4-8GB RAM) works: install Ollama, `ollama pull qwen2.5:7b`, `ollama serve`, and firewall port 11434 to only your trusted servers.
2. **Database:** create a free MongoDB Atlas cluster and grab the connection string.
3. **Deploy this repo to Vercel** (root of repo — `vercel.json` already builds `frontend/` and serves `api/` as functions). Set these Environment Variables in the Vercel project:
   - `MONGODB_URI` — your Atlas connection string
   - `JWT_SECRET` — a long random string
   - `FRONTEND_URL` — your Vercel deployment URL (no trailing slash)
   - `OLLAMA_HOST` — `http://YOUR_VPS_IP:11434`
   - `LOCAL_LLM_MODEL` — `qwen2.5:7b` (must match what you pulled)
   - `VITE_API_URL` — `/api` (same-origin, since frontend and api share one Vercel domain)
4. **Notes-to-video:** deploy `video-service/` separately (it needs a real container, not serverless) — Render, Railway, or Fly.io all work with the included `Dockerfile`. Point `VITE_VIDEO_API_URL` at that service's URL, set `FRONTEND_URL` to the Vercel URL, and optionally give it the same `OLLAMA_HOST`/`LOCAL_LLM_MODEL` env vars.

No API keys required in either mode — only the URL of wherever Ollama is running.

## Important deployment detail

`127.0.0.1` means the current machine/container. It does **not** mean your
laptop when the app is deployed on Vercel. The original video error
(`Could not reach Ollama at http://127.0.0.1:11434`) happened because the
deployed service was trying to find Ollama inside its own container.

You have two working choices:

1. Set `OLLAMA_HOST` in the backend/video-service deployment to an Ollama
   server that is reachable over the network, and pull the configured model
   there.
2. Leave `ENABLE_OFFLINE_FALLBACK=true`. The app will still save materials and
   generate lessons/videos without Ollama, but the generated explanations will
   be simpler.

Do not expose an unauthenticated Ollama port to the public internet. Put it
behind a private network or an authenticated reverse proxy.

## Supported uploads

PDF, DOCX, and TXT files up to `MAX_UPLOAD_MB`.
