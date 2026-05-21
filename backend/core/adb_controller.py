"""
ADB Controller - Điều khiển thiết bị qua ADB
"""
import subprocess
import os
import time
import functools

# Đảm bảo print luôn flush
print = functools.partial(print, flush=True)


class ADBController:
    """Class điều khiển ADB cho một thiết bị cụ thể"""
    
    def __init__(self, adb_path: str, device_serial: str = None):
        self.adb_path = adb_path
        self.device_serial = device_serial
        self._creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    
    def _run_cmd(self, args: list, timeout: int = 10) -> subprocess.CompletedProcess:
        """Chạy lệnh ADB"""
        cmd = [self.adb_path]
        if self.device_serial:
            cmd += ["-s", self.device_serial]
        cmd += args
        
        return subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            creationflags=self._creationflags
        )
    
    def screencap(self) -> bytes:
        """Chụp màn hình, trả về bytes của ảnh PNG"""
        try:
            result = self._run_cmd(["exec-out", "screencap", "-p"], timeout=5)
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception as e:
            print(f"❌ Lỗi screencap: {e}")
        return None
    
    def tap(self, x: int, y: int):
        """Tap vào tọa độ (x, y)"""
        try:
            self._run_cmd(["shell", "input", "tap", str(x), str(y)], timeout=3)
        except Exception as e:
            print(f"❌ Lỗi tap: {e}")
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Vuốt từ (x1, y1) đến (x2, y2)"""
        try:
            self._run_cmd([
                "shell", "input", "swipe",
                str(x1), str(y1), str(x2), str(y2), str(duration)
            ], timeout=5)
        except Exception as e:
            print(f"❌ Lỗi swipe: {e}")
    
    def get_devices(self) -> list:
        """Lấy danh sách thiết bị đang kết nối"""
        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=self._creationflags
            )
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip() and 'device' in line and 'offline' not in line:
                    serial = line.split('\t')[0].strip()
                    if serial:
                        devices.append(serial)
            return devices
        except Exception as e:
            print(f"❌ Lỗi get_devices: {e}")
            return []
