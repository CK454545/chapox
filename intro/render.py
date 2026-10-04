"""CHAPO X intro renderer (Playwright Chromium -> frames -> ffmpeg).
  python render.py probe 0 0.3 0.7 ...     -> tmp/probe/sheet.png (stills at given times)
  python render.py beats                    -> one still per beat of the 160 BPM grid
  python render.py draft                    -> out/draft.mp4 (30 fps, 1 capture/frame, 540x960, judge rhythm)
  python render.py full [procs]             -> frames/ (60 fps, adaptive motion-blur subframes, parallel chunks)
  python render.py encode                   -> out/chapox_intro.mp4 (H.264 + AAC from out/audio.wav)
  python render.py pops [file]              -> single-frame pops / one-frame flashes scan
Each output frame averages N subframes spread over SHUTTER of the frame interval (180 deg = 0.5)."""
import asyncio, functools, http.server, os, shutil, subprocess, sys, threading, time
from pathlib import Path
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", 8781))
URL = f"http://127.0.0.1:{PORT}/chapox_intro.html?render=1"
W, H, FPS, T = 1080, 1920, 60, 9.0
NFR = int(round(T * FPS))                      # 540 frames, last one at 8.9833 s
CHROME = "/opt/pw-browsers/chromium"
# adaptive motion blur: (start, end, subframes, shutter) - dense only where things move fast
SUB = [(0.00, 0.10, 8, .5), (0.10, 0.50, 3, .5), (0.50, 0.90, 14, .7), (0.90, 1.70, 4, .5), (1.70, 2.62, 12, .7),
       (2.62, 3.55, 4, .5), (3.55, 4.70, 10, .55), (4.70, 5.12, 3, .5), (5.12, 6.16, 10, .55), (6.16, 6.45, 3, .5),
       (6.45, 7.12, 12, .6), (7.12, 7.50, 4, .5), (7.50, 7.95, 6, .5), (7.95, 8.25, 3, .5), (8.25, 8.70, 6, .5), (8.70, 9.01, 3, .5)]
CUTS = []                                      # hard cuts (none: every handoff is a continuous move)
ARGS = ["--force-color-profile=srgb", "--font-render-hinting=none", "--disable-checker-imaging",
        "--run-all-compositor-stages-before-draw", "--disable-threaded-animation", "--hide-scrollbars"]


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    class Q(h.func):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=str(HERE)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


async def open_page(p, scale=1):
    b = await p.chromium.launch(executable_path=CHROME, args=ARGS)
    pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=scale)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type in ("error", "warning") else None)
    await pg.goto(URL)
    await pg.wait_for_function("window.ready === true", timeout=120000)
    await pg.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
    return b, pg, errs


async def grab(pg, t, fmt="jpeg"):
    await pg.evaluate(f"window.seek({t:.6f})")
    await pg.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    return await pg.screenshot(type=fmt, **({"quality": 94} if fmt == "jpeg" else {}), clip={"x": 0, "y": 0, "width": W, "height": H})


def sub_for(t):
    for a, b, n, sh in SUB:
        if a <= t < b: return n, sh
    return 1, .5


def sub_times(i):
    tc = i / FPS
    n, sh = sub_for(tc)
    ts = [tc + (j - (n - 1) / 2) * sh / (FPS * n) for j in range(n)] if n > 1 else [tc]
    out = []
    for t in ts:
        t = min(T - 1e-4, max(0.0, t))
        for c in CUTS:
            if (t < c) != (tc < c): t = c if tc >= c else c - 1e-4
        out.append(t)
    return out


async def probe(times, name="sheet.png", cols=5, width=360):
    out = HERE / "tmp/probe"; shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    srv = serve()
    async with async_playwright() as p:
        b, pg, errs = await open_page(p)
        for i, t in enumerate(times):
            (out / f"p_{i:02d}.png").write_bytes(await grab(pg, t, "png"))
        await b.close()
    srv.shutdown()
    if errs: print("PAGE ERRORS:", errs[:8])
    ims = [Image.open(out / f"p_{i:02d}.png").convert("RGB").resize((width, int(width * H / W)), Image.LANCZOS) for i in range(len(times))]
    rows = -(-len(ims) // cols)
    sh = Image.new("RGB", (cols * (width + 6), rows * (int(width * H / W) + 26)), (255, 255, 255))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sh)
    for i, im in enumerate(ims):
        x, y = (i % cols) * (width + 6), (i // cols) * (int(width * H / W) + 26)
        sh.paste(im, (x, y + 22)); d.text((x + 4, y + 4), f"t={times[i]:.3f}", fill=(0, 0, 0))
    sh.save(out / name)
    print("probe ->", out / name)


async def draft(fps=30):
    out = HERE / "tmp/draft"; shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    srv = serve()
    t0 = time.time()
    async with async_playwright() as p:
        b, pg, errs = await open_page(p)
        for i in range(int(T * fps)):
            Image.open(__import__("io").BytesIO(await grab(pg, i / fps))).resize((540, 960), Image.LANCZOS).save(out / f"d_{i:04d}.jpg", quality=90)
        await b.close()
    srv.shutdown()
    if errs: print("PAGE ERRORS:", errs[:8])
    (HERE / "out").mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(out / "d_%04d.jpg"), "-c:v", "libx264", "-crf", "20",
                    "-preset", "veryfast", "-pix_fmt", "yuv420p", str(HERE / "out/draft.mp4")], check=True)
    print(f"draft -> out/draft.mp4 in {time.time() - t0:.0f}s")


