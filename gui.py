"""
Farmer - Modern UI v5.1
Giao diện hiện đại với hỗ trợ đa LDPlayer
"""

import customtkinter as ctk
import threading
import subprocess
import queue
import time
import os
import sys
import re
from datetime import datetime
from PIL import Image

# Import modules
from config_manager import config, DEFAULT_FRUITS, DEFAULT_INSTANCE_CONFIG
from ld_manager import (
    get_ld_instances, 
    get_adb_devices, 
    launch_ld, 
    quit_ld,
    set_ldplayer_path,
    ADB_PATH
)

# Shortcut functions
def load_instance_config(ld_index):
    return config.load_instance_config(ld_index)

def save_instance_config(ld_index, cfg):
    return config.save_instance_config(ld_index, cfg)

# Lấy danh sách FRUITS
FRUITS = config.get_fruits()

# ================= THEME SETUP =================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Colors - Tông màu xanh cyan/teal hiện đại
COLORS = {
    "bg_dark": "#0f0f1a",
    "bg_card": "#1a1a2e",
    "bg_card_hover": "#252542",
    "sidebar": "#141428",
    "accent": "#00d4aa",
    "accent_hover": "#00ffcc",
    "accent_dim": "#008866",
    "success": "#00e676",
    "warning": "#ffab00",
    "error": "#ff5252",
    "text": "#ffffff",
    "text_dim": "#8888aa",
    "border": "#2a2a4a",
}


