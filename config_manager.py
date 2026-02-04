"""
Config Manager - Hệ thống cấu hình chuyên nghiệp dùng JSON
Hỗ trợ hot-reload và cấu hình riêng cho từng LDPlayer
"""

import json
import os
import sys
from typing import Dict, Any, Optional

# Đường dẫn
if getattr(sys, 'frozen', False):
    # Đường dẫn nơi chứa file .exe thực tế
    EXE_DIR = os.path.dirname(sys.executable)
    # Đường dẫn nơi giải nén các file bundle của PyInstaller
    BUNDLE_DIR = sys._MEIPASS
else:
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = EXE_DIR

# Config và ADB luôn nằm cùng thư mục với file chạy (.exe hoặc .py)
CONFIG_DIR = os.path.join(EXE_DIR, "configs")
GLOBAL_CONFIG_FILE = os.path.join(CONFIG_DIR, "global.json")

# Assets được bundle bên trong EXE (để không bị mất icon/template)
ASSETS_DIR = os.path.join(BUNDLE_DIR, "assets")

# ================= DEFAULT CONFIG =================

DEFAULT_GLOBAL_CONFIG = {
    # ADB
    "adb_path": os.path.join(EXE_DIR, "adb", "adb.exe"),
    
    # LDPlayer
    "ldplayer_path": r"C:\LDPlayer\LDPlayer9",
    
    # Telegram
    "telegram_token": "",
    "telegram_id": "",
    "enable_telegram": False,
    
    # Timing
    "use_time_gate": True,
    "first_run_immediate": True,
    "threshold": 0.9,
    "scan_interval": 3,
    
    # Modules
    "enable_buy_fruits": True,
    "enable_buy_voi": True,
    "enable_harvest_sell": True,
    
    # ROI (Region of Interest)
    "roi_btn_cua_hang": [1280, 80, 1800, 370],
    "roi_btn_open_cua_hang": [785, 10, 1150, 615],
    "roi_btn_open_cua_hang_2": [1255, 400, 1650, 540],
    "roi_panel_check": [180, 50, 520, 165],
    "roi_panel_all": [200, 160, 380, 1024],
    "roi_list": [610, 150, 1710, 660],
    "roi_buy": [1010, 790, 1380, 1005],
    "roi_thu_hoach_all": [1515, 940, 1900, 1060],
    "roi_confirm_th": [950, 700, 1405, 910],
    
    # Buttons
    "buy_btn": [1240, 910],
    "max_qty_btn": [1228, 683],
    "plus_btn": [1400, 690],
    "confirm_btn": [985, 785],
    "close_fruit_btn_1": [1690, 115],
    "close_fruit_btn_2": [1310, 700],
    "panel_voi_select_btn": [1320, 590],
    "open_th_sub": [770, 395],
    "harvest_all_btn": [1700, 1000],
    "close_th_btn": [1840, 70],
    "open_ban_sub": [1325, 590],
    "select_all_produce_btn": [1245, 955],
    "sell_btn": [1565, 960],
    "ok_sell_btn": [965, 830],
    "close_ban_btn": [1840, 70],
    
    # Constants
    "harvest_sell_cycles": 2,
    "sell_cycles_after_harvest": 2,
    "total_fruits_to_check": 11,
    
    # Scroll
    "scroll_start": [600, 900],
    "scroll_end": [600, 450],
    
    # Images
    "panel_buy_img": os.path.join(ASSETS_DIR, "templates", "panel_buy.png"),
    "sold_out_img": os.path.join(ASSETS_DIR, "templates", "sold_out.png"),
    "btn_cua_hang_img": os.path.join(ASSETS_DIR, "buttons", "btn_cua_hang.png"),
    "btn_open_cua_hang_img": os.path.join(ASSETS_DIR, "buttons", "btn_open_cua_hang.png"),
    "btn_open_cua_hang_2_img": os.path.join(ASSETS_DIR, "buttons", "btn_open_cua_hang2.png"),
    "sold_out_list_img": os.path.join(ASSETS_DIR, "templates", "sold_out_list.png"),
    
    # Vòi
    "btn_cua_hang_voi_img": os.path.join(ASSETS_DIR, "buttons", "btn_cua_hang_voi.png"),
    "btn_open_cua_hang_voi_img": os.path.join(ASSETS_DIR, "buttons", "btn_open_cua_hang_voi.png"),
    "voi_sieu_cap_img": os.path.join(ASSETS_DIR, "templates", "voi_sieu_cap.png"),
    
    # Thu hoạch
    "btn_ve_nha_img": os.path.join(ASSETS_DIR, "buttons", "btn_ve_nha.png"),
    "btn_panel_th_img": os.path.join(ASSETS_DIR, "buttons", "btn_panel_thu_hoach.png"),
    "btn_thu_hoach_all_img": os.path.join(ASSETS_DIR, "buttons", "btn_thu_hoach_all.png"),
    "btn_ban_fruit_img": os.path.join(ASSETS_DIR, "buttons", "btn_ban_fruit.png"),
    "btn_open_ban_fruit_img": os.path.join(ASSETS_DIR, "buttons", "btn_open_ban_fruit.png"),
    "btn_xac_nhan_img": os.path.join(ASSETS_DIR, "buttons", "btn_xac_nhan.png"),
}

