import requests

HF_DETECTION_MODEL = "facebook/detr-resnet-50"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_DETECTION_MODEL}"

def detect_persons(image_path: str, api_token: str) -> list:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.post(HF_API_URL, headers=headers, data=image_bytes, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Detection API error {response.status_code}: {response.text}")
    results = response.json()
    return [r for r in results if r.get("label") == "person" and r.get("score", 0) > 0.5]
