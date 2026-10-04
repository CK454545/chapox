"""Build intro/assets/ from the two official files (DA.png board + Logo.png badge).
Crops are exact boxes measured on the DA board (tools/grid.py). Text the board printed on top of an image
(card arrows, headline letters, pager digits) is inpainted away before the 4x Real-ESRGAN pass.
Nothing is redrawn: every pixel comes from DA.png / Logo.png."""
import sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE.parent / "assets"
TMP = HERE.parent / "tmp"
OUT.mkdir(exist_ok=True); TMP.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))
from upscale import upscale  # noqa: E402

DA = Image.open(ROOT / "DA.png").convert("RGB")
LOGO = Image.open(ROOT / "Logo.png").convert("RGB")


def inpaint(im, boxes, pred=None, rad=4):
    """boxes in the crop's own coords; pred(rgb)->bool mask of text pixels inside the box (default: whole box)."""
    a = np.asarray(im).copy()
    m = np.zeros(a.shape[:2], np.uint8)
    for (x0, y0, x1, y1) in boxes:
        sub = a[y0:y1, x0:x1].astype(int)
        mm = pred(sub) if pred else np.ones(sub.shape[:2], bool)
        m[y0:y1, x0:x1] |= mm.astype(np.uint8)
    m = cv2.dilate(m * 255, np.ones((3, 3), np.uint8), iterations=1)
    return Image.fromarray(cv2.inpaint(a, m, rad, cv2.INPAINT_TELEA))


def bright_or_green(s):
    lum = s.mean(2)
    return (lum > 95) | ((s[:, :, 1] - s[:, :, 2] > 80) & (s[:, :, 1] > 120))


def x4(name, im, model="realesrgan-x4plus-anime"):
    src = TMP / f"src_{name}.png"; im.save(src)
    upscale(str(src), str(OUT / f"{name}.png"), model)


# ---------- project images (DA "PROJETS / EXEMPLES" + "SITE WEB - HOME")
game = DA.crop((775, 802, 881, 889))                       # X.003 GAME
game = inpaint(game, [(91, 74, 106, 87)], bright_or_green)  # card arrow
x4("game", game)
upscale(str(OUT / "game.png"), str(OUT / "game_x16.png"), "realesrgan-x4plus-anime")

app = DA.crop((637, 800, 752, 891))                        # X.002 MOBILE APP
app = inpaint(app, [(98, 74, 115, 89)], lambda s: s.mean(2) > 150)
x4("app", app)

mystery = DA.crop((767, 945, 884, 1002))                   # X.??? image only (its label is re-set in type)
mystery = inpaint(mystery, [(98, 46, 117, 57)], lambda s: s.mean(2) > 120)
x4("mystery", mystery)

site = DA.crop((952, 430, 1233, 686))                      # website hero image (right half of the mockup)
# end of the headline ("T", "MITS.") over the sky, and the 01-04 pager over the rocks
site = inpaint(site, [(0, 0, 80, 95)], bright_or_green, rad=6)
site = inpaint(site, [(252, 150, 285, 222)], lambda s: s.mean(2) > 105)
x4("site_hero", site, "realesrgan-x4plus")

# ---------- brand marks
ico = DA.crop((806, 214, 892, 300))                         # DA "ICONE" (brush X)
x4("x_icon_rgb", ico)
a = np.asarray(Image.open(OUT / "x_icon_rgb.png").convert("RGB")).astype(np.float32)
alpha = np.clip((a[:, :, 1] - a[:, :, 2] - 45) / 120, 0, 1)
rgb = np.clip(a / np.maximum(alpha[..., None], 1e-3), 0, 255)
Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8)).save(OUT / "x_icon.png")
(OUT / "x_icon_rgb.png").unlink()

wm = DA.crop((24, 104, 422, 196))                           # flat wordmark "CHAPO X" (DA hero)
x4("wordmark_rgb", wm, "realesrgan-x4plus")
a = np.asarray(Image.open(OUT / "wordmark_rgb.png").convert("RGB")).astype(np.float32)
H, W, _ = a.shape
white = np.clip((a.min(2) - 120) / 90, 0, 1)
green = np.clip((a[:, :, 1] - a[:, :, 2] - 70) / 110, 0, 1)
green[:, : int(W * 0.78)] = 0                               # the X sits right of CHAPO; ignore green sky glow elsewhere
alpha = np.maximum(white, green)
col = np.where(green[..., None] > white[..., None], np.array([134, 255, 0], np.float32), np.array([245, 245, 245], np.float32))
Image.fromarray(np.dstack([col, alpha * 255]).astype(np.uint8)).save(OUT / "wordmark.png")
(OUT / "wordmark_rgb.png").unlink()

# ---------- the badge (Logo.png) cut to its circle; fit the green ring first
L = np.asarray(LOGO).astype(np.float32)
g = (L[:, :, 1] > 200) & (L[:, :, 0] > 90) & (L[:, :, 0] < 200) & (L[:, :, 2] < 80)
pts = []
cx0, cy0 = 622, 607
for ang in np.linspace(0, 2 * np.pi, 720, endpoint=False):
    rs = np.arange(500, 600)
    xs = (cx0 + rs * np.cos(ang)).astype(int); ys = (cy0 + rs * np.sin(ang)).astype(int)
    ok = (xs >= 0) & (xs < L.shape[1]) & (ys >= 0) & (ys < L.shape[0])
    hit = rs[ok][g[ys[ok], xs[ok]]]
    if len(hit): pts.append((cx0 + hit.max() * np.cos(ang), cy0 + hit.max() * np.sin(ang)))
P = np.array(pts)
A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
b = (P ** 2).sum(1)
cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]
R = float(np.sqrt(c + cx * cx + cy * cy))
print(f"badge ring centre ({cx:.1f},{cy:.1f}) outer radius {R:.1f}")
yy, xx = np.mgrid[0:L.shape[0], 0:L.shape[1]]
d = np.hypot(xx - cx, yy - cy)
alpha = np.clip((R + 2.5 - d) / 2.0, 0, 1)
side = int(np.ceil(R + 4)) * 2
x0, y0 = int(round(cx)) - side // 2, int(round(cy)) - side // 2
badge = np.dstack([L, alpha * 255]).astype(np.uint8)
Image.fromarray(badge).crop((x0, y0, x0 + side, y0 + side)).save(OUT / "badge.png")
print("badge", side, "px square")

for p in sorted(OUT.glob("*.png")):
    im = Image.open(p); print(f"{p.name:18s} {im.size} {im.mode}")

# ---------- X portal: eroded alpha (window inside a neon rim) + the deepest point to zoom through
xa = np.asarray(Image.open(OUT / "x_icon.png"))[:, :, 3]
inner = cv2.erode((xa > 110).astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
inner = cv2.GaussianBlur(inner, (0, 0), 1.0)
Image.fromarray(np.dstack([np.full_like(inner, 255)] * 3 + [inner])).save(OUT / "x_inner.png")
dist = cv2.distanceTransform((inner > 128).astype(np.uint8), cv2.DIST_L2, 5)
yy, xx = np.unravel_index(int(np.argmax(dist)), dist.shape)
import json
json.dump({"x_size": xa.shape[1], "x_core": [int(xx), int(yy)], "x_core_r": float(dist.max())}, open(OUT / "meta.json", "w"))
print("x portal core", xx, yy, "inscribed radius", round(float(dist.max()), 1))

# ---------- grain tile (seeded, tiles seamlessly)
rng = np.random.default_rng(7)
n = rng.normal(128, 38, (256, 256)).clip(0, 255).astype(np.uint8)
Image.fromarray(n).save(OUT / "grain.png")
