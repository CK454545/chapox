"""Split the X.003 game art (assets/game_x16.png) into two parallax layers:
game_char.png (character cut-out, RGBA) and game_bg.png (background with the character inpainted away).
GrabCut seeded by the character's box (measured with tools/grid.py), run at half size then upscaled."""
from pathlib import Path
import numpy as np
import cv2

A = Path(__file__).resolve().parent.parent / "assets"
img = cv2.imread(str(A / "game_x16.png"))
H, W = img.shape[:2]
small = cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
K = 1696 / 900 / 2          # seeds measured on a 900 px wide preview, applied at half size
P = lambda pts: (np.array(pts, np.float32) * K).astype(np.int32)
mask = np.full(small.shape[:2], cv2.GC_BGD, np.uint8)
cv2.rectangle(mask, (int(318 * K), int(100 * K)), (int(640 * K), int(739 * K)), cv2.GC_PR_BGD, -1)
fgd_shapes = [
    P([(400, 120), (525, 120), (565, 200), (360, 200)]),             # cap dome
    P([(330, 228), (585, 228), (585, 238), (330, 238)]),             # brim
    P([(390, 240), (540, 240), (535, 300), (395, 300)]),             # face
    P([(400, 320), (525, 320), (548, 465), (380, 465)]),             # torso
    P([(368, 390), (385, 390), (382, 485), (366, 485)]),             # left arm
    P([(545, 400), (560, 400), (565, 485), (550, 485)]),             # right arm
    P([(410, 480), (445, 480), (432, 600), (412, 600)]),             # left leg
    P([(478, 480), (515, 480), (508, 600), (486, 600)]),             # right leg
    P([(400, 618), (440, 618), (445, 650), (398, 650)]),             # left shoe
    P([(484, 614), (522, 614), (526, 645), (482, 645)]),             # right shoe
    P([(395, 690), (560, 690), (575, 739), (380, 739)]),             # foreground rock
]
bgd_shapes = [
    P([(440, 540), (476, 540), (480, 612), (436, 612)]),             # ground between the legs
    P([(318, 500), (378, 500), (372, 600), (318, 600)]),             # ground left
    P([(540, 500), (600, 500), (600, 600), (532, 600)]),             # ground right
    P([(447, 615), (480, 615), (484, 684), (444, 684)]),             # ground between the shoes
    P([(330, 110), (378, 110), (372, 150), (330, 150)]),             # sky left of the cap
    P([(340, 300), (382, 305), (376, 365), (340, 380)]),             # sky left of the shoulder
    P([(330, 245), (372, 245), (372, 300), (330, 300)]),             # sky left of the face
    P([(552, 245), (590, 245), (590, 300), (552, 300)]),             # sky right of the face
    P([(548, 110), (590, 110), (590, 150), (552, 150)]),             # sky right of the cap
    P([(568, 380), (600, 380), (600, 470), (572, 470)]),             # sky right of the arm
    P([(318, 640), (345, 640), (335, 739), (318, 739)]),             # ground left of the rock
    P([(612, 640), (640, 640), (640, 739), (622, 739)]),             # ground right of the rock
    P([(318, 100), (370, 100), (330, 220), (318, 220)]),             # sky corners
    P([(560, 100), (592, 100), (592, 215), (590, 215)]),
]
for sh in bgd_shapes: cv2.fillPoly(mask, [sh], cv2.GC_BGD)
for sh in fgd_shapes: cv2.fillPoly(mask, [sh], cv2.GC_FGD)
bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(small, mask, None, bgd, fgd, 10, cv2.GC_INIT_WITH_MASK)
fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
# keep the largest component (the character), fill holes, smooth the edge
n, lab, stats, _ = cv2.connectedComponentsWithStats(fg)
big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
fg = np.where(lab == big, 255, 0).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
# fill only small holes: the gap between the legs and the rock is a real hole and must stay open
n, lab, stats, _ = cv2.connectedComponentsWithStats(255 - fg)
for i in range(1, n):
    if stats[i, cv2.CC_STAT_AREA] < 400: fg[lab == i] = 255
fg = cv2.resize(fg, (W, H), interpolation=cv2.INTER_LINEAR)
alpha = cv2.GaussianBlur(fg, (0, 0), 1.6)
alpha = np.clip((alpha.astype(np.float32) - 60) * 255 / 150, 0, 255).astype(np.uint8)
# the cap pops out of the game window onto black: drop light pink/violet sky pixels left in the top band
top = np.zeros(alpha.shape, bool); top[:400] = True
b, g, r = [img[:, :, i].astype(np.int32) for i in range(3)]
sky = top & (r > 165) & (b > 135) & ((r + g + b) / 3 > 125)
alpha = np.where(sky, 0, alpha).astype(np.uint8)
alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
rgba = np.dstack([img, alpha])
cv2.imwrite(str(A / "game_char.png"), rgba)
# background: inpaint a dilated version of the character region (the layer on top hides the smear)
hole = cv2.dilate((alpha > 8).astype(np.uint8) * 255, np.ones((41, 41), np.uint8))
hs = cv2.resize(hole, (W // 4, H // 4), interpolation=cv2.INTER_NEAREST)
bs = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
fill = cv2.inpaint(bs, hs, 12, cv2.INPAINT_TELEA)
fill = cv2.GaussianBlur(cv2.resize(fill, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 6)
m = (cv2.GaussianBlur(hole, (0, 0), 6).astype(np.float32) / 255)[..., None]
bg = (img * (1 - m) + fill * m).astype(np.uint8)
cv2.imwrite(str(A / "game_bg.jpg"), bg, [cv2.IMWRITE_JPEG_QUALITY, 92])
ys, xs = np.where(alpha > 128)
print("char bbox", xs.min(), ys.min(), xs.max(), ys.max(), "of", W, H)
