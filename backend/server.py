"""
Farmer Pro Backend - Main Entry
"""
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import sys
from pathlib import Path

# Add current dir to path for inner imports
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from api.routes import router
from api.models import state

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Farmer Pro Backend Starting...")
    yield
    print("🛑 Shutting down workers...")
    for serial, proc in state.workers.items():
        proc.terminate()

app = FastAPI(title="Farmer Pro API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        state.websockets.remove(websocket)
        # Verify if cleanup is needed (auto-shutdown when app closes)
        if len(state.websockets) == 0:
            print("⚠️ No clients connected. Shutting down in 3s...")
            import asyncio
            import os
            import signal
            
            async def delayed_shutdown():
                await asyncio.sleep(3)
                if len(state.websockets) == 0:
                    print("🛑 Auto-shutdown triggered!")
                    os.kill(os.getpid(), signal.SIGTERM)
            
            asyncio.create_task(delayed_shutdown())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    
    print(f"[INFO] Server running at http://{args.host}:{args.port}")
    
    # Custom log config to avoid 'isatty' error in windowed/non-TTY mode
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = '%(asctime)s - %(levelname)s - %(message)s'
    log_config["formatters"]["default"]["fmt"] = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Disable coloring to prevent isatty check failure
    log_config["formatters"]["default"]["use_colors"] = False
    log_config["formatters"]["access"]["use_colors"] = False

    uvicorn.run(app, host=args.host, port=args.port, log_config=log_config)
