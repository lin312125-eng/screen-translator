# -*- coding: utf-8 -*-
"""本地 OCR：基于 RapidOCR（PP-OCR 模型，纯本地运行、免费、无需 Key，中英文识别）。"""
import threading

import numpy as np
from PIL import Image


class OCR:
    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()

    def _get_engine(self):
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    from rapidocr_onnxruntime import RapidOCR
                    self._engine = RapidOCR()
        return self._engine

    def recognize(self, pil_image: Image.Image) -> str:
        """识别图片中的文字，按阅读顺序逐行拼接。"""
        engine = self._get_engine()
        img = np.array(pil_image.convert("RGB"))
        result, _ = engine(img)
        if not result:
            return ""
        lines = [str(item[1]) for item in result if len(item) >= 2 and item[1]]
        return "\n".join(lines).strip()

    def recognize_boxes(self, pil_image: Image.Image):
        """识别并返回带坐标的文本块：[(left, top, width, height, text), ...]（像素坐标）。"""
        engine = self._get_engine()
        img = np.array(pil_image.convert("RGB"))
        result, _ = engine(img)
        blocks = []
        for item in result or []:
            if len(item) < 2 or not item[1]:
                continue
            box = item[0]
            text = str(item[1])
            try:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
            except (TypeError, IndexError):
                continue
            left, top = int(min(xs)), int(min(ys))
            right, bottom = int(max(xs)), int(max(ys))
            if right - left < 4 or bottom - top < 4:
                continue
            blocks.append((left, top, right - left, bottom - top, text))
        return blocks
