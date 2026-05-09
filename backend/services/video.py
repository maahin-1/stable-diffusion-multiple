import os
import ffmpeg
from config import MIN_FPS, MAX_FPS

def extract_frames(video_path: str, output_dir: str, fps: int) -> int:
    if fps < MIN_FPS or fps > MAX_FPS:
        raise ValueError(f"FPS must be between {MIN_FPS} and {MAX_FPS}")
    os.makedirs(output_dir, exist_ok=True)
    output_pattern = os.path.join(output_dir, "frame_%05d.jpg")
    (
        ffmpeg
        .input(video_path)
        .output(output_pattern, vf=f"fps={fps}", qscale_v=2)
        .run(overwrite_output=True, quiet=True)
    )
    return len([f for f in os.listdir(output_dir) if f.endswith(".jpg")])

def reconstruct_video(frames_dir: str, output_path: str, fps: int, quality: str = "preview") -> str:
    input_pattern = os.path.join(frames_dir, "frame_%05d.jpg")
    if quality == "preview":
        vf = "scale=1280:720:force_original_aspect_ratio=decrease"
        crf = 28
    else:
        vf = None
        crf = 18
    stream = ffmpeg.input(input_pattern, framerate=fps)
    kwargs = {"vcodec": "libx264", "crf": crf, "pix_fmt": "yuv420p"}
    if vf:
        kwargs["vf"] = vf
    stream.output(output_path, **kwargs).run(overwrite_output=True, quiet=True)
    return output_path
