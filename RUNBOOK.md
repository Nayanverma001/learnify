# Learnify AI runbook

## Local development

1. Install Node.js 20+, Python 3.10+, MongoDB, and FFmpeg.
2. Optional but recommended: install Ollama, then run:
   `ollama pull qwen2.5:7b`. The Learnify tutor now creates structured
   teacher lessons with deterministic diagrams, examples, exam tips and quick
   checks. `OLLAMA_MODEL` is preferred; existing `LOCAL_LLM_MODEL` files remain
   supported.
3. From this directory:
   `cp .env.example .env`
4. Set a real `JWT_SECRET` in `.env`. Keep `ENABLE_OFFLINE_FALLBACK=true`
   unless you deliberately want missing Ollama to fail requests.
5. Install and start the backend:
   `npm install`
   `npm start`
6. In another terminal install and start the frontend:
   `cd frontend`
   `cp .env.example .env`
   `npm install`
   `npm run dev`
7. In a third terminal start the video service:
   `cd video-service`
   `python -m venv .venv`
   Activate the environment, then run `pip install -r requirements.txt`.
   Start it with `uvicorn server:app --host 0.0.0.0 --port 8000`.
8. Open `http://localhost:5173`, register a user, and upload a small text-based
   PDF. Check `http://localhost:5000/api/health` and
   `http://localhost:8000/health` if anything is unclear.

## Vercel + hosted services

1. Create MongoDB Atlas and set `MONGODB_URI`.
2. Set `JWT_SECRET`, `FRONTEND_URL`, `VITE_API_URL=/api`,
   `ENABLE_OFFLINE_FALLBACK=true`, and `MAX_UPLOAD_MB=4` in Vercel.
3. Deploy the project root, not the `frontend` folder.
4. Deploy `video-service/` to Render, Railway, or Fly.io using its Dockerfile.
   Set `FRONTEND_URL` to the Vercel URL and copy the service's public URL into
   Vercel as `VITE_VIDEO_API_URL`, then redeploy the frontend.
5. Never use `OLLAMA_HOST=http://127.0.0.1:11434` in a hosted service unless
   Ollama is running in the same container. Use a reachable private Ollama
   server, or keep the offline fallback enabled.