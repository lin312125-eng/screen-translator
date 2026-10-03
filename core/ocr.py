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
