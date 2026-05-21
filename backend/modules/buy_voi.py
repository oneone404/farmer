"""
Buy Voi Module - Logic mua vòi tưới
Đã đồng bộ đầy đủ với main_legacy.py
"""
import time
import gc
import functools
from typing import Dict

print = functools.partial(print, flush=True)


class BuyVoiModule:
    """Module xử lý việc mua vòi tưới siêu cấp"""
    
    def __init__(self, adb, image_processor, config, instance_config: Dict):
        self.adb = adb
        self.img = image_processor
        self.config = config
        self.instance_config = instance_config
        
        # Load templates
        self._load_templates()
    
    def _load_templates(self):
        """Load các template cần thiết"""
        self.btn_voi_tpl = self.img.load_template(self.config.get_button_path("cua_hang_voi"))
        self.btn_open_voi_tpl = self.img.load_template(self.config.get_button_path("open_cua_hang_voi"))
        self.voi_sieu_cap_tpl = self.img.load_template(self.config.get_template_path("voi_sieu_cap"), use_color=True)
        self.sold_list_tpl = self.img.load_template(self.config.get_template_path("sold_out_list"))
        self.sold_tpl = self.img.load_template(self.config.get_template_path("sold_out"))
    
    def ensure_panel_open(self) -> bool:
        """Đảm bảo panel Vòi đã mở"""
        # Tìm và click nút cửa hàng vòi
        pos = self.img.wait_for_template(
            self.adb, self.btn_voi_tpl,
            self.config.roi.btn_cua_hang, timeout=6
        )
        if pos:
            print("[SPRINKLER] Clicking Sprinkler Shop button")
            self.adb.tap(*pos)
        else:
            print("[SPRINKLER] Sprinkler Shop button not found")
            return False
        
        # Đợi và tìm btn_open_voi
        pos_open = self.img.wait_for_template(
            self.adb, self.btn_open_voi_tpl,
            self.config.roi.btn_open_cua_hang, timeout=6
        )
        if pos_open:
            print("[SPRINKLER] Clicking Open button")
            self.adb.tap(*pos_open)
            time.sleep(1.5)
            # Ấn vào tab vòi
            self.adb.tap(*self.config.buttons.panel_voi_select)
            time.sleep(1)
            return True
        else:
            print("[SPRINKLER] Open button not found")
            return False
    
    def run(self) -> Dict:
        """
        Chạy module mua vòi - LOGIC ĐẦY ĐỦ
        Returns: {"success": bool, "bought": bool}
        """
        print("STATUS: Buying Sprinkler")
        
        # 1. Mở panel vòi
        if not self.ensure_panel_open():
            print("[SPRINKLER] Failed to open panel")
            return {"success": False, "bought": False}
        
        # 2. Chụp màn hình và tìm vòi siêu cấp
        png = self.adb.screencap()
        screen = self.img.decode_screenshot(png)
        if screen is None:
            return {"success": False, "bought": False}
        
        panel = self.img.crop(screen, self.config.roi.panel_all)
        
        # Tìm vòi siêu cấp (chỉ check 1 lần, không cuộn)
        val, loc, size = self.img.match(panel, self.voi_sieu_cap_tpl, use_color=True)
        
        bought = False
        if val >= self.img.threshold:
            cx = self.config.roi.panel_all[0] + loc[0] + size[0] // 2
            cy = self.config.roi.panel_all[1] + loc[1] + size[1] // 2
            
            # Check hết hàng tại chỗ (trong list)
            check_roi = (cx + size[0]//2, cy - size[1]//2, cx + 450, cy + size[1]//2 + 50)
            area_text = self.img.crop(screen, check_roi)
            s_val, _, _ = self.img.match(area_text, self.sold_list_tpl)
            
            if s_val < self.img.threshold:
                print("[SPRINKLER] Found Sprinkler, buying...")
                self.adb.tap(cx, cy)
                time.sleep(1)
                
                # Check sold out ở bảng mua
                png2 = self.adb.screencap()
                screen2 = self.img.decode_screenshot(png2)
                if screen2 is not None:
                    buy_roi = self.img.crop(screen2, self.config.roi.buy)
                    sold_val, _, _ = self.img.match(buy_roi, self.sold_tpl)
                    
                    if sold_val < self.img.threshold:
                        self.adb.tap(*self.config.buttons.buy)
                        time.sleep(0.6)
                        self.adb.tap(*self.config.buttons.max_qty)
                        time.sleep(0.5)
                        self.adb.tap(*self.config.buttons.confirm)
                        print("[SPRINKLER] Purchase confirmed")
                        bought = True
                        time.sleep(1)
                    else:
                        print("[SPRINKLER] Sold out (detail panel)")
            else:
                print("[SPRINKLER] Sold out (list)")
        else:
            print("[SPRINKLER] Sprinkler not found")
        
        # Đóng panel
        self.close_panel()
        
        gc.collect()
        return {"success": True, "bought": bought}
    
    def close_panel(self):
        """Close sprinkler panel"""
        print("[SPRINKLER] Closing panel")
        self.adb.tap(*self.config.buttons.close_fruit_1)
        time.sleep(2)
        self.adb.tap(*self.config.buttons.close_fruit_2)
        time.sleep(2)
