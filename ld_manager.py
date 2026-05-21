"""
LDPlayer Manager - Quản lý và map LDPlayer instances
Thuật toán mapping dựa trên công thức cổng của LDPlayer
"""

import subprocess
import os

# Import config manager
from config_manager import config

# Đường dẫn ADB từ folder tool
ADB_PATH = config.get("adb_path")

# Đường dẫn mặc định của LDPlayer
LDPLAYER_PATH = config.get("ldplayer_path")
LDCONSOLE = os.path.join(LDPLAYER_PATH, "ldconsole.exe")


def set_ldplayer_path(path: str):
    """Cập nhật đường dẫn LDPlayer (không thay đổi ADB_PATH)"""
    global LDPLAYER_PATH, LDCONSOLE
    LDPLAYER_PATH = path
    LDCONSOLE = os.path.join(path, "ldconsole.exe")


def get_adb_devices() -> list:
    """Lấy danh sách các serial ADB đang kết nối"""
    try:
        result = subprocess.run(
            [ADB_PATH, "devices"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        devices = []
        lines = result.stdout.strip().split('\n')[1:]  # Bỏ header
        
        for line in lines:
            if line.strip() and 'device' in line and 'offline' not in line:
                serial = line.split('\t')[0].strip()
                if serial:
                    devices.append(serial)
        
        return devices
    except Exception as e:
        print(f"[LỖI] get_adb_devices: {e}")
        return []


def get_ld_instances() -> list:
    """
    Lấy danh sách LDPlayer instances với mapping ADB serial
    
    Returns:
        List of dict: [
            {
                "index": 0,
                "name": "LDPlayer",
                "running": True,
                "serial": "emulator-5554" or "127.0.0.1:5555" or None
            },
            ...
        ]
    """
    try:
        # Kiểm tra ldconsole tồn tại
        if not os.path.exists(LDCONSOLE):
            print(f"[LỖI] Không tìm thấy ldconsole.exe tại {LDCONSOLE}")
            return []
        
        # Lấy danh sách LD
        result = subprocess.run(
            [LDCONSOLE, "list2"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"[LỖI] ldconsole list2 failed: {result.stderr}")
            return []
        
        # Lấy danh sách ADB
        adb_devices = get_adb_devices()
        
        instances = []
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split(',')
            if len(parts) < 2:
                continue
            
            try:
                idx = int(parts[0])
                
                # Bỏ qua LD có index quá cao (như 99999)
                if idx >= 1000:
                    continue
                
                name = parts[1] if len(parts) > 1 else f"LD-{idx}"
                
                # Kiểm tra trạng thái running
                running = is_ld_running(idx)
                
                # Tính toán serial theo thuật toán mapping
                serial = None
                if running:
                    serial = map_ld_to_serial(idx, adb_devices)
                
                instances.append({
                    "index": idx,
                    "name": name,
                    "running": running,
                    "serial": serial
                })
                
            except (ValueError, IndexError) as e:
                print(f"[CẢNH BÁO] Không parse được dòng: {line} - {e}")
                continue
        
        return instances
        
    except Exception as e:
        print(f"[LỖI] get_ld_instances: {e}")
        return []


def is_ld_running(index: int) -> bool:
    """Kiểm tra LDPlayer có đang chạy không"""
    try:
        result = subprocess.run(
            [LDCONSOLE, "isrunning", "--index", str(index)],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "running" in result.stdout.lower()
    except Exception:
        return False


def map_ld_to_serial(index: int, adb_devices: list) -> str:
    """
    Thuật toán mapping LDPlayer index -> ADB serial
    
    Công thức cổng LDPlayer:
    - Cổng Console: 5554 + (Index * 2)
    - Cổng ADB: 5555 + (Index * 2)
    
    Serial có thể là:
    - emulator-{Console Port} (VD: emulator-5554)
    - 127.0.0.1:{ADB Port} (VD: 127.0.0.1:5555)
    """
    console_port = 5554 + (index * 2)
    adb_port = 5555 + (index * 2)
    
    # Ưu tiên dạng emulator-xxxxx
    emulator_serial = f"emulator-{console_port}"
    if emulator_serial in adb_devices:
        return emulator_serial
    
    # Thử dạng IP
    ip_serial = f"127.0.0.1:{adb_port}"
    if ip_serial in adb_devices:
        return ip_serial
    
    # Không tìm thấy - trả về None
    return None


def launch_ld(index: int) -> bool:
    """Khởi động LDPlayer theo index"""
    try:
        subprocess.Popen(
            [LDCONSOLE, "launch", "--index", str(index)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception as e:
        print(f"[LỖI] launch_ld({index}): {e}")
        return False


def quit_ld(index: int) -> bool:
    """Tắt LDPlayer theo index"""
    try:
        subprocess.run(
            [LDCONSOLE, "quit", "--index", str(index)],
            capture_output=True,
            timeout=10
        )
        return True
    except Exception as e:
        print(f"[LỖI] quit_ld({index}): {e}")
        return False


def get_ld_info_string(instance: dict) -> str:
    """Tạo string hiển thị thông tin LD"""
    status = "Đang chạy" if instance["running"] else "Đã tắt"
    serial = instance["serial"] if instance["serial"] else "N/A"
    return f"{instance['name']} (#{instance['index']}) - {status} - {serial}"


# Test
if __name__ == "__main__":
    print("=== LDPlayer Manager Test ===")
    print(f"LDPlayer Path: {LDPLAYER_PATH}")
    print(f"ADB Path: {ADB_PATH}")
    print()
    
    print("ADB Devices:")
    for d in get_adb_devices():
        print(f"  - {d}")
    print()
    
    print("LDPlayer Instances:")
    for inst in get_ld_instances():
        print(f"  - {get_ld_info_string(inst)}")
