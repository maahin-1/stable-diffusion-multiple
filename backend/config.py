import os
import tempfile

BASE_STORAGE = os.environ.get("SD_STORAGE", os.path.join(tempfile.gettempdir(), "sd-overlay"))
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
MAX_FPS = 60
MIN_FPS = 1
