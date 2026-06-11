from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from processs_manager.process_manager import ProcessManager
from file_lib.lib_service import validate_path

router = APIRouter()
pm = ProcessManager(Path(f"{__file__}/../../file_lib/temp").resolve())


# ----------- Request Models -----------

class CreateProcessRequest(BaseModel):
    path: str


class InitRuntimeRequest(BaseModel):
    process_id: str
    envirement: str | None = ""


class StartRequest(BaseModel):
    process_id: str
    step_through: bool = True


class ProcessIdRequest(BaseModel):
    process_id: str

class LoadRequest(BaseModel):
    process_id: str
    state: str


class VisualizeRequest(BaseModel):
    process_id: str
    output_file: str


# ----------- Endpoints -----------

@router.post("/process/create")
def create_process(req: CreateProcessRequest):
    try:
        process_id = pm.create_process(validate_path(req.path))
        return {"process_id": process_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/init-runtime")
def init_runtime(req: InitRuntimeRequest):
    try:
        runtime_id = pm.init_runtime(req.process_id, req.envirement)
        return {"runtime_id": runtime_id}
    except KeyError:
        raise HTTPException(status_code=404, detail="Process not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/start")
def start(req: StartRequest):
    try:
        pm.start(req.process_id, req.step_through)
        return {"status": "started"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Runtime not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/step")
def step(req: ProcessIdRequest):
    try:
        pm.step(req.process_id)
        return {"status": "stepped"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Runtime not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/stop")
def stop(req: ProcessIdRequest):
    try:
        pm.stop(req.process_id)
        return {"status": "stopped"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Runtime not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/process/pause")
def stop(req: ProcessIdRequest):
    try:
        pm.pause(req.process_id)
        return {"status": "paused"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Runtime not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/save")
def save(req: ProcessIdRequest):
    try:
        save_id = pm.save(req.process_id)
        return {"save_id": save_id}
    except KeyError:
        raise HTTPException(status_code=404, detail="Runtime not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/load")
def load(req: LoadRequest):
    try:
        pm.load(req.process_id, req.state)
        return {"status": "loaded"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Runtime or save not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/runtimeinfo")
def runtimeInfo(req: ProcessIdRequest):
    try:
        data = pm.get_runtime_info(req.process_id)
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail="Runtime not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/process/visualize")
def visualize(req: VisualizeRequest):
    try:
        pm.visualize(req.process_id, req.output_file)
        return {"status": "visualized"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Runtime not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))