class InstanceConfigDialog(ctk.CTkToplevel):
    """Dialog cấu hình riêng cho từng LDPlayer"""
    
    def __init__(self, parent, instance: dict, on_save=None):
        super().__init__(parent)
        
        self.instance = instance
        self.on_save = on_save
        self.config = load_instance_config(instance["index"])
        
        # Window setup
        self.title(f"Cấu hình - {instance['name']} (#{instance['index']})")
        self.geometry("500x500")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 600) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_ui()
    
    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text=f"{self.instance['name']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left")
        
        status_text = "Đang chạy" if self.instance["running"] else "Đã tắt"
        status_color = COLORS["success"] if self.instance["running"] else COLORS["text_dim"]
        ctk.CTkLabel(
            header,
            text=status_text,
            font=ctk.CTkFont(size=12),
            text_color=status_color
        ).pack(side="right")
        
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # === CÀI ĐẶT CHUNG ===
        general_card = self._create_card(scroll, "Cài đặt chung")
        general_card.pack(fill="x", pady=(0, 10))
        
        gen_inner = ctk.CTkFrame(general_card, fg_color="transparent")
        gen_inner.pack(fill="x", padx=15, pady=(5, 15))
        
        # Enabled
        self.enabled_var = ctk.BooleanVar(value=self.config.get("enabled", True))
        ctk.CTkSwitch(
            gen_inner,
            text="Bật automation cho LD này",
            variable=self.enabled_var,
            font=ctk.CTkFont(size=12),
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"]
        ).pack(anchor="w", pady=3)
        
        # Time gate
        self.time_gate_var = ctk.BooleanVar(value=self.config.get("use_time_gate", True))
        ctk.CTkSwitch(
            gen_inner,
            text="Chờ mốc thời gian (5p, 10p...)",
            variable=self.time_gate_var,
            font=ctk.CTkFont(size=12),
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"]
        ).pack(anchor="w", pady=3)
        
        # First run immediate
        self.first_run_var = ctk.BooleanVar(value=self.config.get("first_run_immediate", True))
        ctk.CTkSwitch(
            gen_inner,
            text="Chạy ngay lượt đầu tiên",
            variable=self.first_run_var,
            font=ctk.CTkFont(size=12),
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"]
        ).pack(anchor="w", pady=3)
        
        # Threshold
        threshold_row = ctk.CTkFrame(gen_inner, fg_color="transparent")
        threshold_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            threshold_row,
            text="Ngưỡng nhận diện:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        self.threshold_entry = ctk.CTkEntry(
            threshold_row,
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"]
        )
        self.threshold_entry.pack(side="left", padx=10)
        self.threshold_entry.insert(0, str(self.config.get("threshold", 0.8)))
        
        # === MODULES ===
        module_card = self._create_card(scroll, "Các module")
        module_card.pack(fill="x", pady=10)
        
        mod_inner = ctk.CTkFrame(module_card, fg_color="transparent")
        mod_inner.pack(fill="x", padx=15, pady=(5, 15))
        
        self.buy_fruits_var = ctk.BooleanVar(value=self.config.get("enable_buy_fruits", True))
        ctk.CTkSwitch(
            mod_inner,
            text="Mua trái cây",
            variable=self.buy_fruits_var,
            font=ctk.CTkFont(size=12),
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"]
        ).pack(anchor="w", pady=3)
        
        self.buy_voi_var = ctk.BooleanVar(value=self.config.get("enable_buy_voi", True))
        ctk.CTkSwitch(
            mod_inner,
            text="Mua vòi tưới",
            variable=self.buy_voi_var,
            font=ctk.CTkFont(size=12),
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"]
        ).pack(anchor="w", pady=3)
        
        self.harvest_var = ctk.BooleanVar(value=self.config.get("enable_harvest_sell", True))
        ctk.CTkSwitch(
            mod_inner,
            text="Thu hoạch & bán",
            variable=self.harvest_var,
            font=ctk.CTkFont(size=12),
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"]
        ).pack(anchor="w", pady=3)
        
        self.telegram_var = ctk.BooleanVar(value=self.config.get("enable_telegram", False))
        ctk.CTkSwitch(
            mod_inner,
            text="Gửi thông báo Telegram",
            variable=self.telegram_var,
            font=ctk.CTkFont(size=12),
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"]
        ).pack(anchor="w", pady=3)
        
        # === TRÁI CÂY ===
        fruits_card = self._create_card(scroll, "Trái cây muốn mua")
        fruits_card.pack(fill="x", pady=10)
        
        # Fruits grid
        grid_frame = ctk.CTkFrame(fruits_card, fg_color="transparent")
        grid_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        saved_fruits = self.config.get("fruits", {})
        self.fruit_vars = {}
        
        row, col = 0, 0
        for fruit_name, fruit_data in FRUITS.items():
            is_checked = saved_fruits.get(fruit_name, fruit_data.get("buy", True))
            var = ctk.BooleanVar(value=is_checked)
            self.fruit_vars[fruit_name] = var
            
            cb = ctk.CTkCheckBox(
                grid_frame,
                text=fruit_name,
                variable=var,
                font=ctk.CTkFont(size=11),
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=4,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                border_color=COLORS["border"]
            )
            cb.grid(row=row, column=col, padx=8, pady=4, sticky="w")
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        for i in range(3):
            grid_frame.columnconfigure(i, weight=1)
        
        # === BUTTONS ===
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Hủy",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text"],
            width=100,
            height=40,
            corner_radius=10,
            command=self.destroy
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frame,
            text="Lưu cài đặt",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["bg_dark"],
            width=150,
            height=40,
            corner_radius=10,
            command=self._save
        ).pack(side="right")
    
    def _create_card(self, parent, title):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="w", padx=15, pady=(12, 5))
        
        return card
    
    def _save(self):
        try:
            threshold = float(self.threshold_entry.get())
        except ValueError:
            threshold = 0.8
        
        config = {
            "enabled": self.enabled_var.get(),
            "use_time_gate": self.time_gate_var.get(),
            "first_run_immediate": self.first_run_var.get(),
            "threshold": threshold,
            "enable_buy_fruits": self.buy_fruits_var.get(),
            "enable_buy_voi": self.buy_voi_var.get(),
            "enable_harvest_sell": self.harvest_var.get(),
            "enable_telegram": self.telegram_var.get(),
            "fruits": {name: var.get() for name, var in self.fruit_vars.items()}
        }
        
        if save_instance_config(self.instance["index"], config):
            # Đóng dialog trước rồi mới gọi callback (để tránh lỗi focus)
            self.destroy()
            if self.on_save:
                # Dùng after để đảm bảo dialog đã đóng hẳn trước khi hiện toast
                self.master.after(10, lambda: self.on_save(self.instance["index"], config))


