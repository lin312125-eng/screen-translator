# -*- coding: utf-8 -*-
"""随译 ScreenTranslator —— Windows 桌面翻译小工具。

功能：
  - 截图翻译：Ctrl+Shift+T 框选屏幕区域，OCR 识别并翻译，结果悬浮窗显示
  - 剪贴板翻译：Ctrl+Shift+C 直接翻译剪贴板文本
  - 文本翻译：Ctrl+Shift+W 打开文本翻译窗口，输入即译
  - 设置：Ctrl+Shift+S（切换翻译引擎 / 配置大模型 API / 热键）
"""
import ctypes
import os
import queue
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

import keyboard
import pystray
from PIL import Image, ImageDraw, ImageFont

from core.config import APP_NAME, APP_VERSION, load as load_config
from core.engines import TranslateError, create_engine
from core.ocr import OCR
from core.screenshotter import grab_selection
from ui.result_window import ResultWindow
from ui.settings_window import SettingsWindow
from ui.text_window import TextWindow


def enable_dpi_awareness():
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(APP_NAME)

        self.config = load_config()
        self.engine = create_engine(self.config)
        self.ocr = OCR()
        self.q = queue.Queue()
        self.tray = None
        self.text_window = None
        self.result_windows = []

        self._poll_queue()
        self._register_hotkeys(self.config.get("hotkeys", {}))
        self._setup_tray()

    # ================= 队列调度 =================
    def _poll_queue(self):
        try:
            while True:
                task = self.q.get_nowait()
                self._handle(task)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _handle(self, task):
        kind = task[0]
        if kind == "screenshot":
            self.start_screenshot_translate()
        elif kind == "clipboard":
            self.translate_clipboard()
        elif kind == "text":
            self.open_text_window()
        elif kind == "settings":
            self.open_settings()
        elif kind == "ocr_result":
            _, box, source, translated = task
            self.show_result(box, source, translated)
        elif kind == "translate_result":
            _, source, translated, anchor = task
            self.show_result(anchor, source, translated)
        elif kind == "error":
            messagebox.showerror(APP_NAME, task[1])

    # ================= 功能：截图翻译 =================
    def start_screenshot_translate(self):
        try:
            box, image = grab_selection(self.root)
        except Exception as e:
            self.q.put(("error", f"截图失败: {e}"))
            return
        if box is None:
            return

        def work():
            try:
                source = self.ocr.recognize(image)
                if not source.strip():
                    self.q.put(("error", "没有识别到文字，请框选更清晰的区域"))
                    return
                translated = self.engine.translate(source, self.config["target_lang"])
                self.q.put(("ocr_result", box, source, translated))
            except TranslateError as e:
                self.q.put(("error", str(e)))
            except Exception as e:
                self.q.put(("error", f"识别/翻译失败: {e}"))

        threading.Thread(target=work, daemon=True).start()

    # ================= 功能：剪贴板翻译 =================
    def translate_clipboard(self):
        try:
            text = self.root.clipboard_get()
        except Exception:
            self.q.put(("error", "剪贴板中没有可翻译的文本"))
            return
        text = (text or "").strip()
        if not text:
            self.q.put(("error", "剪贴板中没有可翻译的文本"))
            return
        self._translate_async(text)

    # ================= 功能：通用翻译 =================
    def _translate_async(self, text):
        target = self.config["target_lang"]

        def work():
            try:
                translated = self.engine.translate(text, target)
                self.q.put(("translate_result", text, translated, None))
            except TranslateError as e:
                self.q.put(("error", str(e)))
            except Exception as e:
                self.q.put(("error", f"翻译失败: {e}"))

        threading.Thread(target=work, daemon=True).start()

    # ================= 结果悬浮窗 =================
    def show_result(self, anchor, source, translated):
        win = ResultWindow(self.root, source, translated, anchor=anchor)
        self.result_windows.append(win)
        win.on_close(lambda w=win: self._remove_result(w))

    def _remove_result(self, win):
        if win in self.result_windows:
            self.result_windows.remove(win)

    # ================= 窗口：文本翻译 / 设置 =================
    def open_text_window(self):
        if self.text_window is None:
            self.text_window = TextWindow(self)
        self.text_window.show()

    def open_settings(self):
        SettingsWindow(self)

    def apply_settings(self):
        """设置保存后调用：重建翻译引擎、重注册热键。"""
        self.engine = create_engine(self.config)
        self._register_hotkeys(self.config.get("hotkeys", {}))
        if self.text_window is not None:
            self.text_window.lang_var.set(self.config["target_lang"])

    # ================= 热键 =================
    def _register_hotkeys(self, hk):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        handlers = {
            "screenshot": lambda: self.q.put(("screenshot",)),
            "clipboard": lambda: self.q.put(("clipboard",)),
            "text": lambda: self.q.put(("text",)),
            "settings": lambda: self.q.put(("settings",)),
        }
        for name, key in hk.items():
            if not key or name not in handlers:
                continue
            try:
                keyboard.add_hotkey(key, handlers[name])
            except Exception as e:
                print(f"[hotkey] {name} ({key}) 注册失败: {e}")

    # ================= 托盘 =================
    def _setup_tray(self):
        icon_image = self._make_icon()
        menu = pystray.Menu(
            pystray.MenuItem("截图翻译 (Ctrl+Shift+T)", lambda: self.q.put(("screenshot",))),
            pystray.MenuItem("翻译剪贴板 (Ctrl+Shift+C)", lambda: self.q.put(("clipboard",))),
            pystray.MenuItem("文本翻译 (Ctrl+Shift+W)", lambda: self.q.put(("text",))),
            pystray.MenuItem("设置 (Ctrl+Shift+S)", lambda: self.q.put(("settings",))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._quit),
        )
        self.tray = pystray.Icon(APP_NAME, icon_image, APP_NAME, menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def _make_icon(self) -> Image.Image:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((2, 2, 62, 62), radius=14, fill=(37, 99, 235))
        font_path = "C:/Windows/Fonts/msyh.ttc"
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 34)
                draw.text((32, 32), "译", font=font, fill="white", anchor="mm")
            except Exception:
                draw.text((20, 12), "译", fill="white")
        else:
            draw.text((20, 12), "译", fill="white")
        return img

    def _quit(self, *_):
        self.root.after(0, self._really_quit)

    def _really_quit(self):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        if self.tray:
            try:
                self.tray.stop()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)


def main():
    enable_dpi_awareness()
    app = App()
    app.root.mainloop()


if __name__ == "__main__":
    main()
