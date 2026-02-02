import re

import magic
from fastapi import HTTPException

ALLOWED_EXTENSIONS = {'pt', 'pth'}
MAX_FILENAME_LENGTH = 255
FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-.\s]+$')
ALLOWED_MIME_TYPES = {'application/octet-stream', 'application/x-pickle'}
MAX_MODEL_FILE_SIZE = 1024 ** 3

async def validate_model_file(file_data: bytes, filename: str):
    if not file_data:
        raise HTTPException(400, "Uploaded model file is empty")

    if not filename or not filename.strip():
        raise HTTPException(400, "Uploaded file is empty")

    filename = filename.strip()

    if "." not in filename:
        raise HTTPException(400, "Filename must have extension")

    if len(filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(400, "Filename is too long")

    if not FILENAME_REGEX.match(filename):
        raise HTTPException(400, "Filename contains invalid characters")

    ext = filename.rsplit(".", 1)[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Filename extension is invalid. Only pt & pth allowed")

    if len(file_data) > MAX_MODEL_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Model file size exceeds 1GB limit")

    try:
        mime_type = magic.from_buffer(file_data, mime=True)
    except Exception as e:
        raise HTTPException(400, f"Failed to determine mime type. Error {e}")

    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"Invalid file type: {mime_type}")
