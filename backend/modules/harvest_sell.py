"""
Harvest & Sell Module - Logic thu hoạch và bán trái
Copy chính xác logic từ main.py gốc
"""
import time
import gc
import functools
from typing import Dict

print = functools.partial(print, flush=True)


class HarvestSellModule:
    """Module xử lý việc thu hoạch và bán trái cây"""
    
    def __init__(self, adb, image_processor, config, instance_config: Dict):
        self.adb = adb
        self.img = image_processor
        self.config = config
        self.instance_config = instance_config
        
        # Settings từ instance config (fallback to global)
        self.harvest_cycles = instance_config.get("harvest_sell_cycles", config.get("harvest_sell_cycles", 1))
        self.sell_cycles = instance_config.get("sell_cycles_after_harvest", config.get("sell_cycles_after_harvest", 1))
        
        # ROI constants - lấy từ config
        self.ROI_BTN_CUA_HANG = config.roi.btn_cua_hang
        self.ROI_BTN_OPEN_CUA_HANG = config.roi.btn_open_cua_hang
        self.ROI_THU_HOACH_ALL = config.roi.thu_hoach_all
        self.ROI_CONFIRM_TH = config.roi.confirm_th
        
        # Button constants
        self.OPEN_TH_SUB = config.buttons.open_th_sub
        self.HARVEST_ALL_BTN = config.buttons.harvest_all
        self.CLOSE_TH_BTN = config.buttons.close_th
        self.OPEN_BAN_SUB = config.buttons.open_ban_sub
        self.SELECT_ALL_PRODUCE = config.buttons.select_all_produce
        self.SELL_BTN = config.buttons.sell
        self.OK_SELL_BTN = config.buttons.ok_sell
        self.CLOSE_BAN_BTN = config.buttons.close_ban
        
        # Load templates
        self._load_templates()
    
    def _load_templates(self):
        """Load các template cần thiết"""
        self.ve_nha_tpl = self.img.load_template(self.config.get_button_path("ve_nha"))
        self.panel_th_tpl = self.img.load_template(self.config.get_button_path("panel_th"))
        self.thu_hoach_all_tpl = self.img.load_template(self.config.get_button_path("thu_hoach_all"))
        self.ban_fruit_tpl = self.img.load_template(self.config.get_button_path("ban_fruit"))
        self.open_ban_tpl = self.img.load_template(self.config.get_button_path("open_ban_fruit"))
        self.confirm_tpl = self.img.load_template(self.config.get_button_path("xac_nhan"))
    
    def run(self) -> Dict:
        """
        Chạy module thu hoạch và bán - ĐÚNG LOGIC GỐC
        Returns: {"success": bool, "cycles_completed": int}
        """
        print("STATUS: Harvesting & Selling")
        
        any_cycle_success = False
        cycles_completed = 0
        
        for cycle in range(self.harvest_cycles):
            print(f"[SELL] Cycle {cycle + 1}/{self.harvest_cycles}")
            
            # ==================== 1. VỀ NHÀ ====================
            pos_ve_nha = self.img.wait_for_template(
                self.adb, self.ve_nha_tpl,
                self.ROI_BTN_CUA_HANG, timeout=10
            )
            if pos_ve_nha:
                print(f"[SELL] Returning home")
                self.adb.tap(*pos_ve_nha)
                time.sleep(2)  # Wait for loading
                any_cycle_success = True
            else:
                print(f"[SELL] Home button not found, skipping...")
                break
            
            # ==================== 2. MỞ PANEL THU HOẠCH ====================
            pos_th = self.img.wait_for_template(
                self.adb, self.panel_th_tpl,
                (0, 0, 960, 1080), timeout=6
            )
            if pos_th:
                print("[SELL] Opening harvest panel")
                self.adb.tap(*pos_th)
                time.sleep(1)
                self.adb.tap(*self.OPEN_TH_SUB)
                time.sleep(1.5)
                
                # Thu hoạch toàn bộ
                print("[SELL] Harvesting all...")
                
                # Tìm nút thu hoạch all qua ảnh
                png = self.adb.screencap()
                screen = self.img.decode_screenshot(png)
                
                target_th = self.HARVEST_ALL_BTN  # Fallback position
                if screen is not None:
                    roi_th = self.img.crop(screen, self.ROI_THU_HOACH_ALL)
                    val_th, loc_th, size_th = self.img.match(roi_th, self.thu_hoach_all_tpl)
                    
                    if val_th >= self.img.threshold:
                        target_th = (
                            self.ROI_THU_HOACH_ALL[0] + loc_th[0] + size_th[0]//2,
                            self.ROI_THU_HOACH_ALL[1] + loc_th[1] + size_th[1]//2
                        )
                        print(f"[SELL] Confirming harvest button position: {target_th}")
                
                self.adb.tap(*target_th)
                time.sleep(1)
                
                # CHECK NÚT XÁC NHẬN THU HOẠCH
                png2 = self.adb.screencap()
                screen2 = self.img.decode_screenshot(png2)
                
                if screen2 is not None:
                    roi_conf = self.img.crop(screen2, self.ROI_CONFIRM_TH)
                    val_c, loc_c, size_c = self.img.match(roi_conf, self.confirm_tpl)
                    
                    if val_c < self.img.threshold:
                        print("[SELL] Confirm button not found")
                        self.adb.tap(*self.CLOSE_TH_BTN)
                        time.sleep(1)
                        break
                    
                    cx = self.ROI_CONFIRM_TH[0] + loc_c[0] + size_c[0]//2
                    cy = self.ROI_CONFIRM_TH[1] + loc_c[1] + size_c[1]//2
                    print(f"[SELL] Pressing confirm at ({cx}, {cy})")
                    self.adb.tap(cx, cy)
                    time.sleep(2)
                
                # Đóng panel thu hoạch
                self.adb.tap(*self.CLOSE_TH_BTN)
                time.sleep(1)
            
            # ==================== 3. ĐI BÁN TRÁI ====================
            pos_ban = self.img.wait_for_template(
                self.adb, self.ban_fruit_tpl,
                self.ROI_BTN_CUA_HANG, timeout=6
            )
            if pos_ban:
                print("[SELL] Moving to shop...")
                self.adb.tap(*pos_ban)
                time.sleep(2)
                
                # Mở panel bán
                pos_open_ban = self.img.wait_for_template(
                    self.adb, self.open_ban_tpl,
                    self.ROI_BTN_OPEN_CUA_HANG, timeout=6
                )
                if pos_open_ban:
                    print("[SELL] Opening sell panel")
                    self.adb.tap(*pos_open_ban)
                    time.sleep(1.5)
                    self.adb.tap(*self.OPEN_BAN_SUB)
                    time.sleep(1.5)
                    
                    # Lặp lại việc bấm bán n lần khi đang mở panel
                    for s_cycle in range(self.sell_cycles):
                        print(f"[SELL] Selling cycle {s_cycle + 1}/{self.sell_cycles}")
                        
                        # Bước 1: Chọn tất cả sản phẩm
                        self.adb.tap(*self.SELECT_ALL_PRODUCE)
                        time.sleep(1)
                        
                        # Bước 2: Nhấn nút Bán
                        self.adb.tap(*self.SELL_BTN)
                        time.sleep(1)
                        
                        # Bước 3: Nhấn OK
                        self.adb.tap(*self.OK_SELL_BTN)
                        time.sleep(1)
                        
                        # Bước 4: Tìm và nhấn nút xác nhận qua ảnh
                        target_confirm = (1177, 815)  # Fallback position
                        png3 = self.adb.screencap()
                        screen3 = self.img.decode_screenshot(png3)
                        
                        if screen3 is not None:
                            roi_s = self.img.crop(screen3, self.ROI_CONFIRM_TH)
                            val_s, loc_s, size_s = self.img.match(roi_s, self.confirm_tpl)
                            
                            if val_s >= self.img.threshold:
                                target_confirm = (
                                    self.ROI_CONFIRM_TH[0] + loc_s[0] + size_s[0]//2,
                                    self.ROI_CONFIRM_TH[1] + loc_s[1] + size_s[1]//2
                                )
                                print(f"[SELL] Confirming sell button position: {target_confirm}")
                        
                        # Bước 5: Nhấn xác nhận
                        self.adb.tap(*target_confirm)
                        time.sleep(2)
                        
                        # Bước 6: Nhấn OK lần nữa
                        self.adb.tap(*self.OK_SELL_BTN)
                        time.sleep(1)
                        
                        time.sleep(1.5)  # Đợi animation
                    
                    # Thoát panel sau khi đã bán đủ số lượt
                    print("[SELL] All cycles finished, closing panel")
                    self.adb.tap(*self.CLOSE_BAN_BTN)
                    time.sleep(2)
                    self.adb.tap(*self.CLOSE_BAN_BTN)
                    time.sleep(1)
                else:
                    print("[SELL] Close button not found")
                
                print(f"[SELL] Harvest & Sell cycle {cycle + 1} complete.")
                cycles_completed += 1
            else:
                print(f"[SELL] Sell action button not found")
        
        # Kết thúc
        if any_cycle_success:
            print(f"[SELL] Task finished: {cycles_completed} cycles.")
        
        gc.collect()
        return {"success": any_cycle_success, "cycles_completed": cycles_completed}