async def chunk(a, b_):
    import io
    out = HERE / "frames"; out.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b, pg, errs = await open_page(p)
        t0 = time.time()
        for i in range(a, b_):
            ts = sub_times(i)
            acc = None
            for t in ts:
                im = np.asarray(Image.open(io.BytesIO(await grab(pg, t))).convert("RGB"), np.float32)
                acc = im if acc is None else acc + im
            Image.fromarray((acc / len(ts) + 0.5).clip(0, 255).astype(np.uint8)).save(out / f"f_{i:04d}.png", compress_level=1)
            if (i - a) % 30 == 0: print(f"[{a}-{b_}] frame {i} ({len(ts)} sub) {time.time() - t0:.0f}s", flush=True)
        await b.close()
    if errs: print("PAGE ERRORS:", errs[:8])


def full(procs=4, a=0, b=NFR):
    srv = serve()
    # balance chunks by subframe count
    cost = [len(sub_times(i)) for i in range(a, b)]
    tot, edges, acc = sum(cost), [a], 0
    for i, c in enumerate(cost):
        acc += c
        if acc >= tot * len(edges) / procs and len(edges) < procs: edges.append(a + i + 1)
    edges.append(b)
    t0 = time.time()
    ps = [subprocess.Popen([sys.executable, __file__, "chunk", str(edges[k]), str(edges[k + 1])], env={**os.environ, "NOSERVE": "1"}) for k in range(len(edges) - 1)]
    for p in ps: p.wait()
    srv.shutdown()
    print(f"full {a}-{b}: {tot} captures in {time.time() - t0:.0f}s")


def encode(name="chapox_intro"):
    (HERE / "out").mkdir(exist_ok=True)
    n = len(list((HERE / "frames").glob("f_*.png")))
    assert n == NFR, f"expected {NFR} frames, found {n}"
    aud = HERE / "out/audio.wav"
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(HERE / "frames/f_%04d.png")]
    if aud.exists(): cmd += ["-i", str(aud)]
    cmd += ["-map", "0:v"] + (["-map", "1:a", "-c:a", "aac", "-b:a", "256k", "-ar", "48000"] if aud.exists() else [])
    cmd += ["-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
            "-profile:v", "high", "-level", "4.2", "-r", str(FPS), "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-frames:v", str(NFR), "-t", f"{T:.3f}", "-movflags", "+faststart", str(HERE / f"out/{name}.mp4")]
    subprocess.run(cmd, check=True)
    print("->", HERE / f"out/{name}.mp4")


def pops(path=None):
    path = path or HERE / "out/chapox_intro.mp4"
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(path), "-vf", "scale=180:320,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 320, 180).astype(np.float32)
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    print("frames", len(fr))
    for i in range(1, len(d) - 1):
        nb = max(d[i - 1], d[i + 1], 0.3)
        if d[i] > 3 * nb and d[i] > 2.0: print(f"  pop  frame {i + 1} t {(i + 1) / FPS:.3f} diff {d[i]:.2f} neighbours {nb:.2f}")
    for n in range(1, len(fr) - 1):
        a, b = d[n - 1], d[n]
        if min(a, b) > 2.0 and np.abs(fr[n + 1] - fr[n - 1]).mean() < 0.35 * min(a, b): print(f"  flash frame {n} t {n / FPS:.3f}")


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "probe": asyncio.run(probe([float(x) for x in sys.argv[2:]]))
    elif c == "beats": asyncio.run(probe([round(0.05 + 0.375 * k + 0.06, 3) for k in range(24)], "beats.png", cols=6, width=300))
    elif c == "draft": asyncio.run(draft())
    elif c == "chunk": asyncio.run(chunk(int(sys.argv[2]), int(sys.argv[3])))
    elif c == "full": full(int(sys.argv[2]) if len(sys.argv) > 2 else 4, *(int(x) for x in sys.argv[3:5]))
    elif c == "encode": encode(*(sys.argv[2:3]))
    elif c == "pops": pops(*(sys.argv[2:3]))
