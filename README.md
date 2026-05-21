# Farmer Automation - Tauri Edition

Ứng dụng tự động hóa game với giao diện Tauri đẹp và backend Python mạnh mẽ.

## 📁 Cấu trúc Project

```
Farmer/
├── src/                          # Frontend UI (HTML/CSS/JS)
│   ├── index.html               # Dashboard chính
│   ├── styles.css               # Design system (dark/light mode)
│   └── main.js                  # App logic + WebSocket
├── src-tauri/                   # Tauri Core (Rust)
│   ├── tauri.conf.json          # Config Tauri
│   ├── resources/               # Bundled resources (backend exe)
│   └── src/lib.rs               # Auto-start backend
├── backend/              # Python Backend (Standalone)
│   ├── server.py                # FastAPI + WebSocket server
│   ├── worker.py                # Automation worker
│   ├── ld_manager.py            # LDPlayer manager
│   ├── core/                    # Core modules
│   ├── modules/                 # Business logic
│   ├── assets/                  # Template images
│   └── adb/                     # ADB binaries
├── build.ps1                    # Build script
└── package.json
```

## 🚀 Development

### Cài đặt Dependencies

```powershell
# Frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

### Chạy Development Mode

**Terminal 1 - Python Backend:**
```powershell
cd backend
python server.py --port 8765
```

**Terminal 2 - Tauri Dev:**
```powershell
npm run tauri dev
```

## 📦 Build Production (Single Installer)

### Quick Build

```powershell
# Build cả Python backend và Tauri app
.\build.ps1

# Hoặc skip Python nếu đã build trước đó
.\build.ps1 -SkipPython
```

### Manual Build

**Step 1: Build Python Backend**
```powershell
cd python-backend
pip install nuitka
python -m nuitka --standalone --onefile --output-filename=farmer-backend.exe server.py
```

**Step 2: Copy to Tauri resources**
```powershell
copy farmer-backend.exe ..\src-tauri\resources\
```

**Step 3: Build Tauri Installer**
```powershell
cd ..
npm run tauri build
```

**Output:** `src-tauri/target/release/bundle/nsis/Farmer_1.0.0_x64-setup.exe`

## 📂 Data Storage

| Folder | Location | Purpose |
|--------|----------|---------|
| **Configs** | `%APPDATA%\Farmer\configs\` | User settings, instance configs |
| **Logs** | `%APPDATA%\Farmer\logs\` | Application logs |
| **Install** | `C:\Program Files\Farmer\` | App executable, assets |

## 🔄 Auto-Update

Tauri updater đã được cấu hình sẵn. Để enable:

1. Generate update keys:
```powershell
npm run tauri signer generate -- -w ~/.tauri/farmer.key
```

2. Update `tauri.conf.json` với pubkey và endpoint.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/devices` | Danh sách devices |
| GET | `/config/{ld_index}` | Lấy config instance |
| POST | `/config/{ld_index}` | Lưu config instance |
| POST | `/worker/start` | Bắt đầu worker |
| POST | `/worker/stop/{serial}` | Dừng worker |
| WS | `/ws` | WebSocket real-time logs |

## 🎨 UI Features

- ✅ Dashboard với sidebar devices
- ✅ Stats cards (Devices, Running, Cycles, Uptime)
- ✅ Real-time log console
- ✅ Config modal cho từng device
- ✅ Dark/Light mode toggle
- ✅ Responsive design

## 📋 Requirements

**Development:**
- Node.js 18+
- Python 3.10+
- Rust (cargo)
- Visual Studio Build Tools

**End User:**
- Windows 10/11 64-bit
- LDPlayer 9

## 📝 Version History

- **v1.0.0** - Initial release với Tauri UI
