"""Contact sheet of intro/assets on a dark checker (shows alpha edges). usage: python contact.py out.png [names...]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

A = Path(__file__).resolve().parent.parent / "assets"
names = sys.argv[2:] or sorted(p.stem for p in A.glob("*.png"))
cell = 420
cols = 3
rows = -(-len(names) // cols)
sheet = Image.new("RGB", (cols * cell, rows * (cell + 24)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    im = Image.open(A / f"{n}.png").convert("RGBA")
    im.thumbnail((cell - 10, cell - 10), Image.LANCZOS)
    bg = Image.new("RGBA", im.size)
    bd = ImageDraw.Draw(bg)
    for y in range(0, im.height, 16):
        for x in range(0, im.width, 16):
            bd.rectangle([x, y, x + 15, y + 15], fill=(70, 70, 70, 255) if (x // 16 + y // 16) % 2 else (25, 25, 25, 255))
    bg.alpha_composite(im)
    cx, cy = (i % cols) * cell + 5, (i // cols) * (cell + 24) + 5
    sheet.paste(bg.convert("RGB"), (cx, cy))
    d.text((cx, cy + cell - 4), f"{n} {Image.open(A / f'{n}.png').size}", fill=(255, 255, 0))
sheet.save(sys.argv[1])
