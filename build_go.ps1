# Build Script for Farmer (Go Backend)

# 1. Build Go Backend Sidecar
Write-Host "Building Go Backend..." -ForegroundColor Cyan
cd backend-go
$env:GOOS="windows"
$env:GOARCH="amd64"
go build -o ../src-tauri/binaries/backend-x86_64-pc-windows-msvc.exe .
cd ..

# 2. Build Tauri App
Write-Host "Building Tauri App (Installer)..." -ForegroundColor Cyan
npm run tauri build

Write-Host "Build Complete! Check src-tauri/target/release/bundle/nsis for the installer." -ForegroundColor Green
