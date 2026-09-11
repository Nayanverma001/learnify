import asyncio
import json
from pathlib import Path

from extract import extract_document
from script_gen import generate_curriculum
from tts import generate_audio
from visual import generate_visual
from assemble import make_slide_clip, assemble_video


def run_pipeline(input_path: str, job_dir: str, options=None):
    options = options or {}
    job = Path(job_dir)
    assets = job / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    pages = extract_document(input_path)
    if not pages:
        raise ValueError("No readable pages/slides were found in the uploaded file.")

    full_text = "\n\n".join([p.get("text", "").strip() for p in pages if p.get("text", "").strip()]).strip()
    if not full_text:
        raise ValueError("Could not extract readable text from document.")

    # Generate comprehensive educational curriculum with definitions, diagrams, and quizzes
    scenes = generate_curriculum(full_text, options)
    if not scenes:
        raise ValueError("Failed to generate educational video scenes.")

    # Save metadata for frontend interactive gallery, definitions glossary, and quiz
    metadata = {
        "totalPages": len(pages),
        "totalScenes": len(scenes),
        "scenes": scenes,
    }
    (job / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    clips = []
    for index, scene in enumerate(scenes):
        script = scene.get("narration", "").strip()
        title = scene.get("title", f"Scene {index + 1}")

        audio_path = assets / f"scene_{index + 1}.wav"
        image_path = assets / f"scene_{index + 1}.png"

        asyncio.run(generate_audio(script, str(audio_path), options.get("voice", "default")))
        generate_visual(title, scene, str(image_path))

        clips.append(make_slide_clip(str(image_path), str(audio_path)))

    output_path = job / "output.mp4"
    try:
        assemble_video(clips, str(output_path))
    finally:
        for clip in clips:
            try:
                if clip.audio:
                    clip.audio.close()
                clip.close()
            except Exception:
                pass

    return str(output_path)
