import os
import io
import base64
import requests
from PIL import Image

HF_SEGMENTATION_MODEL = "mattmdjaga/segformer_b2_clothes"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_SEGMENTATION_MODEL}"

CLOTHING_LABELS = {
    "Upper-clothes", "Dress", "Coat", "Pants", "Skirt",
    "Left-shoe", "Right-shoe", "Scarf", "Hat",
}

def segment_clothing(image_path: str, output_path: str, api_token: str) -> str:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.post(HF_API_URL, headers=headers, data=image_bytes, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(f"Segmentation API error {response.status_code}: {response.text[:300]}")

    results = response.json()
    if not isinstance(results, list) or not results:
        raise RuntimeError(f"Unexpected segmentation response: {str(results)[:200]}")

    # Open source image to get dimensions for blank mask fallback
    src = Image.open(image_path).convert("RGB")
    w, h = src.size
    combined = Image.new("L", (w, h), 0)

    for item in results:
        label = item.get("label", "")
        if label not in CLOTHING_LABELS:
            continue
        mask_b64 = item.get("mask")
        if not mask_b64:
            continue
        mask_bytes = base64.b64decode(mask_b64)
        mask = Image.open(io.BytesIO(mask_bytes)).convert("L")
        if mask.size != (w, h):
            mask = mask.resize((w, h), Image.NEAREST)
        # OR the clothing masks together
        import numpy as np
        combined_arr = np.array(combined)
        mask_arr = np.array(mask)
        combined = Image.fromarray(np.maximum(combined_arr, mask_arr))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.save(output_path)
    return output_path
