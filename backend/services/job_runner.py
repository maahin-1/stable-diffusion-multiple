import os
import asyncio
from typing import List, Dict, Callable
from services.inpainting import inpaint_frame
from storage.session_store import get_session_path

async def run_inpainting_job(
    session_id: str,
    base: str,
    assignments: List[Dict],
    api_token: str,
    on_progress: Callable[[Dict], None] = None
):
    session_path = get_session_path(session_id, base=base)
    processed_dir = os.path.join(session_path, "processed")
    segments_dir = os.path.join(session_path, "segments")
    products_dir = os.path.join(session_path, "products")

    for assignment in assignments:
        frame_index = assignment["frame_index"]
        product_tag = assignment["product_tag"]
        product_image = assignment["product_image"]

        frame_path = os.path.join(session_path, "frames", f"frame_{frame_index:05d}.jpg")
        mask_path = os.path.join(segments_dir, f"mask_{frame_index:05d}.png")
        product_path = os.path.join(products_dir, product_tag, product_image)
        output_path = os.path.join(processed_dir, f"frame_{frame_index:05d}.jpg")

        try:
            await asyncio.to_thread(
                inpaint_frame,
                frame_path, mask_path, product_path, output_path, api_token
            )
            if on_progress:
                on_progress({"frame_index": frame_index, "status": "completed"})
        except Exception as e:
            if on_progress:
                on_progress({"frame_index": frame_index, "status": "failed", "error": str(e)})
