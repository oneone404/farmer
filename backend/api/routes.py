import sys
import os
import asyncio
import json
import subprocess
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from typing import List
from pathlib import Path

from .models import DeviceInfo, InstanceConfig, StartWorkerRequest, state
from core.config import config
from ld_manager import get_ld_instances

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent

@router.get("/devices", response_model=List[DeviceInfo])
async def get_devices():
    try:
        instances = get_ld_instances()
        result = []
        for inst in instances:
            if inst["running"] and inst["serial"]:
                status = "running" if inst["serial"] in state.workers else "idle"
                device = DeviceInfo(
                    index=inst["index"],
                    serial=inst["serial"],
                    name=inst["name"],
                    status=status
                )
                result.append(device)
                state.devices[inst["serial"]] = device
        return result
    except Exception as e:
        return []

@router.get("/config/{ld_index}")
async def get_instance_config(ld_index: int):
    return config.load_instance_config(ld_index)

@router.get("/fruits")
async def get_all_fruits():
    return config.get_fruits()

@router.post("/config/{ld_index}")
async def save_instance_config(ld_index: int, cfg: InstanceConfig):
    config.save_instance_config(ld_index, cfg.model_dump())
    return {"status": "ok"}

@router.post("/worker/start")
async def start_worker(req: StartWorkerRequest):
    if req.device_serial in state.workers:
        return {"status": "error", "message": "Worker already running"}
    
    try:
        worker_path = BASE_DIR / "worker.py"
        proc = subprocess.Popen(
            [sys.executable, str(worker_path), req.device_serial, str(req.ld_index)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            cwd=str(BASE_DIR)
        )
        state.workers[req.device_serial] = proc
        
        if req.device_serial in state.devices:
            state.devices[req.device_serial].status = "running"
        
        asyncio.create_task(read_worker_logs(req.device_serial, proc))
        await state.broadcast({"type": "worker_started", "device_serial": req.device_serial})
        return {"status": "ok", "pid": proc.pid}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/worker/stop/{device_serial}")
async def stop_worker(device_serial: str):
    if device_serial not in state.workers:
        return {"status": "error", "message": "Worker not running"}
    
    try:
        proc = state.workers[device_serial]
        proc.terminate()
        del state.workers[device_serial]
        
        if device_serial in state.devices:
            state.devices[device_serial].status = "idle"
        
        await state.broadcast({"type": "worker_stopped", "device_serial": device_serial})
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def read_worker_logs(device_serial: str, proc: subprocess.Popen):
    try:
        while proc.poll() is None:
            line = await asyncio.get_event_loop().run_in_executor(
                None, proc.stdout.readline
            )
            if line:
                await state.broadcast({
                    "type": "log",
                    "device_serial": device_serial,
                    "message": line.strip()
                })
            await asyncio.sleep(0.01)
    finally:
        if device_serial in state.workers:
            del state.workers[device_serial]
        await state.broadcast({"type": "worker_stopped", "device_serial": device_serial})
