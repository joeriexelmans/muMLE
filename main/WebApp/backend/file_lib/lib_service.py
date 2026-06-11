import json
import os
from pathlib import Path
from typing import Any

from fastapi import HTTPException

LIB_PATH = Path("file_lib/temp/data").resolve()
LIB_PATH.mkdir(parents=True, exist_ok=True)

def validate_path(path: str, exist=True):
    root = (LIB_PATH / path).resolve()
    if not root.is_relative_to(LIB_PATH):
        raise HTTPException(403, "Access denied")

    if exist and not root.exists():
        raise HTTPException(404, "Path does not exist")

    return root

def get_file_structure(root: str):
    def build_tree(path: Path):
        if path.is_dir():
            return {
                "name": path.name,
                "type": "directory",
                "children": [build_tree(child) for child in sorted(path.iterdir())]
            }
        else:
            return {
                "name": path.name,
                "type": "file"
            }
    return build_tree(validate_path(root))

def create_directory(path: str):
    abs_path = validate_path(path, exist=False)
    os.makedirs(abs_path, exist_ok=True)

def get_file_content(path: str):
    file = validate_path(path)
    if not file.is_file():
        raise HTTPException(404, detail="Can not request directories")

    return {
        "path": file.relative_to(LIB_PATH),
        "filename": file.name,
        "content": json.loads(file.read_text(encoding="utf-8"))
                    if file.suffix == ".json"
                    else file.read_text(encoding="utf-8")
    }

def update_file(path: str, content: Any, typ: str):
    file = validate_path(path, exist=False)
    if file.is_dir():
        raise HTTPException(400, detail="Path is not a file")

    file.parent.mkdir(parents=True, exist_ok=True)
    match typ:
        case "json":
            print("json")
            try:
                file.write_text(json.dumps(content))  # validate JSON
            except json.JSONDecodeError:
                raise HTTPException(400, "Invalid JSON content")
        case "_":
            try:
                file.write_text(content, encoding="utf-8")
            except Exception as e:
                raise HTTPException(400, str(e))

    return {"message": "File updated", "path": file.relative_to(LIB_PATH)}


def delete_file(path: str):
    file = validate_path(path)

    if file.is_file():
        file.unlink()

    elif file.is_dir():
        if any(file.iterdir()):
            raise HTTPException(400, detail="Directory is not empty")
        if file == LIB_PATH:
            raise HTTPException(403, "Access denied")
        file.rmdir()

    else:
        raise HTTPException(400, detail="Unsupported file type")

    return {
        "message": "Deleted successfully",
        "path": str(file.relative_to(LIB_PATH)).replace("\\", "/")
    }