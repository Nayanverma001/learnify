FROM python:3.11-slim

# pyttsx3's Linux backend shells out to espeak; ffmpeg is needed by moviepy
# even though imageio-ffmpeg bundles a copy, having the system binary avoids
# edge cases with some codecs/fonts.
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway/Render/Fly all inject PORT; fall back to 8000 for local docker run.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
