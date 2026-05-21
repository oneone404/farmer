"""
Image Processor - Xử lý ảnh và template matching
"""
import cv2
import numpy as np
from typing import Tuple, List, Optional
import functools

print = functools.partial(print, flush=True)


class ImageProcessor:
    """Class xử lý ảnh và template matching"""
    
    def __init__(self, threshold: float = 0.9, scales: list = None):
        self.threshold = threshold
        self.scales = scales or [1.0]
    
    def decode_screenshot(self, png_bytes: bytes) -> Optional[np.ndarray]:
        """Decode ảnh PNG từ bytes sang numpy array"""
        if not png_bytes:
            return None
        try:
            nparr = np.frombuffer(png_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print(f"❌ Lỗi decode screenshot: {e}")
            return None
    
    def crop(self, img: np.ndarray, roi: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """Cắt ảnh theo vùng ROI (x1, y1, x2, y2)"""
        if img is None:
            return None
        x1, y1, x2, y2 = roi
        return img[y1:y2, x1:x2]
    
    def load_template(self, path: str, use_color: bool = False) -> List[Tuple]:
        """Load và pre-process template với nhiều tỷ lệ"""
        try:
            img = cv2.imread(path)
            if img is None:
                print(f"❌ Không tìm thấy template: {path}")
                return []
            
            img_proc = img if use_color else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            results = []
            for scale in self.scales:
                tw = int(img_proc.shape[1] * scale)
                th = int(img_proc.shape[0] * scale)
                if tw < 5 or th < 5:
                    continue
                resized = cv2.resize(img_proc, (tw, th))
                results.append((resized, (tw, th)))
            return results
        except Exception as e:
            print(f"❌ Lỗi load template: {e}")
            return []
    
    def match(self, img: np.ndarray, templates: List[Tuple], use_color: bool = False) -> Tuple[float, Tuple[int, int], Tuple[int, int]]:
        """
        Template matching với nhiều tỷ lệ
        Returns: (confidence, location, size)
        """
        if img is None or not templates:
            return 0, (0, 0), (0, 0)
        
        if img.size == 0 or len(img.shape) < 2:
            return 0, (0, 0), (0, 0)
        
        try:
            img_proc = img if use_color else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            return 0, (0, 0), (0, 0)
        
        ih, iw = img_proc.shape[:2]
        if ih == 0 or iw == 0:
            return 0, (0, 0), (0, 0)
        
        best_val, best_loc, best_size = 0, (0, 0), (0, 0)
        
        for (tpl, (tw, th)) in templates:
            if ih < th or iw < tw:
                continue
            
            res = cv2.matchTemplate(img_proc, tpl, cv2.TM_CCOEFF_NORMED)
            _, val, _, loc = cv2.minMaxLoc(res)
            
            if val > best_val:
                best_val = val
                best_loc = loc
                best_size = (tw, th)
        
        return best_val, best_loc, best_size
    
    def wait_for_template(
        self, 
        adb, 
        templates: List[Tuple], 
        roi: Tuple[int, int, int, int],
        timeout: float = 5.0,
        interval: float = 0.5,
        use_color: bool = False
    ) -> Optional[Tuple[int, int]]:
        """Đợi template xuất hiện, trả về tọa độ trung tâm nếu thấy"""
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            png = adb.screencap()
            screen = self.decode_screenshot(png)
            if screen is None:
                time.sleep(interval)
                continue
            
            cropped = self.crop(screen, roi)
            if cropped is None:
                time.sleep(interval)
                continue
            
            val, loc, size = self.match(cropped, templates, use_color)
            if val >= self.threshold:
                cx = roi[0] + loc[0] + size[0] // 2
                cy = roi[1] + loc[1] + size[1] // 2
                return (cx, cy)
            
            time.sleep(interval)
        
        return None