DEFAULT_INSTANCE_CONFIG = {
    "enabled": True,
    "use_time_gate": True,
    "first_run_immediate": True,
    "threshold": 0.8,
    "enable_buy_fruits": True,
    "enable_buy_voi": True,
    "enable_harvest_sell": True,
    "enable_telegram": False,
    "fruits": {}  # {"Dâu Tây": True, "Cà Rốt": False, ...}
}

# Danh sách trái cây mặc định
DEFAULT_FRUITS = {
    "Dâu Tây": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_dau_tay.png"), "buy": True},
    "Cà Rốt": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_ca_rot.png"), "buy": True},
    "Bí Ngô": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_bi_ngo.png"), "buy": True},
    "Dưa Hấu": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_dua_hau.png"), "buy": True},
    "Cổ Đại": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_co_dai.png"), "buy": True},
    "Khế": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_khe.png"), "buy": True},
    "Táo Đường": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_tao_duong.png"), "buy": True},
    "Xoài": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_xoai.png"), "buy": True},
    "Nho": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_nho.png"), "buy": True},
    "Dâu": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_dau.png"), "buy": True},
    "Dưa": {"img": os.path.join(ASSETS_DIR, "fruits", "fruit_dua.png"), "buy": True},
}

SCALES = [1.0]  # Tối ưu tốc độ: chỉ dùng 1 tỷ lệ duy nhất


