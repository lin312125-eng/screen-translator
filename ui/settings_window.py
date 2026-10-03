# -*- coding: utf-8 -*-
"""设置窗口：翻译引擎、大模型 API 配置、目标语言、全局热键。"""
import tkinter as tk
import tkinter.ttk as ttk

from core.config import save as save_cfg
from ui.text_window import LANG_NAMES

ENGINES = [
    ("auto", "自动（推荐：DeepL → Bing → Google 自动切换，无需 Key）"),
    ("deepl", "DeepL 免费接口（无需 Key，国内直连）"),
    ("bing", "Bing 免费接口（无需 Key）"),
    ("google", "Google 免费接口（无需 Key，国内需代理）"),
    ("llm", "大模型 API（豆包 / DeepSeek / OpenAI，需 Key，效果最好）"),
]

HOTKEY_HINTS = {
    "screenshot": "截图翻译",
    "clipboard": "翻译剪贴板",
    "text": "文本翻译窗口",
    "settings": "设置窗口",
}


class SettingsWindow:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.cfg = app.config
        self.win = tk.Toplevel(self.root)
        self.win.title("设置")
        self.win.geometry("540x760")
        self.win.configure(bg="#111827")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)

        body = tk.Frame(self.win, bg="#111827")
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ======== 翻译引擎 ========
        self._section(body, "翻译引擎")
        self.engine_var = tk.StringVar(value=self.cfg.get("engine", "auto"))
        for value, label in ENGINES:
            rb = tk.Radiobutton(body, text=label, variable=self.engine_var, value=value,
                                bg="#111827", fg="#e5e7eb", selectcolor="#111827",
                                activebackground="#111827", activeforeground="#ffffff",
                                font=("Microsoft YaHei UI", 10), anchor="w",
                                command=self._on_engine_change)
            rb.pack(fill="x", padx=(8, 0), pady=2)

        # ======== 大模型 API ========
        self._section(body, "大模型 API（选“大模型 API”时生效）")
        llm = self.cfg.get("llm", {})
        form = tk.Frame(body, bg="#111827")
        form.pack(fill="x", padx=(8, 0), pady=2)
        self._row(form, 0, "接口地址", "base_url", llm.get("base_url", ""))
        self._row(form, 1, "API Key", "api_key", llm.get("api_key", ""), secret=True)
        self._row(form, 2, "模型名称", "model", llm.get("model", ""))
        tip = tk.Label(body, text="豆包(火山方舟)示例：\n接口 https://ark.cn-beijing.volces.com/api/v3\n模型 方舟控制台创建的接入点 ID（如 doubao-seed-1-6-250615）\n\nDeepSeek 示例：\n接口 https://api.deepseek.com  模型 deepseek-chat",
                       bg="#111827", fg="#6b7280", justify="left",
                       font=("Microsoft YaHei UI", 9))
        tip.pack(anchor="w", padx=(8, 0), pady=(2, 6))

        # ======== 目标语言 ========
        self._section(body, "目标语言")
        lang_row = tk.Frame(body, bg="#111827")
        lang_row.pack(fill="x", padx=(8, 0), pady=2)
        self.lang_var = tk.StringVar(value=self.cfg.get("target_lang", "zh-CN"))
        menu = tk.OptionMenu(lang_row, self.lang_var, *LANG_NAMES.keys())
        menu.config(bg="#1f2937", fg="#e5e7eb", highlightthickness=0,
                    activebackground="#374151", font=("Microsoft YaHei UI", 10))
        menu["menu"].config(bg="#1f2937", fg="#e5e7eb")
        menu.pack(side="left")

        # ======== 行为选项 ========
        self._section(body, "行为")
        self.auto_clip_var = tk.BooleanVar(value=self.cfg.get("auto_translate_clipboard", True))
        cb = tk.Checkbutton(body, text="复制文本时自动翻译（在任何应用里 Ctrl+C 即弹译文）",
                            variable=self.auto_clip_var, bg="#111827", fg="#e5e7eb",
                            selectcolor="#111827", activebackground="#111827",
                            activeforeground="#ffffff",
                            font=("Microsoft YaHei UI", 10), anchor="w")
        cb.pack(fill="x", padx=(8, 0), pady=2)
        int_row = tk.Frame(body, bg="#111827")
        int_row.pack(fill="x", padx=(8, 0), pady=2)
        tk.Label(int_row, text="实时翻译刷新间隔(秒):", bg="#111827", fg="#9ca3af",
                 font=("Microsoft YaHei UI", 10)).pack(side="left")
        self.interval_var = tk.StringVar(value=str(self.cfg.get("monitor_interval", 2.5)))
        sp = tk.Spinbox(int_row, from_=1.0, to=10.0, increment=0.5, width=6,
                        textvariable=self.interval_var, bg="#1f2937", fg="#f9fafb",
                        insertbackground="#f9fafb", buttonbackground="#374151",
                        relief="flat", highlightthickness=1, highlightbackground="#374151",
                        font=("Microsoft YaHei UI", 10))
        sp.pack(side="left", padx=(6, 0))
        tk.Label(int_row, text="（越小越灵敏，CPU 占用越高）", bg="#111827", fg="#6b7280",
                 font=("Microsoft YaHei UI", 9)).pack(side="left", padx=(8, 0))

        # ======== 全局热键 ========
        self._section(body, "全局热键（格式示例：ctrl+shift+t）")
        hk = self.cfg.get("hotkeys", {})
        self.hk_vars = {}
        for i, (key, hint) in enumerate(HOTKEY_HINTS.items()):
            row = tk.Frame(body, bg="#111827")
            row.pack(fill="x", padx=(8, 0), pady=2)
            tk.Label(row, text=f"{hint}:", width=14, anchor="w", bg="#111827",
                     fg="#9ca3af", font=("Microsoft YaHei UI", 10)).pack(side="left")
            var = tk.StringVar(value=hk.get(key, ""))
            ent = tk.Entry(row, textvariable=var, bg="#1f2937", fg="#f9fafb",
                           insertbackground="#f9fafb", relief="flat",
                           highlightthickness=1, highlightbackground="#374151",
                           font=("Microsoft YaHei UI", 10), width=28)
            ent.pack(side="left", padx=(6, 0))
            self.hk_vars[key] = var

        # ======== 保存 ========
        btns = tk.Frame(self.win, bg="#111827")
        btns.pack(fill="x", padx=16, pady=(0, 14))
        self._btn(btns, "保存并应用", self._save).pack(side="left", padx=(0, 8))
        self._btn(btns, "取消", self.win.destroy).pack(side="left")

        self._on_engine_change()

    # ---------- 构建工具 ----------
    def _section(self, parent, text):
        tk.Label(parent, text=text, bg="#111827", fg="#38bdf8", anchor="w",
                 font=("Microsoft YaHei UI", 10, "bold")).pack(fill="x", pady=(8, 2))

    def _row(self, parent, row, label, key, value, secret=False):
        tk.Label(parent, text=label, width=10, anchor="e", bg="#111827",
                 fg="#9ca3af", font=("Microsoft YaHei UI", 10)).grid(
            row=row, column=0, sticky="e", padx=(0, 8), pady=3)
        var = tk.StringVar(value=value)
        ent = tk.Entry(parent, textvariable=var, bg="#1f2937", fg="#f9fafb",
                       insertbackground="#f9fafb", relief="flat", show="*" if secret else "",
                       highlightthickness=1, highlightbackground="#374151",
                       font=("Microsoft YaHei UI", 10), width=36)
        ent.grid(row=row, column=1, sticky="w", pady=3)
        setattr(self, f"llm_{key}", var)

    def _btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg="#374151", fg="#e5e7eb",
                         activebackground="#4b5563", activeforeground="#ffffff",
                         relief="flat", bd=0, padx=14, pady=5,
                         font=("Microsoft YaHei UI", 9), cursor="hand2")

    # ---------- 行为 ----------
    def _on_engine_change(self):
        # 引擎切换时仅更新界面提示（校验在保存时进行）
        pass

    def _save(self):
        cfg = self.cfg
        cfg["engine"] = self.engine_var.get()
        cfg["llm"]["base_url"] = self.llm_base_url.get().strip()
        cfg["llm"]["api_key"] = self.llm_api_key.get().strip()
        cfg["llm"]["model"] = self.llm_model.get().strip()
        cfg["target_lang"] = self.lang_var.get()
        cfg["auto_translate_clipboard"] = bool(self.auto_clip_var.get())
        try:
            cfg["monitor_interval"] = float(self.interval_var.get())
        except ValueError:
            pass
        new_hk = {}
        for key, var in self.hk_vars.items():
            val = var.get().strip().lower()
            new_hk[key] = val
        cfg["hotkeys"] = new_hk
        save_cfg(cfg)
        self.app.apply_settings()
        self.win.destroy()
