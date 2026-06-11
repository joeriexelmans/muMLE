import importlib.util
import sys
import os
from pathlib import Path

import uuid


def load_module_from_file(env_file, env_process_mapping):
    module_name = f"env_{uuid.uuid4().hex}"

    path = os.path.abspath(env_file)
    module_dir = os.path.dirname(path)

    sys.path.insert(0, module_dir)
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        module.__dict__.update(env_process_mapping)
        return module
    finally:
        sys.path.remove(module_dir)


def get_module_path(module: str, filename: str = "") -> Path:
    """Return absolute path to a model file inside Workflow/{module}."""
    return Path(__file__).parent.parent / module / filename