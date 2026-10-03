# -*- coding: utf-8 -*-
"""屏幕实时翻译监控器。

后台线程循环：截图监控区域 → 低成本差异检测（无变化则跳过）→ OCR 识别文本块
→ 仅翻译新增/变化的文本（带缓存）→ 通过回调把译文块交给主线程绘制覆盖层。
"""
import threading
import time

import numpy as np

from core.engines import TranslateError
from core.screenshotter import grab_region

# 差异检测阈值：缩放后平均像素差小于该值视为屏幕未变化
DIFF_THRESHOLD = 2.0


class ScreenMonitor:
    def __init__(self, ocr, engine, config, on_update):
        """
        on_update(blocks, region) -> 在主线程中调用。
        blocks: [(left, top, width, height, source_text, translated_text), ...]（屏幕坐标）
        """
        self.ocr = ocr
        self.engine = engine
        self.config = config
        self.on_update = on_update
        self.region = None
        self._thread = None
        self._stop = threading.Event()
        self._prev_small = None
        self._cache = {}

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, region):
        if self.running:
            return
        self.region = region
        self._prev_small = None
        self._cache = {}
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        self._thread = None

    # ---------------- 主循环 ----------------
    def _loop(self):
        interval = max(1.0, float(self.config.get("monitor_interval", 2.5)))
        while not self._stop.is_set():
            t0 = time.time()
            try:
                self._tick()
            except Exception as e:
                print(f"[monitor] tick error: {e}")
            elapsed = time.time() - t0
            self._stop.wait(max(0.1, interval - elapsed))

    def _tick(self):
        region = self.region
        if not region:
            return
        left, top, width, height = region

        shot = grab_region(left, top, width, height)

        # ---- 差异检测：缩略图对比，无明显变化则跳过 ----
        small = shot.resize((max(1, width // 4), max(1, height // 4))).convert("L")
        arr = np.asarray(small, dtype=np.int16)
        if self._prev_small is not None:
            diff = float(np.mean(np.abs(arr - self._prev_small)))
            if diff < DIFF_THRESHOLD:
                return
        self._prev_small = arr

        # ---- OCR ----
        blocks = self.ocr.recognize_boxes(shot)  # [(l, t, w, h, text)]（区域内坐标）
        if not blocks:
            return

        # ---- 语言过滤 + 缓存翻译 ----
        target = self.config.get("target_lang", "zh-CN")
        results = [None] * len(blocks)
        new_texts, new_indices = [], []

        for i, (l, t, w, h, text) in enumerate(blocks):
            if not self._should_translate(text, target):
                continue
            if text in self._cache:
                results[i] = self._cache[text]
            else:
                new_texts.append(text)
                new_indices.append(i)

        # 新增文本合并为一次批量请求，响应按行对应
        if new_texts:
            try:
                combined = "\n".join(new_texts)
                translated = self.engine.translate(combined, target)
                parts = translated.split("\n")
                for k, idx in enumerate(new_indices):
                    tr = (parts[k] if k < len(parts) else (parts[-1] if parts else "")).strip()
                    self._cache[new_texts[k]] = tr
                    results[idx] = tr
            except TranslateError as e:
                # 翻译失败：记录缓存避免反复请求
                for k, idx in enumerate(new_indices):
                    self._cache[new_texts[k]] = ""
                print(f"[monitor] translate error: {e}")

        # ---- 组装译文块（屏幕坐标）并回调 ----
        out = []
        for (l, t, w, h, text), tr in zip(blocks, results):
            if not tr or tr == text:
                continue
            out.append((left + l, top + t, w, h, text, tr))
        if out:
            self.on_update(out, region)

    # ---------------- 工具 ----------------
    @staticmethod
    def _should_translate(text: str, target_lang: str) -> bool:
        """目标为中文时只翻译以外文（拉丁字母）为主的文本块，避免把覆盖层译文再识别翻译。"""
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return False
        if target_lang == "zh-CN":
            latin = sum(1 for c in letters if ord(c) < 0x2E80)
            return latin / len(letters) > 0.6
        return True
