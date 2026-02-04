import cv2
import subprocess
import time
import requests
import os
import sys
import gc  # Garbage collection để giải phóng RAM
import numpy as np

# Fix encoding cho Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Import config manager
from config_manager import config, FRUITS, DEFAULT_FRUITS, SCALES

# Lấy device serial và LD index từ arguments
DEVICE_SERIAL = sys.argv[1] if len(sys.argv) > 1 else None
LD_INDEX = int(sys.argv[2]) if len(sys.argv) > 2 else 0

# Load config cho LD instance này
instance_config = config.load_instance_config(LD_INDEX)

# Các biến config (từ instance hoặc global)
ADB_PATH = config.get("adb_path")
THRESHOLD = instance_config.get("threshold", config.get("threshold", 0.8))
USE_TIME_GATE = instance_config.get("use_time_gate", config.get("use_time_gate", True))
ENABLE_FIRST_RUN_IMMEDIATE = instance_config.get("first_run_immediate", True)
ENABLE_BUY_FRUITS = instance_config.get("enable_buy_fruits", True)
ENABLE_BUY_VOI = instance_config.get("enable_buy_voi", True)
ENABLE_HARVEST_SELL = instance_config.get("enable_harvest_sell", True)
ENABLE_TELEGRAM = instance_config.get("enable_telegram", False)

# ROI config
ROI_BTN_CUA_HANG = tuple(config.get("roi_btn_cua_hang", [1280, 80, 1800, 370]))
ROI_BTN_OPEN_CUA_HANG = tuple(config.get("roi_btn_open_cua_hang", [785, 10, 1150, 615]))
ROI_BTN_OPEN_CUA_HANG_2 = tuple(config.get("roi_btn_open_cua_hang_2", [1255, 400, 1650, 540]))
ROI_PANEL_CHECK = tuple(config.get("roi_panel_check", [180, 50, 520, 165]))
ROI_PANEL_ALL = tuple(config.get("roi_panel_all", [200, 160, 380, 1024]))
ROI_LIST = tuple(config.get("roi_list", [610, 150, 1710, 660]))
ROI_BUY = tuple(config.get("roi_buy", [1010, 790, 1380, 1005]))
ROI_THU_HOACH_ALL = tuple(config.get("roi_thu_hoach_all", [1515, 940, 1900, 1060]))
ROI_CONFIRM_TH = tuple(config.get("roi_confirm_th", [950, 700, 1405, 910]))

# Button config
BUY_BTN = tuple(config.get("buy_btn", [1240, 910]))
MAX_QTY_BTN = tuple(config.get("max_qty_btn", [1228, 683]))
CONFIRM_BTN = tuple(config.get("confirm_btn", [985, 785]))
CLOSE_FRUIT_BTN_1 = tuple(config.get("close_fruit_btn_1", [1690, 115]))
CLOSE_FRUIT_BTN_2 = tuple(config.get("close_fruit_btn_2", [1310, 700]))
PANEL_VOI_SELECT_BTN = tuple(config.get("panel_voi_select_btn", [1320, 590]))
OPEN_TH_SUB = tuple(config.get("open_th_sub", [770, 395]))
HARVEST_ALL_BTN = tuple(config.get("harvest_all_btn", [1700, 1000]))
CLOSE_TH_BTN = tuple(config.get("close_th_btn", [1840, 70]))
OPEN_BAN_SUB = tuple(config.get("open_ban_sub", [1325, 590]))
SELECT_ALL_PRODUCE = tuple(config.get("select_all_produce_btn", [1245, 955]))
SELL_BTN = tuple(config.get("sell_btn", [1565, 960]))
OK_SELL_BTN = tuple(config.get("ok_sell_btn", [965, 830]))
CLOSE_BAN_BTN = tuple(config.get("close_ban_btn", [1840, 70]))

# Constants
SCAN_INTERVAL = config.get("scan_interval", 3)
HARVEST_SELL_CYCLES = config.get("harvest_sell_cycles", 2)
SELL_CYCLES_AFTER_HARVEST = config.get("sell_cycles_after_harvest", 2)
TOTAL_FRUITS_TO_CHECK = config.get("total_fruits_to_check", 11)

# Scroll config
SCROLL_START = tuple(config.get("scroll_start", [600, 900]))
SCROLL_END = tuple(config.get("scroll_end", [600, 450]))