class ConfigManager:
    """Singleton class để quản lý config"""
    
    _instance = None
    _global_config: Dict[str, Any] = None
    _instance_configs: Dict[int, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """Khởi tạo config manager"""
        self._ensure_config_dir()
        self._global_config = self._load_global_config()
    
    def _ensure_config_dir(self):
        """Tạo thư mục configs nếu chưa có"""
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
    
    # ================= GLOBAL CONFIG =================
    
    def _load_global_config(self) -> Dict[str, Any]:
        """Load global config từ file, merge với default"""
        config = DEFAULT_GLOBAL_CONFIG.copy()
        
        if os.path.exists(GLOBAL_CONFIG_FILE):
            try:
                with open(GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    config.update(saved)
            except Exception as e:
                print(f"[CONFIG] Lỗi load global config: {e}")
        
        return config
    
    def save_global_config(self) -> bool:
        """Lưu global config ra file"""
        try:
            self._ensure_config_dir()
            with open(GLOBAL_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._global_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[CONFIG] Lỗi save global config: {e}")
            return False
    
    def reload_global_config(self):
        """Reload global config từ file"""
        self._global_config = self._load_global_config()
    
    def get(self, key: str, default=None):
        """Lấy giá trị từ global config"""
        return self._global_config.get(key, default)
    
    def set(self, key: str, value):
        """Đặt giá trị trong global config"""
        self._global_config[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Lấy toàn bộ global config"""
        return self._global_config.copy()
    
    # ================= INSTANCE CONFIG =================
    
    def _get_instance_config_path(self, ld_index: int) -> str:
        return os.path.join(CONFIG_DIR, f"ld_{ld_index}.json")
    
    def load_instance_config(self, ld_index: int) -> Dict[str, Any]:
        """Load config cho 1 LD instance"""
        # Check cache
        if ld_index in self._instance_configs:
            return self._instance_configs[ld_index].copy()
        
        config = DEFAULT_INSTANCE_CONFIG.copy()
        config_path = self._get_instance_config_path(ld_index)
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    config.update(saved)
            except Exception as e:
                print(f"[CONFIG] Lỗi load config LD-{ld_index}: {e}")
        
        # Cache
        self._instance_configs[ld_index] = config
        return config.copy()
    
    def save_instance_config(self, ld_index: int, config: Dict[str, Any]) -> bool:
        """Lưu config cho 1 LD instance"""
        try:
            self._ensure_config_dir()
            config_path = self._get_instance_config_path(ld_index)
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # Update cache
            self._instance_configs[ld_index] = config.copy()
            return True
        except Exception as e:
            print(f"[CONFIG] Lỗi save config LD-{ld_index}: {e}")
            return False
    
    def reload_instance_config(self, ld_index: int):
        """Reload config cho 1 LD từ file"""
        if ld_index in self._instance_configs:
            del self._instance_configs[ld_index]
        return self.load_instance_config(ld_index)
    
    def get_instance_value(self, ld_index: int, key: str, default=None):
        """Lấy 1 giá trị từ instance config"""
        config = self.load_instance_config(ld_index)
        return config.get(key, default)
    
    def set_instance_value(self, ld_index: int, key: str, value):
        """Đặt 1 giá trị trong instance config"""
        config = self.load_instance_config(ld_index)
        config[key] = value
        self.save_instance_config(ld_index, config)
    
    # ================= FRUITS CONFIG =================
    
    def get_fruits(self) -> Dict[str, Dict]:
        """Lấy danh sách trái cây từ global config hoặc default"""
        return self._global_config.get("fruits", DEFAULT_FRUITS.copy())
    
    def get_instance_fruits(self, ld_index: int) -> Dict[str, bool]:
        """Lấy config trái cây cho 1 LD instance"""
        config = self.load_instance_config(ld_index)
        fruits = config.get("fruits", {})
        
        # Nếu chưa có config fruits, dùng default từ FRUITS
        if not fruits:
            for name, data in DEFAULT_FRUITS.items():
                fruits[name] = data.get("buy", True)
        
        return fruits
    
    def get_enabled_fruits_for_instance(self, ld_index: int) -> Dict[str, Dict]:
        """Lấy danh sách trái cây được bật cho 1 LD (dùng trong main.py)"""
        all_fruits = self.get_fruits()
        instance_fruits = self.get_instance_fruits(ld_index)
        
        enabled = {}
        for name, data in all_fruits.items():
            if instance_fruits.get(name, True):
                enabled[name] = data
        
        return enabled


# Singleton instance
config = ConfigManager()


# ================= BACKWARD COMPATIBILITY =================
# Các hằng số để tương thích với code cũ

def get_adb_path():
    return config.get("adb_path")

def get_ldplayer_path():
    return config.get("ldplayer_path")

def get_threshold():
    return config.get("threshold", 0.8)

def get_roi(name: str):
    return tuple(config.get(f"roi_{name}", [0, 0, 0, 0]))

def get_button(name: str):
    return tuple(config.get(f"{name}_btn", [0, 0]))


# ================= QUICK ACCESS =================
# Export các giá trị thường dùng

ADB_PATH = config.get("adb_path")
LDPLAYER_PATH = config.get("ldplayer_path")
THRESHOLD = config.get("threshold", 0.8)
FRUITS = config.get_fruits()


if __name__ == "__main__":
    print("=== Config Manager Test ===")
    print(f"ADB Path: {config.get('adb_path')}")
    print(f"LDPlayer Path: {config.get('ldplayer_path')}")
    print(f"Threshold: {config.get('threshold')}")
    print(f"Fruits: {list(config.get_fruits().keys())}")
    
    print("\n--- Test Instance Config ---")
    cfg = config.load_instance_config(0)
    print(f"LD-0 config: {cfg}")
    
    cfg["threshold"] = 0.85
    config.save_instance_config(0, cfg)
    print("Saved!")
    
    cfg2 = config.reload_instance_config(0)
    print(f"Reloaded: threshold = {cfg2['threshold']}")
