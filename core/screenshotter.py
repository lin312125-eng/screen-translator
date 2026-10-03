# -*- coding: utf-8 -*-
"""屏幕截图：全屏遮罩 + 鼠标拖拽选框，截取指定区域（物理像素坐标，已适配 DPI 缩放）。"""
import tkinter as tk

import mss
from PIL import Image


def grab_region(left: int, top: int, width: int, height: int) -> Image.Image:
    with mss.mss() as sct:
        shot = sct.grab({"left": left, "top": top, "width": width, "height": height})
    return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def grab_selection(root: tk.Tk):
    """弹出全屏遮罩让用户拖拽选框。返回 (box, image) 或 (None, None)（用户取消/区域过小）。"""
    mask = tk.Toplevel(root)
    mask.attributes("-fullscreen", True)
    mask.attributes("-alpha", 0.25)
    mask.attributes("-topmost", True)
    mask.overrideredirect(True)
    mask.configure(bg="black", cursor="cross")

    canvas = tk.Canvas(mask, bg="black", highlightthickness=0, cursor="cross")
    canvas.pack(fill="both", expand=True)

    box = {}
    rect_id = [None]

    def on_down(event):
        box["x0"], box["y0"] = event.x_root, event.y_root
        box["x1"], box["y1"] = event.x_root, event.y_root
        if rect_id[0]:
            canvas.delete(rect_id[0])
        rect_id[0] = canvas.create_rectangle(box["x0"], box["y0"], box["x1"], box["y1"],
                                             outline="#38bdf8", width=2, fill="#38bdf8",
                                             stipple="gray50")

    def on_move(event):
        if "x0" not in box:
            return
        box["x1"], box["y1"] = event.x_root, event.y_root
        if rect_id[0]:
            canvas.coords(rect_id[0], box["x0"], box["y0"], box["x1"], box["y1"])

    def on_up(event):
        box["x1"], box["y1"] = event.x_root, event.y_root
        mask.destroy()

    def on_cancel(event):
        box.clear()
        mask.destroy()

    canvas.bind("<ButtonPress-1>", on_down)
    canvas.bind("<B1-Motion>", on_move)
    canvas.bind("<ButtonRelease-1>", on_up)
    canvas.bind("<Escape>", on_cancel)

    root.wait_window(mask)

    if "x0" not in box:
        return None, None
    x0, y0 = min(box["x0"], box["x1"]), min(box["y0"], box["y1"])
    x1, y1 = max(box["x0"], box["x1"]), max(box["y0"], box["y1"])
    w, h = x1 - x0, y1 - y0
    if w < 5 or h < 5:
        return None, None
    img = grab_region(x0, y0, w, h)
    return (x0, y0, w, h), img
