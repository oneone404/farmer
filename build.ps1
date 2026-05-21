# Farmer Build Script
# Build Python backend và Tauri app thành installer

param(
    [switch]$SkipPython,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Building Farmer Application..." -ForegroundColor Cyan

# Paths
$RootDir = $PSScriptRoot
$PythonBackend = Join-Path $RootDir "python-backend"
$TauriResources = Join-Path $RootDir "src-tauri\resources"

# Step 1: Build Python Backend
if (-not $SkipPython) {
    Write-Host "`n📦 Step 1: Building Python Backend..." -ForegroundColor Yellow
    
    Push-Location $PythonBackend
    
    # Install nuitka if needed
    python -m pip install nuitka --quiet
    
    # Build with Nuitka
    Write-Host "   Compiling with Nuitka (this may take a while)..."
    python -m nuitka `
        --standalone `
        --onefile `
        --output-filename=farmer-backend.exe `
        --windows-console-mode=disable `
        --include-data-dir=core=core `
        --include-data-dir=modules=modules `
        --include-data-dir=assets=assets `
        --include-data-dir=adb=adb `
        --include-data-dir=configs=configs `
        server.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Python build failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    # Copy to Tauri resources
    Write-Host "   Copying backend to Tauri resources..."
    New-Item -ItemType Directory -Path $TauriResources -Force | Out-Null
    Copy-Item "farmer-backend.exe" -Destination $TauriResources -Force
    
    Pop-Location
    Write-Host "✅ Python backend built successfully!" -ForegroundColor Green
} else {
    Write-Host "`n⏭ Skipping Python build (--SkipPython)" -ForegroundColor Gray
}

# Step 2: Build Tauri App
Write-Host "`n📦 Step 2: Building Tauri App..." -ForegroundColor Yellow

$BuildArgs = @("run", "tauri", "build")
if ($Debug) {
    $BuildArgs += "--debug"
}

npm @BuildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tauri build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Build completed successfully!" -ForegroundColor Green
Write-Host "   Installer location: src-tauri/target/release/bundle/nsis/" -ForegroundColor Cyan