# Image paths
PANEL_BUY_IMG = config.get("panel_buy_img", "assets/templates/panel_buy.png")
SOLD_OUT_IMG = config.get("sold_out_img", "assets/templates/sold_out.png")
BTN_CUA_HANG_IMG = config.get("btn_cua_hang_img", "assets/buttons/btn_cua_hang.png")
BTN_OPEN_CUA_HANG_IMG = config.get("btn_open_cua_hang_img", "assets/buttons/btn_open_cua_hang.png")
BTN_OPEN_CUA_HANG_2_IMG = config.get("btn_open_cua_hang_2_img", "assets/buttons/btn_open_cua_hang2.png")
SOLD_OUT_LIST_IMG = config.get("sold_out_list_img", "assets/templates/sold_out_list.png")
BTN_CUA_HANG_VOI_IMG = config.get("btn_cua_hang_voi_img", "assets/buttons/btn_cua_hang_voi.png")
BTN_OPEN_CUA_HANG_VOI_IMG = config.get("btn_open_cua_hang_voi_img", "assets/buttons/btn_open_cua_hang_voi.png")
VOI_SIEU_CAP_IMG = config.get("voi_sieu_cap_img", "assets/templates/voi_sieu_cap.png")
BTN_VE_NHA_IMG = config.get("btn_ve_nha_img", "assets/buttons/btn_ve_nha.png")
BTN_PANEL_TH_IMG = config.get("btn_panel_th_img", "assets/buttons/btn_panel_thu_hoach.png")
BTN_THU_HOACH_ALL_IMG = config.get("btn_thu_hoach_all_img", "assets/buttons/btn_thu_hoach_all.png")
BTN_BAN_FRUIT_IMG = config.get("btn_ban_fruit_img", "assets/buttons/btn_ban_fruit.png")
BTN_OPEN_BAN_FRUIT_IMG = config.get("btn_open_ban_fruit_img", "assets/buttons/btn_open_ban_fruit.png")
BTN_XAC_NHAN_IMG = config.get("btn_xac_nhan_img", "assets/buttons/btn_xac_nhan.png")

# Telegram config
TELEGRAM_TOKEN = config.get("telegram_token", "")
TELEGRAM_ID = config.get("telegram_id", "")

