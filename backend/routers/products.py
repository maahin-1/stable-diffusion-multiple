import os
import json
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from storage.session_store import session_exists, get_session_path
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["products"])

def get_products_dir(session_id: str) -> str:
    return os.path.join(get_session_path(session_id, base=BASE_STORAGE), "products")

def load_product_index(session_id: str) -> dict:
    index_path = os.path.join(get_products_dir(session_id), "index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return json.load(f)
    return {}

def save_product_index(session_id: str, index: dict) -> None:
    index_path = os.path.join(get_products_dir(session_id), "index.json")
    with open(index_path, "w") as f:
        json.dump(index, f)

@router.post("/{session_id}/products")
async def upload_product(session_id: str, tag: str = Form(...), file: UploadFile = File(...)):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    products_dir = get_products_dir(session_id)
    tag_dir = os.path.join(products_dir, tag)
    os.makedirs(tag_dir, exist_ok=True)
    dest = os.path.join(tag_dir, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    index = load_product_index(session_id)
    if tag not in index:
        index[tag] = []
    if file.filename not in index[tag]:
        index[tag].append(file.filename)
    save_product_index(session_id, index)
    return {"tag": tag, "filename": file.filename}

@router.get("/{session_id}/products")
async def list_products(session_id: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    index = load_product_index(session_id)
    return {"products": index}

@router.get("/{session_id}/products/{tag}/{filename}/image")
async def get_product_image(session_id: str, tag: str, filename: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    from fastapi.responses import FileResponse
    path = os.path.join(get_products_dir(session_id), tag, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Product image not found")
    return FileResponse(path, media_type="image/jpeg")
