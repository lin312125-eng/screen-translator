# -*- coding: utf-8 -*-
"""翻译结果悬浮窗：无边框、置顶、可拖动，展示原文与译文。"""
import tkinter as tk
import tkinter.font as tkfont


class ResultWindow:
    def __init__(self, master: tk.Tk, source: str, translated: str,
                 anchor: tuple = None, title: str = "翻译结果"):
        self.root = master
        self.source = source
        self.translated = translated

        self.win = tk.Toplevel(master)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#1f2937", padx=0, pady=0)

        self._close_cb = None

        # ---- 布局 ----
        body = tk.Frame(self.win, bg="#1f2937")
        body.pack(fill="both", expand=True, padx=14, pady=10)

        title_lbl = tk.Label(body, text=title, bg="#1f2937", fg="#9ca3af",
                             font=("Microsoft YaHei UI", 9))
        title_lbl.pack(anchor="w")

        src_lbl = tk.Label(body, text=source, bg="#1f2937", fg="#9ca3af",
                           font=("Microsoft YaHei UI", 9), justify="left",
                           wraplength=self._wrap_len(source))
        src_lbl.pack(anchor="w", pady=(6, 4))

        sep = tk.Frame(body, bg="#374151", height=1)
        sep.pack(fill="x", pady=4)

        dst_lbl = tk.Label(body, text=translated, bg="#1f2937", fg="#f9fafb",
                           font=("Microsoft YaHei UI", 12, "bold"), justify="left",
                           wraplength=self._wrap_len(translated))
        dst_lbl.pack(anchor="w", pady=(4, 6))

        btns = tk.Frame(body, bg="#1f2937")
        btns.pack(anchor="e")
        self._btn(btns, "复制译文", self._copy_dst).pack(side="left", padx=(0, 6))
        self._btn(btns, "复制原文", self._copy_src).pack(side="left", padx=(0, 6))
        self._btn(btns, "关闭", self.close).pack(side="left")

        # ---- 拖动 & 快捷键 ----
        for w in (self.win, body, title_lbl, src_lbl, dst_lbl, sep, btns):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
        self.win.bind("<Escape>", lambda e: self.close())

        # ---- 显示位置 ----
        self._place(anchor)
        self.win.deiconify()
        self.win.lift()

    # ---------- 工具 ----------
    def _wrap_len(self, text: str) -> int:
        font = tkfont.Font(family="Microsoft YaHei UI", size=12)
        max_w = int(self.root.winfo_screenwidth() * 0.72)
        longest = 0
        for line in text.splitlines():
            longest = max(longest, font.measure(line))
        if longest <= max_w:
            return longest + 40
        return max_w

    def _btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg="#374151", fg="#e5e7eb",
                         activebackground="#4b5563", activeforeground="#ffffff",
                         relief="flat", bd=0, padx=10, pady=3,
                         font=("Microsoft YaHei UI", 9),
                         cursor="hand2")

    def _place(self, anchor):
        self.win.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
        if anchor:
            ax, ay = anchor[0], anchor[1]
            x = min(max(ax, 0), sw - w - 8)
            y = ay + (anchor[3] + 8 if len(anchor) > 3 else 8)
            if y + h > sh - 20:
                y = max(ay - h - 8, 0)
        else:
            x, y = sw - w - 24, 40
        self.win.geometry(f"+{int(x)}+{int(y)}")

    # ---------- 事件 ----------
    def _drag_start(self, event):
        self._dx = event.x
        self._dy = event.y

    def _drag_move(self, event):
        try:
            x = self.win.winfo_x() + event.x - self._dx
            y = self.win.winfo_y() + event.y - self._dy
            self.win.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    def _copy_dst(self):
        self._copy(self.translated)

    def _copy_src(self):
        self._copy(self.source)

    def _copy(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def close(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        if self._close_cb:
            self._close_cb()

    def on_close(self, cb):
        self._close_cb = cb
