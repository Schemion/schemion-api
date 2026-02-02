import re
import zipfile
from io import BytesIO
from fastapi import HTTPException

# TODO: вынести их отсюда в val_config.json

MAX_FILENAME_LENGTH = 255
FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-.\s]+$')
ALLOWED_EXTENSION = '.zip'

IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff'}
TEXT_EXTENSIONS = {'csv', 'txt', 'yml', 'yaml'}

MAX_DATASET_FILE_SIZE = 5 * 1024 ** 3  # 5 GB


def validate_dataset_archive(file_data: bytes, filename: str) -> None:
    if not file_data:
        raise HTTPException(400, "Uploaded dataset file is empty")

    if not filename or not filename.strip():
        raise HTTPException(400, "Filename is empty")

    filename = filename.strip()

    if len(filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(400, "Filename is too long")

    if not FILENAME_REGEX.match(filename):
        raise HTTPException(400, "Filename contains invalid characters")

    if len(file_data) > MAX_DATASET_FILE_SIZE:
        raise HTTPException(
            400,
            f"Dataset file is too large. Max allowed size is {MAX_DATASET_FILE_SIZE} bytes"
        )

    if not filename.lower().endswith(ALLOWED_EXTENSION):
        raise HTTPException(400, f"Only {ALLOWED_EXTENSION} files are allowed")

    try:
        with zipfile.ZipFile(BytesIO(file_data)) as zf:
            infos = zf.infolist()

            has_image = False
            has_text = False
            files_checked = 0

            for info in infos:
                if info.is_dir():
                    continue

                if info.filename.startswith("/") or ".." in info.filename.split("/"):
                    raise HTTPException(400, "Invalid file path inside zip")

                ext = info.filename.rsplit(".", 1)[-1].lower()

                if ext in IMAGE_EXTENSIONS:
                    has_image = True
                elif ext in TEXT_EXTENSIONS:
                    has_text = True

                files_checked += 1
                if files_checked >= 100:
                    break

            if files_checked == 0:
                raise HTTPException(400, "Zip file contains no files")
            if not has_image:
                raise HTTPException(400, "Zip file contains no image files")
            if not has_text:
                raise HTTPException(400, "Zip file contains no annotation files")

    except zipfile.BadZipFile:
        raise HTTPException(400, "Bad zip file")
