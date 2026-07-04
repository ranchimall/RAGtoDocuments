"""
Decides whether a content item needs an image and makes sure a usable
local file path is available for the renderer.

Two sources are supported:
  1. Metadata-supplied image_path (local file or http(s) URL) -> download if remote
  2. No image available -> renderer falls back to a text-only layout variant
"""
import hashlib
import os
import urllib.request

CACHE_DIR = "./.image_cache"


def resolve_image(image_path: str | None) -> str | None:
    if not image_path:
        return None

    if image_path.startswith("http://") or image_path.startswith("https://"):
        os.makedirs(CACHE_DIR, exist_ok=True)
        ext = os.path.splitext(image_path)[1] or ".jpg"
        cache_key = hashlib.sha256(image_path.encode()).hexdigest()[:16]
        local_path = os.path.join(CACHE_DIR, f"{cache_key}{ext}")
        if not os.path.exists(local_path):
            try:
                urllib.request.urlretrieve(image_path, local_path)
            except Exception:
                return None
        return local_path

    return image_path if os.path.exists(image_path) else None