# ================= UTILS =================
def adb(cmd):
    base_cmd = [ADB_PATH]
    if DEVICE_SERIAL:
        base_cmd += ["-s", DEVICE_SERIAL]
    subprocess.run(base_cmd + cmd,
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

def tap(x, y):
    adb(["shell", "input", "tap", str(x), str(y)])

def swipe(x1, y1, x2, y2):
    adb(["shell", "input", "swipe",
         str(x1), str(y1), str(x2), str(y2), "300"])

def screencap():
    # ⚡ CẢI TIẾN: Dùng exec-out để truyền dữ liệu binary thuần túy mã không bị hỏng
    try:
        # 'exec-out' giúp tránh lỗi tự động đổi \n thành \r\n trên Windows
        base_cmd = [ADB_PATH]
        if DEVICE_SERIAL:
            base_cmd += ["-s", DEVICE_SERIAL]
        base_cmd += ["exec-out", "screencap", "-p"]
        process = subprocess.Popen(base_cmd, stdout=subprocess.PIPE)
        binary_data, _ = process.communicate()
        
        if not binary_data:
            return None
            
        nparr = np.frombuffer(binary_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"[LOI] Loi chup man hinh (RAM): {e}")
        return None

def crop(img, roi):
    if img is None: return None
    x1, y1, x2, y2 = roi
    # Đảm bảo tọa độ không vượt quá kích thước ảnh
    h, w = img.shape[:2]
    if h == 0 or w == 0: return None
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
    # Kiểm tra ROI hợp lệ
    if x2 <= x1 or y2 <= y1: return None
    cropped = img[y1:y2, x1:x2]
    if cropped.size == 0: return None
    return cropped

def match_with_loc(img, pre_tpls, use_color=False):
    # Kiểm tra ảnh rỗng
    if img is None: return 0, (0, 0), (0, 0)
    if img.size == 0: return 0, (0, 0), (0, 0)
    if len(img.shape) < 2: return 0, (0, 0), (0, 0)
    
    # Nếu dùng màu thì giữ nguyên img, nếu ko thì chuyển xám
    try:
        img_proc = img if use_color else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    except cv2.error:
        return 0, (0, 0), (0, 0)
    
    ih, iw = img_proc.shape[:2]
    if ih == 0 or iw == 0: return 0, (0, 0), (0, 0)
    
    best, best_loc, best_size = 0, None, None

    for (rs, (tw, th)) in pre_tpls:
        if ih < th or iw < tw: continue
        
        res = cv2.matchTemplate(img_proc, rs, cv2.TM_CCOEFF_NORMED)
        _, val, _, loc = cv2.minMaxLoc(res)
        
        if val > best:
            best = val
            best_loc = loc
            best_size = (tw, th)
            
    return best, best_loc, best_size

def wait_for_img(tpls, roi, timeout=5, interval=0.5, use_color=False):
    """Đợi ảnh xuất hiện trong ROI, trả về tọa độ nếu thấy, None nếu hết timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        screen = screencap()
        if screen is None: 
            time.sleep(interval)
            continue
        crop_img = crop(screen, roi)
        if crop_img is None:
            time.sleep(interval)
            continue
        val, loc, size = match_with_loc(crop_img, tpls, use_color=use_color)
        if val >= THRESHOLD:
            cx = roi[0] + loc[0] + size[0]//2
            cy = roi[1] + loc[1] + size[1]//2
            return (cx, cy)
        time.sleep(interval)
    return None

def pre_process_tpl(img, name, use_color=False):
    if img is None:
        print(f"❌ Không tìm thấy file template: {name}")
        return []
    
    # Chuyển xám nếu cần
    img_proc = img if use_color else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    results = []
    for scale in SCALES:
        tw, th = int(img_proc.shape[1] * scale), int(img_proc.shape[0] * scale)
        if tw < 5 or th < 5: continue
        rs = cv2.resize(img_proc, (tw, th))
        results.append((rs, (tw, th)))
    return results

def wait_for_next_cycle():
    while True:
        now = time.localtime()
        # Chờ đến phút chia hết cho 5
        if now.tm_min % 5 == 0 and now.tm_sec < 10:
            print(f"⏰ [Cửa hàng] Đã đến mốc thời gian: {now.tm_hour}:{now.tm_min:02d}. Chạy...")
            break
        
        time.sleep(5)
        print(f"⏳ Đợi mốc phút 0 / 5 / 10 ... (Hiện tại: {now.tm_hour}:{now.tm_min:02d}:{now.tm_sec:02d})", end='\r')

def now_str():
    return time.strftime("%H:%M:%S", time.localtime())

def send_tele(text):
    if not ENABLE_TELEGRAM:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        print("❌ Lỗi gửi Telegram")

def format_result(available):
    if not available: return None
    body = "\n".join([f"✅ <b>{fruit}</b>" for fruit in available])
    return f"⏱ <i>{now_str()}</i>\n\n📌 <b>CÒN HÀNG:</b>\n{body}"

def ensure_panel_buy_open(panel_tpl, btn_cua_hang_tpl, btn_open_tpl, btn_open_tpl2):
    # 1. Check xem bảng Buy đã mở sẵn chưa
    screen = screencap()
    if screen is None:
        return False
    # ⚡ Dùng ROI nhỏ thay vì toàn màn hình để tiết kiệm RAM
    panel_check = crop(screen, ROI_PANEL_CHECK)
    val, _, _ = match_with_loc(panel_check, panel_tpl)
    del panel_check  # ⚡ Giải phóng RAM
    del screen
    gc.collect()  # ⚡ Thu gom rác
    if val >= THRESHOLD:
        print("✅ Panel BUY đang mở.")
        return True
    
    print("⚠️ Panel BUY đang tắt → tìm nút Cửa Hàng")
    
    # 2. Tìm btn_cua_hang 
    pos = wait_for_img(btn_cua_hang_tpl, ROI_BTN_CUA_HANG, timeout=6)
    if pos:
        print("🛒 Thấy nút Cửa Hàng, đang nhấn...")
        tap(*pos)
    else:
        print("❌ Không tìm thấy btn_cua_hang")
        return False
        
    # ===== Đợi và tìm btn_open_cua_hang (Open 1) =====
    pos1 = wait_for_img(btn_open_tpl, ROI_BTN_OPEN_CUA_HANG, timeout=6)
    if pos1:
        print("✨ Thấy nút OPEN, đang nhấn...")
        tap(*pos1)
    else:
        print("❌ Không thấy nút Open 1")
        return False
        
    # ===== Đợi và tìm btn_open_cua_hang2 (Open 2) =====
    pos2 = wait_for_img(btn_open_tpl2, ROI_BTN_OPEN_CUA_HANG_2, timeout=6)
    if pos2:
        print("✨ Thấy nút OPEN 2, đang nhấn...")
        tap(*pos2)
        time.sleep(1) # Load bảng trái cây
        return True
    else:
        print("❌ Không thấy nút Open 2")
        return False

def scroll_to_top():
    print("🔝 Đang cuộn lên đỉnh...")
    for _ in range(3):
        adb(["shell", "input", "swipe", "600", "400", "600", "1000", "200"])
        time.sleep(0.5)

def ensure_panel_voi_open(btn_voi_tpl, btn_open_voi_tpl):
    # Tìm btn_voi_trong_cua_hang
    pos = wait_for_img(btn_voi_tpl, ROI_BTN_CUA_HANG, timeout=6)
    if pos:
        print("🚿 Thấy nút Shop Vòi, đang nhấn...")
        tap(*pos)
    else:
        print("❌ Không tìm thấy Shop Vòi")
        return False
        
    # ===== Đợi và tìm btn_open_voi =====
    pos_open = wait_for_img(btn_open_voi_tpl, ROI_BTN_OPEN_CUA_HANG, timeout=6)
    if pos_open:
        print("✨ Thấy nút OPEN Vòi, đang nhấn...")
        tap(*pos_open)
        time.sleep(1.5)
        # Ấn vào tab vòi
        tap(*PANEL_VOI_SELECT_BTN)
        time.sleep(1)
        return True
    else:
        print("❌ Không thấy OPEN Vòi")
        return False

# ================= MAIN =================
def main():
    print("🚀 TOOL OPTIMIZED (V4) - PRE-PROCESSED TEMPLATES")
    
    # Pre-process hệ thống (Dùng Grayscale cho nhanh)
    sold_tpl = pre_process_tpl(cv2.imread(SOLD_OUT_IMG), SOLD_OUT_IMG, use_color=False)
    sold_list_tpl = pre_process_tpl(cv2.imread(SOLD_OUT_LIST_IMG), SOLD_OUT_LIST_IMG, use_color=False)
    panel_tpl = pre_process_tpl(cv2.imread(PANEL_BUY_IMG), PANEL_BUY_IMG, use_color=False)
    btn_cua_hang_tpl = pre_process_tpl(cv2.imread(BTN_CUA_HANG_IMG), BTN_CUA_HANG_IMG, use_color=False)
    btn_open_tpl = pre_process_tpl(cv2.imread(BTN_OPEN_CUA_HANG_IMG), BTN_OPEN_CUA_HANG_IMG, use_color=False)
    btn_open_tpl2 = pre_process_tpl(cv2.imread(BTN_OPEN_CUA_HANG_2_IMG), BTN_OPEN_CUA_HANG_2_IMG, use_color=False)
    
    # Pre-process Vòi
    btn_voi_tpl = pre_process_tpl(cv2.imread(BTN_CUA_HANG_VOI_IMG), BTN_CUA_HANG_VOI_IMG, use_color=False)
    btn_open_voi_tpl = pre_process_tpl(cv2.imread(BTN_OPEN_CUA_HANG_VOI_IMG), BTN_OPEN_CUA_HANG_VOI_IMG, use_color=False)
    voi_sieu_cap_tpl = pre_process_tpl(cv2.imread(VOI_SIEU_CAP_IMG), VOI_SIEU_CAP_IMG, use_color=True)

    # Pre-process Thu hoạch & Bán
    ve_nha_tpl = pre_process_tpl(cv2.imread(BTN_VE_NHA_IMG), BTN_VE_NHA_IMG, use_color=False)
    panel_th_tpl = pre_process_tpl(cv2.imread(BTN_PANEL_TH_IMG), BTN_PANEL_TH_IMG, use_color=False)
    ban_fruit_tpl = pre_process_tpl(cv2.imread(BTN_BAN_FRUIT_IMG), BTN_BAN_FRUIT_IMG, use_color=False)
    open_ban_tpl = pre_process_tpl(cv2.imread(BTN_OPEN_BAN_FRUIT_IMG), BTN_OPEN_BAN_FRUIT_IMG, use_color=False)
    confirm_th_tpl = pre_process_tpl(cv2.imread(BTN_XAC_NHAN_IMG), BTN_XAC_NHAN_IMG, use_color=False)
    thu_hoach_all_tpl = pre_process_tpl(cv2.imread(BTN_THU_HOACH_ALL_IMG), BTN_THU_HOACH_ALL_IMG, use_color=False)

    # Pre-process trái cây (Lấy danh sách từ instance config)
    fruits = {}
    instance_fruits = config.get_instance_fruits(LD_INDEX)  # {name: True/False}
    all_fruits = config.get_fruits()  # {name: {img, buy}}
    
    for k, v in all_fruits.items():
        # Kiểm tra instance config trước, nếu không có thì dùng default
        should_buy = instance_fruits.get(k, v.get("buy", True))
        if not should_buy:  # Skip những trái không cần mua
            continue
        tpls = pre_process_tpl(cv2.imread(v["img"]), v["img"], use_color=True)
        if tpls:
            fruits[k] = {"tpls": tpls}
    
    # Cập nhật số lượng trái cần check = chỉ những trái được chọn mua
    active_fruits_count = len(fruits)
    print(f"[INFO] LD-{LD_INDEX}: Dang check {active_fruits_count} loai trai cay")

    first_run = ENABLE_FIRST_RUN_IMMEDIATE # ⚡ Cờ đánh dấu lượt chạy đầu tiên
    is_init_run = ENABLE_FIRST_RUN_IMMEDIATE # ⚡ Cờ để cưỡng bức vòi chạy lượt đầu

    while True:
        if USE_TIME_GATE:
            if first_run:
                print("🚀 [Khởi động] Chạy lượt đầu tiên ngay lập tức...")
                first_run = False
            else:
                wait_for_next_cycle()

        now = time.localtime()
        # ⚡ Lượt đầu tiên (is_init_run) hoặc đúng mốc thời gian mới check
        if USE_TIME_GATE:
            is_voi_time = (now.tm_min % 30 == 0) or is_init_run
            is_harvest_time = (now.tm_min == 0) or is_init_run
        else:
            is_voi_time = True
            is_harvest_time = True
            
        is_init_run = False # Sau lượt đầu thì tắt cờ này đi

        if not ENABLE_BUY_FRUITS:
            print("⏭ Bỏ qua module Trái cây (ENABLE_BUY_FRUITS=False)")
        else:
            if not ensure_panel_buy_open(panel_tpl, btn_cua_hang_tpl, btn_open_tpl, btn_open_tpl2):
                print("⚠️ Không đảm bảo được panel BUY → skip vòng này")
                pass
            else:
                # ⚡ TAP MỒI VÀO TRÁI ĐẦU TIÊN ĐỂ REFRESH PANEL (TRIGGER)
                print("👆 Kích hoạt phần tử đầu tiên (295, 270)...")
                tap(290, 630)

                # ⚡ Xác định món cuối cùng trong danh sách trái CẦN MUA để làm mốc dừng
                LAST_FRUIT_NAME = list(fruits.keys())[-1] if fruits else None
                checked, available, sold_out, bought = set(), [], [], set()
                
                for attempt in range(2):  # ⚡ THỬ TỐI ĐA 2 LƯỢT QUÉT (Double Check)
                    print(f"🔄 Bắt đầu lượt quét {attempt + 1}...")
                    if attempt > 0:
                        print("🔝 Quét lại: Reset về đầu trang shop...")
                        scroll_to_top()
                    
                    scroll_count = 0
                    max_scrolls = 6
                    reached_end = False # Flag đánh dấu đã thấy đáy shop

                    while len(checked) < active_fruits_count and scroll_count < max_scrolls:
                        screen = screencap()
                        if screen is None: continue
                        panel = crop(screen, ROI_PANEL_ALL)

                        # 1. Tìm tất cả các trái trong view hiện tại
                        targets_in_view = []
                        for name, data in fruits.items():
                            if name in checked: continue

                            # ⚡ Dùng màu để match trái cây chính xác
                            val, loc, size = match_with_loc(panel, data["tpls"], use_color=True)
                            if val >= THRESHOLD:
                                cx = ROI_PANEL_ALL[0] + loc[0] + size[0] // 2
                                cy = ROI_PANEL_ALL[1] + loc[1] + size[1] // 2
                                
                                # Đánh dấu nếu thấy món cuối cùng
                                if name == LAST_FRUIT_NAME:
                                    reached_end = True
                                    
                                # ⚡ CHECK HẾT HÀNG TRONG LIST...
                                check_roi = (cx + size[0]//2, cy - size[1]//2, cx + 450, cy + size[1]//2 + 50)
                                check_roi = (max(0, check_roi[0]), max(0, check_roi[1]), min(1920, check_roi[2]), min(1080, check_roi[3]))
                                area_text = crop(screen, check_roi)
                                s_val, _, _ = match_with_loc(area_text, sold_list_tpl)
                                
                                if s_val >= THRESHOLD:
                                    print(f"🔴 {name} đã hết hàng (list) -> Skip")
                                    checked.add(name)
                                    sold_out.append(name)
                                    continue
                                
                                # Tất cả fruits trong dict đều là cần mua (đã lọc ở đầu)

                                targets_in_view.append({"name": name, "pos": (cx, cy), "data": data})

                        # 2. Xử lý danh sách tìm được
                        should_break_to_top = False 
                        if targets_in_view:
                            for item in targets_in_view:
                                name = item["name"]
                                print(f"🎯 Thấy {name}, đang xử lý...")
                                tap(*item["pos"])
                                time.sleep(1)
                                screen_buy = screencap()
                                if screen_buy is None: continue
                                buy_roi = crop(screen_buy, ROI_BUY)
                                sold_val, _, _ = match_with_loc(buy_roi, sold_tpl)
                                if sold_val < THRESHOLD:
                                    available.append(name)
                                    # Tất cả fruits trong dict đều là cần mua (đã lọc ở đầu)
                                    if name not in bought:
                                        print(f"[MUA] Dang mua {name}...")
                                        tap(*BUY_BTN); time.sleep(0.6)
                                        tap(*MAX_QTY_BTN); time.sleep(0.5)
                                        tap(*CONFIRM_BTN)
                                        bought.add(name)
                                        time.sleep(1.0)
                                        should_break_to_top = True
                                else:
                                    print(f"🔴 {name} hết hàng (bảng mua)")
                                    sold_out.append(name)
                                checked.add(name)
                                time.sleep(0.5)
                                if should_break_to_top: break 
                        
                        if should_break_to_top:
                            print("🔄 Reset trang, quay lại đỉnh...")
                            scroll_count = 0 
                            continue 

                        # 3. Quyết định cuộn tiếp hay dừng
                        if reached_end:
                            print(f"🏁 Đã thấy {LAST_FRUIT_NAME}, dừng cuộn.")
                            break

                        if len(checked) < active_fruits_count:
                            print(f"🚀 Cuộn {scroll_count+1}/{max_scrolls}...")
                            swipe(*SCROLL_START, *SCROLL_END)
                            time.sleep(1.2)
                            scroll_count += 1
                        else:
                            break
                    
                    if len(checked) >= active_fruits_count:
                        print("✅ Tìm thấy tất cả vật phẩm.")
                        break
                    else:
                        if attempt == 0:
                            print(f"⚠️ Lượt 1 mới check {len(checked)}/{active_fruits_count} quả. Quét lại...")

                # Thông báo Telegram
                msg = format_result(available)
                if msg:
                    send_tele(msg)

        # ================= MODULE VÒI (30 PHÚT) =================
        if is_voi_time:
            if not ENABLE_BUY_VOI:
                print("⏭ Bỏ qua module Vòi (ENABLE_BUY_VOI=False)")
            else:
                print("🚿 Đã đến giờ check Vòi Tưới (Mốc 30p)...")
                # 1. Thoát panel trái cây
                tap(*CLOSE_FRUIT_BTN_1); time.sleep(2)
                tap(*CLOSE_FRUIT_BTN_2); time.sleep(2)
                # Ấn thêm lần nữa để tắt thông báo nếu có
                tap(*CLOSE_FRUIT_BTN_2); time.sleep(2)

                # 2. Mở panel vòi
                if ensure_panel_voi_open(btn_voi_tpl, btn_open_voi_tpl):

                    screen = screencap()
                    panel = crop(screen, ROI_PANEL_ALL)
                    
                    # Tìm vòi siêu cấp (chỉ check 1 lần, ko cuộn)
                    val, loc, size = match_with_loc(panel, voi_sieu_cap_tpl, use_color=True)
                    if val >= THRESHOLD:
                        cx = ROI_PANEL_ALL[0] + loc[0] + size[0] // 2
                        cy = ROI_PANEL_ALL[1] + loc[1] + size[1] // 2
                        
                        # Check hết hàng tại chỗ
                        area_text = crop(screen, (cx + size[0]//2, cy - size[1]//2, cx + 450, cy + size[1]//2 + 50))
                        s_val, _, _ = match_with_loc(area_text, sold_list_tpl)
                        
                        if s_val < THRESHOLD:
                            print("🎯 Thấy Vòi Siêu Cấp, đang mua...")
                            tap(cx, cy); time.sleep(1)
                            
                            screen_buy = screencap()
                            buy_roi = crop(screen_buy, ROI_BUY)
                            sold_val, _, _ = match_with_loc(buy_roi, sold_tpl)
                            
                            if sold_val < THRESHOLD:
                                tap(*BUY_BTN); time.sleep(0.6)
                                tap(*MAX_QTY_BTN); time.sleep(0.5)
                                tap(*CONFIRM_BTN)
                                send_tele(f"⏱ <i>{now_str()}</i>\n\n🚿 <b>ĐÃ MUA VÒI SIÊU CẤP</b>")
                                time.sleep(1)
                            else:
                                print("🔴 Vòi siêu cấp hết hàng (bảng mua)")
                        else:
                            print("🔴 Vòi siêu cấp hết hàng (list)")
                    else:
                        print("❌ Không tìm thấy Vòi Siêu Cấp trên màn hình")
                    
                    # 4. Thoát panel vòi
                    print("🔙 Thoát panel vòi...")
                    tap(*CLOSE_FRUIT_BTN_1); time.sleep(2)
                    tap(*CLOSE_FRUIT_BTN_2); time.sleep(2)
                
        # ================= MODULE THU HOẠCH & BÁN (1 TIẾNG) =================
        if is_harvest_time:
            if not ENABLE_HARVEST_SELL:
                print("⏭ Bỏ qua module Thu hoạch & Bán (ENABLE_HARVEST_SELL=False)")
            else:
                print("🚜 Đã đến giờ Thu hoạch & Bán (Mốc 1 tiếng)...")
                
                any_cycle_success = False
                for cycle in range(HARVEST_SELL_CYCLES):
                    print(f"🚜 Bắt đầu lượt {cycle+1}/{HARVEST_SELL_CYCLES}...")
                    
                    # 1. Về nhà 
                    pos_ve_nha = wait_for_img(ve_nha_tpl, ROI_BTN_CUA_HANG, timeout=10)
                    if pos_ve_nha:
                        print(f"🏠 [Lượt {cycle+1}] Đang về nhà...")
                        tap(*pos_ve_nha)
                        time.sleep(2) # Đợi load về nhà
                        any_cycle_success = True
                    else:
                        print(f"❌ Không thấy nút về nhà ở lượt {cycle+1}, bỏ qua các lượt sau.")
                        break

                    # 2. Mở panel thu hoạch
                    pos_th = wait_for_img(panel_th_tpl, (0, 0, 960, 1080), timeout=6)
                    if pos_th:
                        print("🌾 Mở panel thu hoạch...")
                        tap(*pos_th)
                        time.sleep(1); tap(*OPEN_TH_SUB); time.sleep(1.5)
                        
                        # Thu hoạch toàn bộ
                        print("🧺 Thu hoạch toàn bộ...")
                        
                        # ⚡ TÌM NÚT THU HOẠCH ALL QUA ẢNH
                        screen_th = screencap()
                        roi_th = crop(screen_th, ROI_THU_HOACH_ALL)
                        val_th, loc_th, size_th = match_with_loc(roi_th, thu_hoach_all_tpl)
                        
                        target_th = HARVEST_ALL_BTN
                        if val_th >= THRESHOLD:
                            target_th = (ROI_THU_HOACH_ALL[0] + loc_th[0] + size_th[0]//2, ROI_THU_HOACH_ALL[1] + loc_th[1] + size_th[1]//2)
                            print(f"✔️ Thấy nút thu hoạch all qua ảnh tại {target_th}")
                        
                        tap(*target_th); time.sleep(1)
                        
                        # ⚡ CHECK NÚT XÁC NHẬN
                        screen_conf = screencap()
                        roi_conf = crop(screen_conf, ROI_CONFIRM_TH)
                        val_c, loc_c, size_c = match_with_loc(roi_conf, confirm_th_tpl)
                        
                        if val_c < THRESHOLD:
                            print("❌ Không thấy nút xác nhận thu hoạch -> Dừng toàn bộ các lượt tiếp theo.")
                            tap(*CLOSE_TH_BTN); time.sleep(1)
                            break
                        
                        cx = ROI_CONFIRM_TH[0] + loc_c[0] + size_c[0]//2
                        cy = ROI_CONFIRM_TH[1] + loc_c[1] + size_c[1]//2
                        print(f"✔️ Thấy nút xác nhận tại ({cx}, {cy}), đang ấn...")
                        tap(cx, cy); time.sleep(2)
                        tap(*CLOSE_TH_BTN); time.sleep(1)
                    
                    # 3. Đi bán trái
                    pos_ban = wait_for_img(ban_fruit_tpl, ROI_BTN_CUA_HANG, timeout=6)
                    if pos_ban:
                        print("💰 Đi tới chỗ bán trái...")
                        tap(*pos_ban)
                        time.sleep(2) # Đợi di chuyển
                        
                        # 1. Mở panel bán
                        pos_open_ban = wait_for_img(open_ban_tpl, ROI_BTN_OPEN_CUA_HANG, timeout=6)
                        if pos_open_ban:
                            print("🛍 Mở panel bán...")
                            tap(*pos_open_ban)
                            time.sleep(1.5); tap(*OPEN_BAN_SUB); time.sleep(1.5)
                            
                            # 2. Lặp lại việc bấm bán n lần khi đang mở panel
                            for s_cycle in range(SELL_CYCLES_AFTER_HARVEST):
                                print(f"💵 Thực hiện bán lần {s_cycle+1}/{SELL_CYCLES_AFTER_HARVEST}...")
                                tap(*SELECT_ALL_PRODUCE); time.sleep(1)
                                tap(*SELL_BTN); time.sleep(1)
                                tap(*OK_SELL_BTN); time.sleep(1)
                                # ⚡ Tìm nút xác nhận 
                                target_confirm = (1177, 815) 
                                screen_s = screencap()
                                roi_s = crop(screen_s, ROI_CONFIRM_TH)
                                val_s, loc_s, size_s = match_with_loc(roi_s, confirm_th_tpl)
                                if val_s >= THRESHOLD:
                                    target_confirm = (ROI_CONFIRM_TH[0] + loc_s[0] + size_s[0]//2, ROI_CONFIRM_TH[1] + loc_s[1] + size_s[1]//2)
                                    print(f"✔️ Thấy nút xác nhận bán qua ảnh tại {target_confirm}")
                                
                                tap(*target_confirm); time.sleep(2)
                                tap(*OK_SELL_BTN); time.sleep(1)
                                time.sleep(1.5) 
                            
                            # 3. Thoát panel sau khi đã bán đủ số lượt
                            print("🔙 Đã bán đủ số lượt, đóng panel...")
                            tap(*CLOSE_BAN_BTN); time.sleep(2)
                            tap(*CLOSE_BAN_BTN); time.sleep(1)
                        else:
                            print("❌ Không thấy nút Open bán trái ở lượt này")
                        
                        print(f"✅ Đã xong chu kỳ thu hoạch & bán lượt {cycle+1}.")
                    else:
                        print(f"❌ Không thấy nút đi bán trái ở lượt {cycle+1}")
                
                # Telegram
                if any_cycle_success:
                    send_tele(f"⏱ <i>{now_str()}</i>\n\n🚜 <b>THU HOẠCH & BÁN XONG</b>\n(Đã chạy {HARVEST_SELL_CYCLES} lượt)")

        print("✅ Kết thúc chu kỳ. Đợt lượt tiếp theo.")
        gc.collect()  # ⚡ Giải phóng RAM cuối mỗi chu kỳ
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
