# -*- coding: utf-8 -*-
"""全屏透明译文覆盖层：在原文下方绘制半透明译文块，透明区域鼠标可穿透。"""
import tkinter as tk

# 透明色（用于 attributes("-transparentcolor")，该颜色区域不显示且鼠标穿透）
TRANSPARENT = "#010203"
FILL = "#1e40af"
BORDER = "#3b82f6"
FONT = ("Microsoft YaHei UI", 10)


class OverlayWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", TRANSPARENT)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.win.geometry(f"{sw}x{sh}+0+0")
        self.canvas = tk.Canvas(self.win, bg=TRANSPARENT, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.win.deiconify()
        self.win.lift()

    def update_blocks(self, blocks, region):
        """blocks: [(left, top, width, height, src, tr)]（屏幕坐标）；region: 监控区域。"""
        self.canvas.delete("all")
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        for left, top, width, height, src, tr in blocks:
            if top + height + 4 > sh - 40:  # 超出屏幕下缘则显示在原文上方
                y = top - self._estimate_height(tr) - 4
            else:
                y = top + height + 4
            x = min(max(left, 0), sw - 8)
            self._draw_block(x, y, width, tr)
        self._draw_status(region)
        self.win.lift()

    def _draw_block(self, x, y, width, text):
        w = max(min(width + 12, self.root.winfo_screenwidth() - x - 8), 60)
        h = self._estimate_height(text, w)
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=FILL,
                                     outline=BORDER, width=1, stipple="gray50")
        self.canvas.create_text(x + 6, y + 4, text=text, anchor="nw", fill="#ffffff",
                                width=w - 12, font=FONT)

    def _estimate_height(self, text, width=None):
        lines = len(text.splitlines())
        if width is None:
            return lines * 18 + 8
        # 简单估算换行数：每行约容纳 (width / 11) 个中文字符
        per_line = max(int((width - 12) / 11), 4)
        total = 0
        for line in text.splitlines():
            total += max(1, -(-len(line) // per_line))  # 向上取整
        return total * 16 + 8

    def _draw_status(self, region):
        sw = self.root.winfo_screenwidth()
        text = f"屏幕实时翻译中 · 监控区域 {region[2]}x{region[3]} · 按 Esc 停止"
        x, y = sw - 320, 8
        h = 28
        self.canvas.create_rectangle(x, y, x + 310, y + h, fill="#0f172a",
                                     outline="#38bdf8", width=1)
        self.canvas.create_text(x + 8, y + h / 2, text=text, anchor="w", fill="#38bdf8",
                                font=("Microsoft YaHei UI", 9))

    def destroy(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass
