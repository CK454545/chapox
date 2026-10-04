"""Real-ESRGAN x4plus on CPU (ncnn), weights bundled in the realesrgan-ncnn-py wheel.
usage: python upscale.py in.png out.png [model]   (model: realesrgan-x4plus | realesrgan-x4plus-anime)
Tiled (128 px + 12 px pad) so memory stays small. Alpha (if any) is upscaled with Lanczos."""
import os, sys, time
import numpy as np
import ncnn
from PIL import Image
import importlib.util

MD = os.path.join(os.path.dirname(importlib.util.find_spec("realesrgan_ncnn_py").origin), "models")


def make_net(model):
    net = ncnn.Net()
    net.opt.use_vulkan_compute = False
    net.opt.num_threads = os.cpu_count() or 4
    for k in ("use_fp16_storage", "use_fp16_packed", "use_fp16_arithmetic", "use_bf16_storage"):
        setattr(net.opt, k, False)  # fp16 overflows on bright tiles (x4plus output saturates to white)
    net.load_param(os.path.join(MD, model + ".param"))
    net.load_model(os.path.join(MD, model + ".bin"))
    return net


def run_tile(net, rgb):  # rgb float32 HxWx3 in 0..1
    h, w, _ = rgb.shape
    px = np.ascontiguousarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    m = ncnn.Mat.from_pixels(px, ncnn.Mat.PixelType.PIXEL_RGB, w, h)  # aligned cstep, unlike Mat(numpy)
    m.substract_mean_normalize([], [1 / 255.0] * 3)
    ex = net.create_extractor()
    ex.input("data", m)
    _, out = ex.extract("output")
    o = np.stack([np.array(out.channel(c)) for c in range(out.c)], 2)
    return o.reshape(out.h, out.w, out.c)


def upscale(src, dst, model="realesrgan-x4plus", tile=128, pad=12):
    im = Image.open(src)
    alpha = im.getchannel("A") if im.mode == "RGBA" else None
    rgb = np.asarray(im.convert("RGB"), np.float32) / 255.0
    H, W, _ = rgb.shape
    S = 4
    out = np.zeros((H * S, W * S, 3), np.float32)
    net = make_net(model)
    t0 = time.time()
    for y in range(0, H, tile):
        for x in range(0, W, tile):
            y0, x0 = max(0, y - pad), max(0, x - pad)
            y1, x1 = min(H, y + tile + pad), min(W, x + tile + pad)
            o = run_tile(net, rgb[y0:y1, x0:x1])
            ty1, tx1 = min(H, y + tile), min(W, x + tile)
            out[y * S:ty1 * S, x * S:tx1 * S] = o[(y - y0) * S:(ty1 - y0) * S, (x - x0) * S:(tx1 - x0) * S]
    res = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    if alpha is not None:
        res.putalpha(alpha.resize(res.size, Image.LANCZOS))
    res.save(dst)
    print(f"{src} {W}x{H} -> {dst} {W * S}x{H * S} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    upscale(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or []))
