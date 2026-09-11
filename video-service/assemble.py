from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from pathlib import Path
import time


def make_slide_clip(image_path, audio_path):
    audio = AudioFileClip(audio_path)
    clip = ImageClip(image_path).set_duration(audio.duration)
    return clip.set_audio(audio)


def assemble_video(slide_clips, output_path):
    final = concatenate_videoclips(slide_clips, method="compose")
    # MoviePy 1.x creates a temporary MP4 audio track while rendering. On
    # Windows, its automatic cleanup can race with ffmpeg and raise
    # WinError 32 ("file is being used by another process"). Use a unique
    # temp file and clean it up only after every MoviePy handle is closed.
    output = Path(output_path)
    temp_audio = output.with_name(f"{output.stem}_temp_audio.mp4")

    try:
        final.write_videofile(
            str(output),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(temp_audio),
            remove_temp=False,
            logger=None,
        )
    finally:
        final.close()

    # Cleanup is best effort. Leaving a small temp file is safer than marking
    # an otherwise valid video job as failed on Windows.
    for _ in range(5):
        try:
            if temp_audio.exists():
                temp_audio.unlink()
            break
        except PermissionError:
            time.sleep(0.5)
