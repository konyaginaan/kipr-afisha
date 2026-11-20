"""Слои сцены из исходников ChatGPT (art/src/*.png, не в git) → art/*.webp.

  python3 art/build.py

Лист с несколькими вырезками (sheet.png) режется по прозрачности на отдельные
куски: sheet-1.webp, sheet-2.webp … слева направо, сверху вниз.
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "src"
WIDTH = {"back": 1600, "village": 1000, "boat": 420, "sheet": 520}


def trim(im):
    return im.crop(im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()) if im.mode == "RGBA" else im


def save(im, name, width):
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(HERE / f"{name}.webp", quality=82, method=6)
    print(name, im.size)


def split(im):
    """Куски листа: связные области непрозрачных пикселей (по уменьшенной маске)."""
    small = im.getchannel("A").resize((im.width // 8, im.height // 8)).point(lambda a: 255 if a > 20 else 0)
    w, h = small.size
    px, seen, boxes = small.load(), set(), []
    for y in range(h):
        for x in range(w):
            if px[x, y] and (x, y) not in seen:
                stack, box = [(x, y)], [x, y, x, y]
                seen.add((x, y))
                while stack:
                    cx, cy = stack.pop()
                    box = [min(box[0], cx), min(box[1], cy), max(box[2], cx), max(box[3], cy)]
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and px[nx, ny] and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                if (box[2] - box[0]) * (box[3] - box[1]) > 60:
                    boxes.append(box)
    boxes.sort(key=lambda b: (b[1] // 40, b[0]))
    for b in boxes:
        yield trim(im.crop((max(0, b[0] * 8 - 8), max(0, b[1] * 8 - 8), min(im.width, b[2] * 8 + 16), min(im.height, b[3] * 8 + 16))))


for src in sorted(SRC.glob("*.png")):
    name = src.stem
    if name == "avatar":
        continue
    im = Image.open(src)
    if name == "sheet":
        # порядок кусков листа: кипарисы, солнце, лавка, ёлка
        for part, n in zip(split(im.convert("RGBA")), ["cypress", "sun", "stall", "tree"]):
            save(part, n, WIDTH["sheet"])
    else:
        save(trim(im), name, WIDTH.get(name, 800))
