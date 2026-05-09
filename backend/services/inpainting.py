import base64
import time
import requests

REPLICATE_MODEL = "stability-ai/stable-diffusion-inpainting"
REPLICATE_VERSION = "95b7223104132402a9ae91cc677285bc5eb997834bd2349fa486f53910fd68b3"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"

def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    ext = path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

def inpaint_frame(
    frame_path: str,
    mask_path: str,
    product_path: str,
    output_path: str,
    api_token: str,
    max_wait: int = 120
) -> str:
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "version": REPLICATE_VERSION,
        "input": {
            "image": _encode_image(frame_path),
            "mask": _encode_image(mask_path),
            "prompt": "product clothing, same style, seamless blend",
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
        }
    }
    response = requests.post(REPLICATE_API_URL, headers=headers, json=payload, timeout=30)
    prediction = response.json()
    prediction_id = prediction["id"]
    poll_url = f"{REPLICATE_API_URL}/{prediction_id}"
    elapsed = 0
    while elapsed < max_wait:
        result = requests.get(poll_url, headers=headers, timeout=30).json()
        status = result.get("status")
        if status == "succeeded":
            image_url = result["output"][0]
            img_data = requests.get(image_url, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(img_data)
            return output_path
        if status == "failed":
            raise RuntimeError(f"Inpainting failed: {result.get('error')}")
        time.sleep(2)
        elapsed += 2
    raise RuntimeError("Inpainting timed out")
