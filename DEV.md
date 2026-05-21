# Farmer Tauri - Development Scripts

# Run in separate terminals:
# 1. Start Python Backend
# 2. Start Tauri Dev

# ============ PowerShell Scripts ============

# Start Backend (Terminal 1)
# cd python-backend
# pip install -r requirements.txt
# python server.py --port 8765

# Start Tauri Dev (Terminal 2)  
# npm run tauri dev

# ============ Build for Production ============

# 1. Build Python backend to exe
# cd python-backend
# pip install nuitka
# nuitka --standalone --onefile server.py -o python-backend.exe

# 2. Copy python-backend.exe to src-tauri/binaries/
# mkdir src-tauri/binaries
# copy python-backend.exe src-tauri/binaries/python-backend-x86_64-pc-windows-msvc.exe

# 3. Build Tauri
# npm run tauri build
