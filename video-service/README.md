# Learnify Notes-to-Video Service

This service is intentionally separate from the Vercel React app because video generation is long-running and uses Python, MoviePy/FFmpeg and local job files.

## Local run

```bash
cd video-service
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt

# Optional: point at an Ollama server for model-written narration.
# export OLLAMA_HOST=http://127.0.0.1:11434
# export LOCAL_LLM_MODEL=qwen2.5:7b
uvicorn server:app --host 0.0.0.0 --port 8000
```

Health check:
`GET http://localhost:8000/health`

The React app expects:
`VITE_VIDEO_API_URL=http://localhost:8000`

## Deploy

Deploy this folder to a Python-friendly service such as Render or Railway. Set:

- OLLAMA_HOST (optional; defaults to http://127.0.0.1:11434)
- LOCAL_LLM_MODEL (optional; defaults to qwen2.5:7b)
- ENABLE_OFFLINE_FALLBACK (optional; defaults to true)
- FRONTEND_URL
- MAX_FILE_MB

Then set `VITE_VIDEO_API_URL` in the Vercel frontend project to the deployed service URL and redeploy the frontend.

## Important

The service keeps generated jobs on its own disk. For a production system where videos must survive service restarts/redeploys, replace the local `jobs/` directory with object storage such as S3/Cloudinary/Supabase Storage.
