import os
import io
import requests
from PIL import Image

HF_SEGMENTATION_MODEL = "mattmdjaga/segformer_b2_clothes"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_SEGMENTATION_MODEL}"

def segment_clothing(image_path: str, output_path: str, api_token: str) -> str:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.post(HF_API_URL, headers=headers, data=image_bytes, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Segmentation API error {response.status_code}: {response.text}")
    mask_img = Image.open(io.BytesIO(response.content)).convert("L")
    mask_img.save(output_path)
    return output_path