class LDInstanceRow(ctk.CTkFrame):
    """Widget hiển thị 1 dòng LDPlayer instance"""
    
    def __init__(self, parent, instance: dict, icons: dict, on_config, on_start, on_stop, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=10, **kwargs)
        
        self.instance = instance
        self.icons = icons
        self.on_config = on_config
        self.on_start = on_start
        self.on_stop = on_stop
        self.is_running_automation = False
        
        self._create_ui()
    
    def _create_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=12, pady=8)
        
        # Left: Status indicator + Info
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        
        # Status dot
        status_color = COLORS["success"] if self.instance["running"] else COLORS["text_dim"]
        self.status_dot = ctk.CTkLabel(
            left,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=status_color,
            width=20
        )
        self.status_dot.pack(side="left", padx=(0, 8))
        
        # Info
        info_frame = ctk.CTkFrame(left, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        self.name_label = ctk.CTkLabel(
            info_frame,
            text=f"{self.instance['name']} (#{self.instance['index']})",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
            anchor="w"
        )
        self.name_label.pack(anchor="w")
        
        serial_text = self.instance["serial"] if self.instance["serial"] else "Chưa kết nối"
        serial_color = COLORS["text_dim"] if self.instance["serial"] else COLORS["warning"]
        self.serial_label = ctk.CTkLabel(
            info_frame,
            text=serial_text,
            font=ctk.CTkFont(size=11),
            text_color=serial_color,
            anchor="w"
        )
        self.serial_label.pack(anchor="w")
        
        # Right: Buttons
        right = ctk.CTkFrame(container, fg_color="transparent")
        right.pack(side="right")
        
        self.automation_status = ctk.CTkLabel(
            right,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
            width=80
        )
        self.automation_status.pack(side="left", padx=(0, 10))
        
        self.config_btn = ctk.CTkButton(
            right,
            text="",
            image=self.icons.get("settings"),
            width=40,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
            command=lambda: self.on_config(self.instance)
        )
        self.config_btn.pack(side="left", padx=4)
        
        self.start_btn = ctk.CTkButton(
            right,
            text="",
            image=self.icons.get("play"),
            width=40,
            height=35,
            fg_color=COLORS["success"],
            hover_color="#00cc66",
            corner_radius=8,
            command=lambda: self.on_start(self)
        )
        self.start_btn.pack(side="left", padx=4)
        
        self.stop_btn = ctk.CTkButton(
            right,
            text="",
            image=self.icons.get("stop"),
            width=40,
            height=35,
            fg_color=COLORS["error"],
            hover_color="#ff3333",
            corner_radius=8,
            command=lambda: self.on_stop(self)
        )
        # Ban đầu ẩn nút stop
        self.stop_btn.pack_forget()
        
        if not self.instance["running"] or not self.instance["serial"]:
            self.start_btn.configure(state="disabled")
    
    def set_automation_running(self, running: bool):
        self.is_running_automation = running
        if running:
            self.automation_status.configure(text="Running", text_color=COLORS["success"])
            self.start_btn.pack_forget()
            self.stop_btn.pack(side="left", padx=4)
            self.stop_btn.configure(state="normal")
            self.config_btn.configure(state="disabled")
        else:
            self.automation_status.configure(text="", text_color=COLORS["text_dim"])
            self.stop_btn.pack_forget()
            self.start_btn.pack(side="left", padx=4)
            if self.instance["running"] and self.instance["serial"]:
                self.start_btn.configure(state="normal")
            else:
                self.start_btn.configure(state="disabled")
            self.config_btn.configure(state="normal")
    
    def update_instance(self, instance: dict):
        self.instance = instance
        status_color = COLORS["success"] if instance["running"] else COLORS["text_dim"]
        self.status_dot.configure(text_color=status_color)
        
        serial_text = instance["serial"] if instance["serial"] else "Chưa kết nối"
        serial_color = COLORS["text_dim"] if instance["serial"] else COLORS["warning"]
        self.serial_label.configure(text=serial_text, text_color=serial_color)
        
        if not self.is_running_automation:
            if instance["running"] and instance["serial"]:
                self.start_btn.configure(state="normal")
            else:
                self.start_btn.configure(state="disabled")


class AutoBuyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window config
        self.title("Farmer v5.1")
        self.geometry("1000x550")
        self.minsize(800, 500)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # State
        self.ld_instances = []
        self.ld_rows = {}
        self.automation_processes = {}
        self.automation_threads = {}
        self.stop_events = {}
        self.log_queue = queue.Queue()
        
        # Load icons
        self._load_icons()
        
        # Build UI
        self._create_ui()
        
        # Start log updater
        self._update_log()
    
    def _load_icons(self):
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "ui")
        self.icons = {}
        
        try:
            self.icons["play"] = ctk.CTkImage(
                light_image=Image.open(os.path.join(icon_path, "play.png")),
                dark_image=Image.open(os.path.join(icon_path, "play.png")),
                size=(20, 20)
            )
            self.icons["stop"] = ctk.CTkImage(
                light_image=Image.open(os.path.join(icon_path, "stop.png")),
                dark_image=Image.open(os.path.join(icon_path, "stop.png")),
                size=(18, 18)
            )
            self.icons["refresh"] = ctk.CTkImage(
                light_image=Image.open(os.path.join(icon_path, "refresh.png")),
                dark_image=Image.open(os.path.join(icon_path, "refresh.png")),
                size=(28, 28)
            )
            self.icons["settings"] = ctk.CTkImage(
                light_image=Image.open(os.path.join(icon_path, "setting.png")),
                dark_image=Image.open(os.path.join(icon_path, "setting.png")),
                size=(20, 20)
            )
        except Exception as e:
            print(f"[ERROR] Lỗi load icons: {e}")
            self.icons["play"] = None
            self.icons["stop"] = None
            self.icons["refresh"] = None
            self.icons["settings"] = None
        
        # Hiển thị hướng dẫn khi mở
        self._log("[INFO] Nhấn 'Làm mới' để quét danh sách LDPlayer")
    
    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="Farmer",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Farmer Manager v5.1",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"]
        ).pack(anchor="w")
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            header,
            text="",
            image=self.icons.get("refresh"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            width=50,
            height=50,
            corner_radius=14,
            command=self._refresh_ld_instances
        )
        self.refresh_btn.pack(side="right")
        
        # Main content
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=10)
        
        # LDPlayer list
        list_label = ctk.CTkLabel(
            main,
            text="LDPlayer",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"]
        )
        list_label.pack(anchor="w", pady=(0, 8))
        
        self.ld_list_frame = ctk.CTkScrollableFrame(
            main,
            fg_color=COLORS["bg_card"],
            corner_radius=12
        )
        self.ld_list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Placeholder text
        self.placeholder_label = ctk.CTkLabel(
            self.ld_list_frame,
            text="Nhấn 'Làm mới' để quét danh sách LDPlayer",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"]
        )
        self.placeholder_label.pack(pady=50)
        
        # Log console
        log_label = ctk.CTkLabel(
            main,
            text="Log",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"]
        )
        log_label.pack(anchor="w", pady=(0, 8))
        
        log_frame = ctk.CTkFrame(main, fg_color=COLORS["bg_card"], corner_radius=12, height=150)
        log_frame.pack(fill="x")
        log_frame.pack_propagate(False)
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="transparent",
            text_color=COLORS["text"],
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _refresh_ld_instances(self):
        def refresh():
            self._log("[INFO] Đang quét LDPlayer instances...")
            self.ld_instances = get_ld_instances()
            self.after(0, self._update_ld_list)
        
        threading.Thread(target=refresh, daemon=True).start()
    
    def _update_ld_list(self):
        # Clear
        for widget in self.ld_list_frame.winfo_children():
            widget.destroy()
        self.ld_rows.clear()
        
        if not self.ld_instances:
            ctk.CTkLabel(
                self.ld_list_frame,
                text="Không tìm thấy LDPlayer nào.\nHãy kiểm tra LDPlayer đã được cài đặt.",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_dim"]
            ).pack(pady=50)
            self._log("[CẢNH BÁO] Không tìm thấy LDPlayer")
            return
        
        for instance in self.ld_instances:
            row = LDInstanceRow(
                self.ld_list_frame,
                instance,
                icons=self.icons,
                on_config=self._on_ld_config,
                on_start=self._on_ld_start,
                on_stop=self._on_ld_stop
            )
            row.pack(fill="x", pady=4, padx=8)
            self.ld_rows[instance["index"]] = row
        
        running_count = sum(1 for i in self.ld_instances if i["running"])
        self._log(f"[OK] Tìm thấy {len(self.ld_instances)} LDPlayer ({running_count} đang chạy)")
    
    def _on_ld_config(self, instance):
        self._log(f"[INFO] Mở cấu hình cho {instance['name']}")
        
        def on_save(idx, config):
            self._log(f"[OK] Đã lưu cấu hình cho LD-{idx}")
        
        dialog = InstanceConfigDialog(self, instance, on_save=on_save)
    
    def _on_ld_start(self, row: LDInstanceRow):
        instance = row.instance
        idx = instance["index"]
        
        if not instance["serial"]:
            self._log(f"[LỖI] {instance['name']} chưa kết nối ADB")
            return
        
        self.stop_events[idx] = threading.Event()
        
        def run():
            self._run_automation_for_ld(idx, instance["serial"], row)
        
        thread = threading.Thread(target=run, daemon=True)
        self.automation_threads[idx] = thread
        thread.start()
        
        row.set_automation_running(True)
        self._log(f"[START] Đã bắt đầu automation trên {instance['name']} ({instance['serial']})")
    
    def _on_ld_stop(self, row: LDInstanceRow):
        instance = row.instance
        idx = instance["index"]
        
        if idx in self.stop_events:
            self.stop_events[idx].set()
        
        if idx in self.automation_processes:
            proc = self.automation_processes[idx]
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except:
                    proc.kill()
        
        row.set_automation_running(False)
        self._log(f"[STOP] Đã dừng automation trên {instance['name']}")
    
    def _run_automation_for_ld(self, idx: int, serial: str, row: LDInstanceRow):
        try:
            process = subprocess.Popen(
                ["python", "-u", "main.py", serial, str(idx)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            self.automation_processes[idx] = process
            
            stop_event = self.stop_events.get(idx)
            
            while stop_event and not stop_event.is_set():
                if process.poll() is not None:
                    break
                
                line = process.stdout.readline()
                if line:
                    self.log_queue.put(f"[LD-{idx}] {line.strip()}")
            
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
                
        except Exception as e:
            self._log(f"[LỖI] LD-{idx}: {e}")
        finally:
            self.after(0, lambda: row.set_automation_running(False))
    
    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")
        
    def _update_log(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
        except queue.Empty:
            pass
        finally:
            self.after(100, self._update_log)
    



if __name__ == "__main__":
    app = AutoBuyApp()
    app.mainloop()
