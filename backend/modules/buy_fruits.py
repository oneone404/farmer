"""
Buy Fruits Module - Logic mua trái cây
Đã đồng bộ đầy đủ với main_legacy.py
"""
import time
import gc
import functools
from typing import Dict, Set, List, Optional

print = functools.partial(print, flush=True)


class BuyFruitsModule:
    """Module xử lý việc mua trái cây trong Shop"""
    
    def __init__(self, adb, image_processor, config, instance_config: Dict):
        self.adb = adb
        self.img = image_processor
        self.config = config
        self.instance_config = instance_config
        
        # Load templates
        self._load_templates()
        
        # State
        self.checked: Set[str] = set()
        self.bought: Set[str] = set()
        self.available: List[str] = []
        self.sold_out: List[str] = []
    
    def _load_templates(self):
        """Load các template cần thiết"""
        self.panel_tpl = self.img.load_template(self.config.get_template_path("panel_buy"))
        self.sold_tpl = self.img.load_template(self.config.get_template_path("sold_out"))
        self.sold_list_tpl = self.img.load_template(self.config.get_template_path("sold_out_list"))
        self.btn_cua_hang_tpl = self.img.load_template(self.config.get_button_path("cua_hang"))
        self.btn_open_tpl = self.img.load_template(self.config.get_button_path("open_cua_hang"))
        self.btn_open_tpl2 = self.img.load_template(self.config.get_button_path("open_cua_hang_2"))
        
        # Load fruit templates
        self.fruits = {}
        all_fruits = self.config.get_fruits()
        instance_fruits = self.instance_config.get("fruits", {})
        
        for name, data in all_fruits.items():
            fruit_cfg = instance_fruits.get(name)
            if isinstance(fruit_cfg, dict):
                should_buy = fruit_cfg.get("buy", True)
            else:
                should_buy = data.get("buy", True)
                
            if not should_buy:
                continue
                
            tpls = self.img.load_template(data["img"], use_color=True)
            if tpls:
                self.fruits[name] = {"tpls": tpls}

        
        print(f"[FRUIT] Templates loaded for {len(self.fruits)} items")
    
    def scroll_to_top(self):
        """Scroll to the top of the shop"""
        print("[FRUIT] Scrolling to top...")
        for _ in range(3):
            self.adb.swipe(600, 400, 600, 1000, 200)
            time.sleep(0.5)
    
    def ensure_panel_open(self) -> bool:
        """Đảm bảo panel Shop đã mở - ĐẦY ĐỦ các bước"""
        # 1. Check xem bảng Buy đã mở sẵn chưa
        png = self.adb.screencap()
        screen = self.img.decode_screenshot(png)
        if screen is None:
            return False
        
        roi = self.config.roi.panel_check
        cropped = self.img.crop(screen, roi)
        val, _, _ = self.img.match(cropped, self.panel_tpl)
        
        del cropped
        del screen
        gc.collect()
        
        if val >= self.img.threshold:
            print("[FRUIT] Shop panel is open")
            return True
        
        print("[FRUIT] Shop panel closed - Opening...")
        
        # 2. Tìm và click btn_cua_hang
        pos = self.img.wait_for_template(
            self.adb, self.btn_cua_hang_tpl, 
            self.config.roi.btn_cua_hang, timeout=6
        )
        if pos:
            print("[FRUIT] Clicking Shop button")
            self.adb.tap(*pos)
        else:
            print("[FRUIT] Shop button not found")
            return False
        
        # 3. Đợi và tìm btn_open_cua_hang (Open 1)
        pos1 = self.img.wait_for_template(
            self.adb, self.btn_open_tpl,
            self.config.roi.btn_open_cua_hang, timeout=6
        )
        if pos1:
            print("[FRUIT] Clicking Open button 1")
            self.adb.tap(*pos1)
        else:
            print("[FRUIT] Open button 1 not found")
            return False
        
        # 4. Đợi và tìm btn_open_cua_hang2 (Open 2)
        pos2 = self.img.wait_for_template(
            self.adb, self.btn_open_tpl2,
            self.config.roi.btn_open_cua_hang_2, timeout=6
        )
        if pos2:
            print("[FRUIT] Clicking Open button 2")
            self.adb.tap(*pos2)
            time.sleep(1)
            return True
        else:
            print("[FRUIT] Open button 2 not found")
            return False
    
    def run(self) -> Dict:
        """
        Chạy module mua trái cây - LOGIC ĐẦY ĐỦ
        Returns: {"available": [...], "bought": [...], "sold_out": [...]}
        """
        print("STATUS: Buying Fruits")
        
        if not self.ensure_panel_open():
            print("[FRUIT] Failed to open shop panel")
            return {"available": [], "bought": [], "sold_out": []}
        
        # Reset state
        self.checked.clear()
        self.bought.clear()
        self.available.clear()
        self.sold_out.clear()
        
        # Kích hoạt phần tử đầu tiên (trigger)
        print("[FRUIT] Initializing shop scroll...")
        self.adb.tap(290, 630)
        time.sleep(1)
        
        # Xác định món cuối cùng trong danh sách
        LAST_FRUIT_NAME = list(self.fruits.keys())[-1] if self.fruits else None
        active_fruits_count = len(self.fruits)
        
        # Quét 2 lượt (Double Check như code gốc)
        for attempt in range(2):
            print(f"[FRUIT] Scanning items (Attempt {attempt + 1})")
            if attempt > 0:
                print("[FRUIT] Resetting shop view...")
                self.scroll_to_top()
            
            scroll_count = 0
            max_scrolls = 6
            reached_end = False
            
            while len(self.checked) < active_fruits_count and scroll_count < max_scrolls:
                png = self.adb.screencap()
                screen = self.img.decode_screenshot(png)
                if screen is None:
                    continue
                
                panel = self.img.crop(screen, self.config.roi.panel_all)
                
                # 1. Tìm tất cả các trái trong view hiện tại
                targets_in_view = []
                for name, data in self.fruits.items():
                    if name in self.checked:
                        continue
                    
                    val, loc, size = self.img.match(panel, data["tpls"], use_color=True)
                    if val >= self.img.threshold:
                        cx = self.config.roi.panel_all[0] + loc[0] + size[0] // 2
                        cy = self.config.roi.panel_all[1] + loc[1] + size[1] // 2
                        
                        # Đánh dấu nếu thấy món cuối cùng
                        if name == LAST_FRUIT_NAME:
                            reached_end = True
                        
                        # CHECK HẾT HÀNG TRONG LIST
                        check_roi = (cx + size[0]//2, cy - size[1]//2, cx + 450, cy + size[1]//2 + 50)
                        check_roi = (max(0, check_roi[0]), max(0, check_roi[1]), min(1920, check_roi[2]), min(1080, check_roi[3]))
                        area_text = self.img.crop(screen, check_roi)
                        s_val, _, _ = self.img.match(area_text, self.sold_list_tpl)
                        
                        if s_val >= self.img.threshold:
                            print(f"[FRUIT] {name}: Sold out")
                            self.checked.add(name)
                            self.sold_out.append(name)
                            continue
                        
                        targets_in_view.append({"name": name, "pos": (cx, cy), "data": data})
                
                # 2. Xử lý danh sách tìm được
                should_break_to_top = False
                if targets_in_view:
                    for item in targets_in_view:
                        name = item["name"]
                        print(f"[FRUIT] Selecting {name}")
                        self.adb.tap(*item["pos"])
                        time.sleep(1)
                        
                        png2 = self.adb.screencap()
                        screen2 = self.img.decode_screenshot(png2)
                        if screen2 is None:
                            continue
                        
                        buy_roi = self.img.crop(screen2, self.config.roi.buy)
                        sold_val, _, _ = self.img.match(buy_roi, self.sold_tpl)
                        
                        if sold_val < self.img.threshold:
                            self.available.append(name)
                            if name not in self.bought:
                                print(f"[FRUIT] Buying {name}")
                                self.adb.tap(*self.config.buttons.buy)
                                time.sleep(0.6)
                                self.adb.tap(*self.config.buttons.max_qty)
                                time.sleep(0.5)
                                self.adb.tap(*self.config.buttons.confirm)
                                self.bought.add(name)
                                time.sleep(1.0)
                                should_break_to_top = True
                        else:
                            print(f"[FRUIT] {name}: Sold out (detail panel)")
                            self.sold_out.append(name)
                        
                        self.checked.add(name)
                        time.sleep(0.5)
                        if should_break_to_top:
                            break
                
                if should_break_to_top:
                    print("[FRUIT] Returning to top to refresh list...")
                    scroll_count = 0
                    continue
                
                # 3. Quyết định cuộn tiếp hay dừng
                if reached_end:
                    print(f"[FRUIT] End of list reached: {LAST_FRUIT_NAME}")
                    break
                
                if len(self.checked) < active_fruits_count:
                    print(f"[FRUIT] Scrolling ({scroll_count + 1}/{max_scrolls})")
                    scroll_start = self.config.get("scroll_start", [600, 900])
                    scroll_end = self.config.get("scroll_end", [600, 450])
                    self.adb.swipe(*scroll_start, *scroll_end)
                    time.sleep(1.2)
                    scroll_count += 1
                else:
                    break
            
            if len(self.checked) >= active_fruits_count:
                break
            else:
                if attempt == 0:
                    print(f"[FRUIT] Incomplete scan ({len(self.checked)}/{active_fruits_count}). retrying...")
        
        print(f"[FRUIT] Cycle finished: {len(self.bought)} items bought")
        gc.collect()
        
        return {
            "available": list(self.available),
            "bought": list(self.bought),
            "sold_out": list(self.sold_out)
        }
    
    def close_panel(self):
        """Đóng panel Shop"""
        self.adb.tap(*self.config.buttons.close_fruit_1)
        time.sleep(2)
        self.adb.tap(*self.config.buttons.close_fruit_2)
        time.sleep(2)
        # Ấn thêm lần nữa để tắt thông báo nếu có
        self.adb.tap(*self.config.buttons.close_fruit_2)
        time.sleep(2)
