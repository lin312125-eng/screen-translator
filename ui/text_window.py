# -*- coding: utf-8 -*-
"""文本翻译窗口：输入即译（带防抖），支持目标语言切换。"""
import queue
import threading
import tkinter as tk
import tkinter.font as tkfont

from core.engines import TranslateError

LANG_NAMES = {
    "zh-CN": "中文(简体)",
    "en": "英语",
    "ja": "日语",
    "ko": "韩语",
    "fr": "法语",
    "de": "德语",
    "es": "西班牙语",
    "ru": "俄语",
    "it": "意大利语",
    "pt": "葡萄牙语",
    "ar": "阿拉伯语",
    "vi": "越南语",
    "th": "泰语",
    "id": "印尼语",
    "tr": "土耳其语",
}


class TextWindow:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.win = tk.Toplevel(self.root)
        self.win.title("文本翻译")
        self.win.geometry("560x420")
        self.win.configure(bg="#111827")
        self.win.resizable(True, True)
        self.win.protocol("WM_DELETE_WINDOW", self._hide)

        self._q = queue.Queue()
        self._debounce = None
        self._running = False

        # ---- 顶栏 ----
        top = tk.Frame(self.win, bg="#111827")
        top.pack(fill="x", padx=12, pady=(10, 6))
        tk.Label(top, text="目标语言:", bg="#111827", fg="#9ca3af",
                 font=("Microsoft YaHei UI", 10)).pack(side="left")
        self.lang_var = tk.StringVar(value=self.app.config.get("target_lang", "zh-CN"))
        lang_menu = tk.OptionMenu(top, self.lang_var, *LANG_NAMES.keys(),
                                  command=self._on_lang_change)
        lang_menu.config(bg="#1f2937", fg="#e5e7eb", highlightthickness=0,
                         activebackground="#374151", font=("Microsoft YaHei UI", 10))
        lang_menu["menu"].config(bg="#1f2937", fg="#e5e7eb")
        lang_menu.pack(side="left", padx=(6, 12))
        self.status_var = tk.StringVar(value="就绪")
        self.status_lbl = tk.Label(top, textvariable=self.status_var, bg="#111827",
                                   fg="#34d399", font=("Microsoft YaHei UI", 9))
        self.status_lbl.pack(side="right")

        # ---- 输入 ----
        tk.Label(self.win, text="原文（输入后自动翻译，Ctrl+Enter 立即翻译）",
                 bg="#111827", fg="#6b7280", font=("Microsoft YaHei UI", 9),
                 anchor="w").pack(fill="x", padx=12)
        self.src = tk.Text(self.win, height=7, wrap="word", bg="#1f2937", fg="#f9fafb",
                           insertbackground="#f9fafb", relief="flat",
                           padx=10, pady=8, font=("Microsoft YaHei UI", 11),
                           highlightthickness=1, highlightbackground="#374151",
                           highlightcolor="#38bdf8")
        self.src.pack(fill="both", expand=True, padx=12, pady=(4, 8))
        self.src.bind("<KeyRelease>", self._on_input)
        self.src.bind("<Control-Return>", self._translate_now)

        # ---- 输出 ----
        self.dst = tk.Text(self.win, height=8, wrap="word", bg="#1f2937", fg="#38bdf8",
                           relief="flat", padx=10, pady=8,
                           font=("Microsoft YaHei UI", 12, "bold"),
                           highlightthickness=1, highlightbackground="#374151")
        self.dst.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.dst.configure(state="disabled")

        # ---- 底部按钮 ----
        bottom = tk.Frame(self.win, bg="#111827")
        bottom.pack(fill="x", padx=12, pady=(0, 10))
        self._btn(bottom, "翻译", self._translate_now).pack(side="left", padx=(0, 8))
        self._btn(bottom, "复制结果", self._copy_result).pack(side="left", padx=(0, 8))
        self._btn(bottom, "清空", self._clear).pack(side="left")
        self._btn(bottom, "关闭", self._hide).pack(side="right")

        self._poll_queue()

    # ---------- 界面工具 ----------
    def _btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg="#374151", fg="#e5e7eb",
                         activebackground="#4b5563", activeforeground="#ffffff",
                         relief="flat", bd=0, padx=12, pady=4,
                         font=("Microsoft YaHei UI", 9), cursor="hand2")

    def _set_dst(self, text, color="#38bdf8"):
        self.dst.configure(state="normal")
        self.dst.delete("1.0", "end")
        self.dst.insert("1.0", text)
        self.dst.configure(state="disabled", fg=color)

    def _set_status(self, text, ok=True):
        self.status_var.set(text)
        self.status_lbl.configure(fg="#34d399" if ok else "#f87171")

    # ---------- 行为 ----------
    def _on_lang_change(self, _):
        self.app.config["target_lang"] = self.lang_var.get()
        from core.config import save as save_cfg
        save_cfg(self.app.config)
        self._translate_now()

    def _on_input(self, _event):
        if self._debounce:
            try:
                self.win.after_cancel(self._debounce)
            except Exception:
                pass
        self._debounce = self.win.after(700, self._translate_now)

    def _translate_now(self, _event=None):
        text = self.src.get("1.0", "end").strip()
        if not text:
            self._set_status("没有可翻译的文本")
            return
        if self._running:
            return
        self._running = True
        self._set_status("翻译中…", ok=True)
        target = self.lang_var.get()

        def work():
            try:
                result = self.app.engine.translate(text, target)
                self._q.put(("ok", result))
            except TranslateError as e:
                self._q.put(("err", str(e)))
            except Exception as e:
                self._q.put(("err", f"翻译失败: {e}"))
            finally:
                self._q.put(("done", None))

        threading.Thread(target=work, daemon=True).start()

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self._q.get_nowait()
                if kind == "ok":
                    self._set_dst(payload)
                    self._set_status("完成", ok=True)
                elif kind == "err":
                    self._set_dst(payload, color="#f87171")
                    self._set_status("出错", ok=False)
                elif kind == "done":
                    self._running = False
        except queue.Empty:
            pass
        self.win.after(100, self._poll_queue)

    # ---------- 其他 ----------
    def _copy_result(self):
        try:
            text = self.dst.get("1.0", "end").strip()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self._set_status("已复制", ok=True)
        except tk.TclError:
            pass

    def _clear(self):
        self.src.delete("1.0", "end")
        self._set_dst("")
        self._set_status("就绪", ok=True)

    def _hide(self):
        self.win.withdraw()

    def show(self):
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
