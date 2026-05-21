"""
Config Manager - Hệ thống cấu hình chuyên nghiệp
Refactored version với class-based design
Data stored in %APPDATA%/Farmer
"""
import json
import os
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


def get_base_path(external: bool = False) -> str:
    """
    Lấy đường dẫn gốc của ứng dụng.
    external=False: Trả về folder chứa code/icon (trong _MEIPASS nếu là EXE).
    external=True: Trả về folder chứa EXE (để lấy assets đi kèm).
    """
    if getattr(sys, 'frozen', False):
        if external:
            return os.path.dirname(os.path.abspath(sys.executable))
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_appdata_path() -> str:
    """
    Lấy đường dẫn AppData cho lưu trữ cấu hình và dữ liệu người dùng.
    Windows: %APPDATA%/Farmer
    """
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    farmer_dir = os.path.join(appdata, 'Farmer')
    os.makedirs(farmer_dir, exist_ok=True)
    return farmer_dir


# Đường dẫn cơ sở
INTERNAL_DIR = get_base_path(external=False)  # Assets, code
EXTERNAL_DIR = get_base_path(external=True)   # EXE location
APPDATA_DIR = get_appdata_path()              # User data, configs
CONFIG_DIR = os.path.join(APPDATA_DIR, "configs")
LOGS_DIR = os.path.join(APPDATA_DIR, "logs")


@dataclass
class ROIConfig:
    """Cấu hình các vùng quét (Region of Interest)"""
    btn_cua_hang: tuple = (1280, 80, 1800, 370)
    btn_open_cua_hang: tuple = (785, 10, 1150, 615)
    btn_open_cua_hang_2: tuple = (1255, 400, 1650, 540)
    panel_check: tuple = (180, 50, 520, 165)
    panel_all: tuple = (200, 160, 380, 1024)
    list: tuple = (610, 150, 1710, 660)
    buy: tuple = (1010, 790, 1380, 1005)
    thu_hoach_all: tuple = (1515, 940, 1900, 1060)
    confirm_th: tuple = (950, 700, 1405, 910)


@dataclass
class ButtonConfig:
    """Cấu hình các nút bấm"""
    buy: tuple = (1240, 910)
    max_qty: tuple = (1228, 683)
    plus: tuple = (1400, 690)
    confirm: tuple = (985, 785)
    close_fruit_1: tuple = (1690, 115)
    close_fruit_2: tuple = (1310, 700)
    panel_voi_select: tuple = (1320, 590)
    open_th_sub: tuple = (770, 395)
    harvest_all: tuple = (1700, 1000)
    close_th: tuple = (1840, 70)
    open_ban_sub: tuple = (1325, 590)
    select_all_produce: tuple = (1245, 955)
    sell: tuple = (1565, 960)
    ok_sell: tuple = (965, 830)
    close_ban: tuple = (1840, 70)


