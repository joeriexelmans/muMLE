from fastapi import APIRouter
from .lib_service import get_file_structure, get_file_content, update_file, delete_file, create_directory
from .file_models import FileUpdate


router = APIRouter(prefix="", tags=["items"])

@router.get("/files/{path:path}")
def get_file_structure_api(path: str = ""):
    return get_file_structure(path)

@router.put("/files/{path:path}")
def create_directory_api(path: str):
    return create_directory(path)

@router.get("/file/{path:path}")
def get_file_content_api(path: str):
    return get_file_content(path)

@router.put("/file/{path:path}")
def update_file_api(path: str, body: FileUpdate):
    return update_file(path, body.content, body.__getattribute__("type"))

@router.delete("/file/{path:path}")
def delete_file_api(path: str):
    return delete_file(path)