# -*- coding: utf-8 -*-
"""生成应用图标 assets/icon.ico（用于打包 exe）。"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "icon.ico")


def make(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * 0.22)
    draw.rounded_rectangle((2, 2, size - 2, size - 2), radius=radius, fill=(37, 99, 235))
    font_path = "C:/Windows/Fonts/msyh.ttc"
    if os.path.exists(font_path):
        font = ImageFont.truetype(font_path, int(size * 0.55))
        draw.text((size / 2, size / 2), "译", font=font, fill="white", anchor="mm")
    else:
        draw.text((size * 0.3, size * 0.25), "译", fill="white")
    return img


if __name__ == "__main__":
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    first = make(256)
    first.save(OUT, format="ICO", sizes=sizes)
    print(f"icon written: {OUT}")
