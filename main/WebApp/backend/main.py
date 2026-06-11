import json
import os.path
import signal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic
from starlette.staticfiles import StaticFiles

from file_lib.file_api import router as router_file
from processs_manager.process_api import router as router_process

from models import *
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_origin_regex=r"http://192\.168\.\d+\.\d+(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router_file)
app.include_router(router_process)


STORAGE = "app/storage"
os.makedirs(STORAGE, exist_ok=True)
