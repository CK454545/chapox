"""Draw a labelled coordinate grid over a region of an image (to pick exact crop boxes).
usage: python grid.py src.png x0 y0 x1 y1 out.png [scale] [step]"""
import sys
from PIL import Image, ImageDraw

src, x0, y0, x1, y1, out = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
S = int(sys.argv[7]) if len(sys.argv) > 7 else 3
step = int(sys.argv[8]) if len(sys.argv) > 8 else 10
im = Image.open(src).convert("RGB").crop((x0, y0, x1, y1))
im = im.resize((im.width * S, im.height * S), Image.NEAREST)
d = ImageDraw.Draw(im)
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * S
    d.line([(X, 0), (X, im.height)], fill=(255, 0, 255) if x % (step * 5) == 0 else (90, 0, 90), width=1)
    if x % (step * 5) == 0: d.text((X + 2, 2), str(x), fill=(255, 255, 0))
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * S
    d.line([(0, Y), (im.width, Y)], fill=(0, 255, 255) if y % (step * 5) == 0 else (0, 90, 90), width=1)
    if y % (step * 5) == 0: d.text((2, Y + 2), str(y), fill=(255, 255, 0))
im.save(out)
