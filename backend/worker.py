"""
Farmer Worker - Worker process xử lý automation
Đã refactored với cấu trúc module chuyên nghiệp
"""
import sys
import os
import time
import gc
import functools

# Fix encoding cho Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Đảm bảo print luôn flush ngay lập tức
print = functools.partial(print, flush=True)

# Import core modules
from core.config import config
from core.adb_controller import ADBController
from core.image_processor import ImageProcessor

# Import business modules
from modules.buy_fruits import BuyFruitsModule
from modules.buy_voi import BuyVoiModule
from modules.harvest_sell import HarvestSellModule


def wait_for_next_cycle():
    """Wait for the next 5-minute time gate"""
    while True:
        now = time.localtime()
        if now.tm_min % 5 == 0 and now.tm_sec < 10:
            print(f"[WORKER] Time gate reached ({now.tm_hour}:{now.tm_min:02d}). Starting cycle...")
            break
        time.sleep(5)



def now_str():
    return time.strftime("%H:%M:%S", time.localtime())


def main():
    """Main worker function"""
    # Lấy arguments
    device_serial = sys.argv[1] if len(sys.argv) > 1 else None
    ld_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    if not device_serial:
        print("[WORKER] Error: Missing device serial")
        return
    
    print(f"[WORKER] Farmer v6.0 Initialized")
    print(f"[WORKER] Device: {device_serial} | Index: {ld_index}")
    
    # Load instance config
    instance_config = config.load_instance_config(ld_index)
    
    # Khởi tạo controllers
    adb = ADBController(config.get("adb_path"), device_serial)
    threshold = instance_config.get("threshold", config.get("threshold", 0.9))
    img = ImageProcessor(threshold=threshold)
    
    # Khởi tạo modules
    buy_fruits = BuyFruitsModule(adb, img, config, instance_config)
    buy_voi = BuyVoiModule(adb, img, config, instance_config)
    harvest_sell = HarvestSellModule(adb, img, config, instance_config)
    
    # Config flags
    USE_TIME_GATE = instance_config.get("use_time_gate", config.get("use_time_gate", True))
    ENABLE_FIRST_RUN_IMMEDIATE = instance_config.get("first_run_immediate", True)
    ENABLE_BUY_FRUITS = instance_config.get("enable_buy_fruits", True)
    ENABLE_BUY_VOI = instance_config.get("enable_buy_voi", True)
    ENABLE_HARVEST_SELL = instance_config.get("enable_harvest_sell", True)
    SCAN_INTERVAL = config.get("scan_interval", 3)
    
    first_run = ENABLE_FIRST_RUN_IMMEDIATE
    is_init_run = ENABLE_FIRST_RUN_IMMEDIATE
    
    print(f"[WORKER] Monitoring {len(buy_fruits.fruits)} fruits")
    
    while True:
        if USE_TIME_GATE:
            if first_run:
                print("[WORKER] First run initiated")
                first_run = False
            else:
                wait_for_next_cycle()
        
        now = time.localtime()
        
        # Xác định thời điểm chạy các module
        if USE_TIME_GATE:
            is_voi_time = (now.tm_min % 30 == 0) or is_init_run
            is_harvest_time = (now.tm_min == 0) or is_init_run
        else:
            is_voi_time = True
            is_harvest_time = True
        
        is_init_run = False
        
        # ================= MODULE MUA TRÁI =================
        if not ENABLE_BUY_FRUITS:
            print("[WORKER] Fruits module disabled")
        else:
            result = buy_fruits.run()
            # Đóng panel sau khi mua xong (chỉ khi cần mở panel vòi)
            if is_voi_time and ENABLE_BUY_VOI:
                buy_fruits.close_panel()
        
        # ================= MODULE VÒI (30 PHÚT) =================
        if is_voi_time:
            if not ENABLE_BUY_VOI:
                print("[WORKER] Sprinkler module disabled")
            else:
                result = buy_voi.run()
        
        # ================= MODULE THU HOẠCH & BÁN (1 TIẾNG) =================
        if is_harvest_time:
            if not ENABLE_HARVEST_SELL:
                print("[WORKER] Harvest & Sell module disabled")
            else:
                result = harvest_sell.run()
        
        print("[WORKER] Cycle complete. Waiting...")
        gc.collect()
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
