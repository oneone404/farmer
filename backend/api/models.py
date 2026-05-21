from pydantic import BaseModel
from typing import Dict, List, Optional
import subprocess
from fastapi import WebSocket

class DeviceInfo(BaseModel):
    index: int
    serial: str
    name: str
    status: str = "idle"

class InstanceConfig(BaseModel):
    enable_buy_fruits: bool = True
    enable_buy_voi: bool = True
    enable_harvest_sell: bool = True
    use_time_gate: bool = True
    first_run_immediate: bool = True
    threshold: float = 0.95
    harvest_sell_cycles: int = 1
    sell_cycles_after_harvest: int = 1
    fruits: Dict[str, dict] = {}

class StartWorkerRequest(BaseModel):
    device_serial: str
    ld_index: int

class AppState:
    def __init__(self):
        self.devices: Dict[str, DeviceInfo] = {}
        self.workers: Dict[str, subprocess.Popen] = {}
        self.websockets: List[WebSocket] = []
        
    async def broadcast(self, message: dict):
        for ws in self.websockets[:]:
            try:
                await ws.send_json(message)
            except:
                self.websockets.remove(ws)

state = AppState()