class Config:
    """
    Singleton Config Manager
    Quản lý toàn bộ cấu hình ứng dụng
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._global_config: Dict = {}
        self._instance_configs: Dict[int, Dict] = {}
        
        # Load config
        self._ensure_config_dir()
        self._load_global_config()
        
        # Initialize sub-configs
        self.roi = ROIConfig()
        self.buttons = ButtonConfig()
    
    def _ensure_config_dir(self):
        """Đảm bảo thư mục config tồn tại"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
    
    def _load_global_config(self):
        """Load cấu hình global"""
        config_file = os.path.join(CONFIG_DIR, "global.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._global_config = json.load(f)
            except Exception as e:
                print(f"⚠️ Lỗi load config: {e}")
                self._global_config = self._get_default_global()
        else:
            self._global_config = self._get_default_global()
            self._save_global_config()
    
    def _save_global_config(self):
        """Lưu cấu hình global"""
        config_file = os.path.join(CONFIG_DIR, "global.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._global_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Lỗi lưu config: {e}")
    
    def _get_default_global(self) -> Dict:
        """Lấy cấu hình mặc định"""
        return {
            "adb_path": os.path.join(EXTERNAL_DIR, "adb", "adb.exe"),
            "ldplayer_path": r"C:\LDPlayer\LDPlayer9",
            "use_time_gate": True,
            "first_run_immediate": True,
            "threshold": 0.95,
            "scan_interval": 3,
            "enable_buy_fruits": True,
            "enable_buy_voi": True,
            "enable_harvest_sell": True,
            "harvest_sell_cycles": 1,
            "sell_cycles_after_harvest": 1,
            "scroll_start": [600, 900],
            "scroll_end": [600, 450],
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị config"""
        return self._global_config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set giá trị config và lưu"""
        self._global_config[key] = value
        self._save_global_config()
    
    def load_instance_config(self, ld_index: int) -> Dict:
        """Load cấu hình cho một LDPlayer instance"""
        if ld_index in self._instance_configs:
            return self._instance_configs[ld_index]
        
        config_file = os.path.join(CONFIG_DIR, f"ld_{ld_index}.json")
        default_config = {
            "enabled": True,
            "use_time_gate": True,
            "first_run_immediate": True,
            "threshold": 0.95,
            "enable_buy_fruits": True,
            "enable_buy_voi": True,
            "enable_harvest_sell": True,
            "harvest_sell_cycles": 1,
            "sell_cycles_after_harvest": 1,
            "fruits": {}
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self._instance_configs[ld_index] = {**default_config, **config}
            except:
                self._instance_configs[ld_index] = default_config
        else:
            self._instance_configs[ld_index] = default_config
        
        return self._instance_configs[ld_index]
    
    def save_instance_config(self, ld_index: int, config: Dict) -> bool:
        """Lưu cấu hình cho một LDPlayer instance"""
        config_file = os.path.join(CONFIG_DIR, f"ld_{ld_index}.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self._instance_configs[ld_index] = config
            return True
        except Exception as e:
            print(f"❌ Lỗi lưu instance config: {e}")
            return False
    
    def get_fruits(self) -> Dict:
        """Lấy danh sách trái cây và đường dẫn ảnh"""
        return {
            "Dâu Tây": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_dau_tay.png"), "buy": True},
            "Cà Rốt": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_ca_rot.png"), "buy": True},
            "Mảng Cầu": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_mang_cau.png"), "buy": True},
            "Bí Ngô": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_bi_ngo.png"), "buy": True},
            "Dưa Hấu": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_dua_hau.png"), "buy": True},
            "Đu Đủ": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_du_du.png"), "buy": True},
            "Khế": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_khe.png"), "buy": True},
            "Táo Đường": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_tao_duong.png"), "buy": True},
            "Xoài": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_xoai.png"), "buy": True},
            "Nho": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_nho.png"), "buy": True},
            "Đậu": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_dau.png"), "buy": True},
            "Dừa": {"img": os.path.join(INTERNAL_DIR, "assets", "fruits", "fruit_dua.png"), "buy": True},
        }
    
    def get_instance_fruits(self, ld_index: int) -> Dict:
        """Lấy cấu hình trái cây của một instance"""
        config = self.load_instance_config(ld_index)
        return config.get("fruits", {})
    
    def get_template_path(self, name: str) -> str:
        """Lấy đường dẫn template"""
        templates = {
            "panel_buy": os.path.join(INTERNAL_DIR, "assets", "templates", "panel_buy.png"),
            "sold_out": os.path.join(INTERNAL_DIR, "assets", "templates", "sold_out.png"),
            "sold_out_list": os.path.join(INTERNAL_DIR, "assets", "templates", "sold_out_list.png"),
            "voi_sieu_cap": os.path.join(INTERNAL_DIR, "assets", "templates", "voi_sieu_cap.png"),
        }
        return templates.get(name, "")
    
    def get_button_path(self, name: str) -> str:
        """Lấy đường dẫn ảnh nút"""
        buttons = {
            "cua_hang": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_cua_hang.png"),
            "open_cua_hang": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_open_cua_hang.png"),
            "open_cua_hang_2": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_open_cua_hang2.png"),
            "cua_hang_voi": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_cua_hang_voi.png"),
            "open_cua_hang_voi": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_open_cua_hang_voi.png"),
            "ve_nha": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_ve_nha.png"),
            "panel_th": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_panel_thu_hoach.png"),
            "thu_hoach_all": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_thu_hoach_all.png"),
            "ban_fruit": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_ban_fruit.png"),
            "open_ban_fruit": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_open_ban_fruit.png"),
            "xac_nhan": os.path.join(INTERNAL_DIR, "assets", "buttons", "btn_xac_nhan.png"),
        }
        return buttons.get(name, "")


# Singleton instance
config = Config()
