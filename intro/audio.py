"""CHAPO X intro sound design, 100 % synthesized (no samples), placed on the film's exact times.
Grid: 160 BPM half-time, beat k at 0.05 + 0.375 k; one bar (1.5 s) per scene: 0.80 app, 2.30 game, 3.80 web, 5.30 chain,
tape stop at 6.425, magnetic pull into the drop/logo at 6.80. Output: out/audio.wav, 48 kHz stereo, two-pass -14 LUFS, TP -1."""
import json, subprocess
from pathlib import Path
import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
SR, T = 48000, 9.0
N = int(round(T * SR))
rng = np.random.default_rng(1909)
bt = lambda k: 0.05 + 0.375 * k

MUS = np.zeros((N, 2)); SFX = np.zeros((N, 2)); VERB = np.zeros((N, 2)); KENV = np.zeros(N)


def tt(d): return np.arange(int(d * SR)) / SR


def pan_gains(p):
    p = np.clip(p, -1, 1); a = (p + 1) * np.pi / 4
    return np.cos(a), np.sin(a)


def add(bus, sig, t, gain=1.0, pan=0.0, verb=0.0):
    sig = np.asarray(sig, float) * gain
    i0 = int(round(t * SR))
    if sig.ndim == 1:
        gl, gr = pan_gains(pan if np.isscalar(pan) else np.asarray(pan))
        sig = np.stack([sig * gl, sig * gr], 1)
    lo, hi = max(0, i0), min(N, i0 + len(sig))
    if hi <= lo: return
    bus[lo:hi] += sig[lo - i0:hi - i0]
    if verb: VERB[lo:hi] += sig[lo - i0:hi - i0] * verb


def bp(x, lo, hi, order=2): return signal.sosfilt(signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def hp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)
def lp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)
def noise(d): return rng.standard_normal(int(d * SR))


def sweep_bp(x, f_from, f_to, q=1.2, block=256):
    """band-pass whose centre glides (log) from f_from to f_to over the signal; block-wise biquad with carried state"""
    out = np.zeros_like(x); zi = None; n = len(x)
    for i in range(0, n, block):
        u = i / max(1, n - 1)
        fc = f_from * (f_to / f_from) ** u
        bw = fc / q
        b, a = signal.butter(1, [max(20, fc - bw / 2), min(SR / 2 - 100, fc + bw / 2)], "bandpass", fs=SR)
        if zi is None: zi = signal.lfilter_zi(b, a) * 0
        out[i:i + block], zi = signal.lfilter(b, a, x[i:i + block], zi=zi)
    return out


# ------------------------------------------------------------------ instruments
def kick(f0=150, f1=44, tp=0.035, ta=0.22, d=0.6, click=0.5):
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t / tp)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / ta)
    c = hp(noise(0.004), 2500) * np.linspace(1, 0, int(0.004 * SR)) * click
    s[:len(c)] += c
    return np.tanh(1.6 * s) / np.tanh(1.6)


def boom(f0=56, f1=31, d=1.6, ta=0.55):
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t / 0.25)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / ta) * np.minimum(1, t / 0.004)
    r = lp(noise(d), 140) * np.exp(-t / (ta * 0.8)) * 0.8
    return np.tanh(1.3 * (s + r))


def crack(d=0.09, lo=1800, hi=7500, ta=0.025):
    t = tt(d); return bp(noise(d), lo, hi) * np.exp(-t / ta)


def clap():
    d = 0.32; t = tt(d); x = np.zeros(len(t))
    for k, o in enumerate([0, 0.011, 0.022]):
        i = int(o * SR); m = int(0.012 * SR) if k < 2 else len(t) - i
        e = np.exp(-np.arange(m) / SR / (0.006 if k < 2 else 0.07))
        x[i:i + m] += bp(noise(m / SR), 900, 3200)[:m] * e
    return x


def hat(open_=False):
    d = 0.16 if open_ else 0.05; t = tt(d)
    return hp(noise(d), 7500) * np.exp(-t / (0.05 if open_ else 0.012))


def click(f=3200, d=0.03):
    t = tt(d); s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006) * 0.6
    c = hp(noise(0.003), 3000) * 0.8; s[:len(c)] += c
    return s


def blip(f, d=0.06, square=True):
    t = tt(d); ph = 2 * np.pi * f * t
    s = np.sign(np.sin(ph)) if square else np.sin(ph)
    s = np.round(s * np.exp(-t / (d / 3)) * 6) / 6      # bit-crushed
    return lp(s, 6000)


def whoosh(d, f_from, f_to, peak=0.6, q=1.4, tone=0.0):
    t = tt(d); u = t / d
    env = np.where(u < peak, (u / peak) ** 2.2, ((1 - u) / (1 - peak)) ** 1.6)
    x = sweep_bp(noise(d), f_from, f_to, q) * env
    if tone:
        f = f_from * (f_to / f_from) ** u * 0.5
        x += np.sin(2 * np.pi * np.cumsum(f) / SR) * env * tone
    return x / (np.abs(x).max() + 1e-9)


def riser(d, f_from=180, f_to=2400):
    t = tt(d); u = t / d; env = u ** 2.5
    x = sweep_bp(noise(d), 400, 6000, 1.0) * env
    f = f_from * (f_to / f_from) ** (u ** 1.5)
    x += 0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env
    return x / (np.abs(x).max() + 1e-9)


def swell(d):
    """reverse tail: what a big hit's reverb sounds like played backwards (the suck into the drop)"""
    t = tt(d)
    tail = (bp(noise(d), 300, 5000) * 0.6 + lp(noise(d), 200)) * np.exp(-t / (d / 3.2))
    return tail[::-1] / (np.abs(tail).max() + 1e-9)


def saw_pluck(f, d, bright=1.0, decay=2.4):
    t = tt(d); s = np.zeros(len(t))
    for n in range(1, int(min(2400, SR / 2) / f)):
        s += np.sin(2 * np.pi * n * f * t) / n * np.exp(-t * (decay + 0.85 * n / bright))
    return s


def pad(freqs, d, att=0.4, rel=0.5, fc=1400, det=(-0.11, 0, 0.12)):
    t = tt(d); out = np.zeros((len(t), 2))
    for j, f0 in enumerate(freqs):
        for k, dc in enumerate(det):
            f = f0 * 2 ** (dc / 12)
            ph = rng.uniform(0, 6.28)
            v = np.zeros(len(t))
            for n in range(1, int(4000 / f)):
                v += np.sin(2 * np.pi * n * f * t + ph * n) / n / (1 + (n * f / fc) ** 2)
            pnl = (k - 1) * 0.6
            gl, gr = pan_gains(pnl)
            out[:, 0] += v * gl; out[:, 1] += v * gr
    env = np.minimum(1, t / att) * np.minimum(1, (d - t) / rel).clip(0, 1)
    return out * env[:, None] / (len(freqs) * len(det))


# ------------------------------------------------------------------ hook 0 - 0.80
add(SFX, kick(170, 42, 0.03, 0.25), 0.055, 1.0, verb=0.25)
add(SFX, boom(60, 32, 1.2, 0.35), 0.055, 0.55)
add(SFX, crack(), 0.055, 0.35, verb=0.4)
add(SFX, click(4200), 0.062, 0.3)
for i in range(11):                                              # digital texture while the X breathes
    tg = 0.13 + i * 0.027 + rng.uniform(-0.006, 0.006)
    add(SFX, blip(rng.choice([1320, 1760, 2093, 2637, 3520]), 0.035), tg, 0.07, pan=rng.uniform(-0.7, 0.7))
add(SFX, swell(0.36), 0.44, 0.55, verb=0.1)                     # inhale, then the rush through the X
add(SFX, riser(0.34, 220, 3000), 0.46, 0.22)
add(SFX, whoosh(0.32, 300, 4200, 0.82, 1.2, tone=0.25), 0.49, 0.5)

# ------------------------------------------------------------------ groove, bars 1-4 (0.80 - 6.425)
BARS = [(0.80, 87.31), (2.30, 69.30), (3.80, 77.78), (5.30, 87.31)]
def kick_at(t0, g=0.85):
    add(MUS, kick(), t0, g); i = int(t0 * SR); m = min(N - i, int(0.25 * SR))
    KENV[i:i + m] = np.maximum(KENV[i:i + m], np.exp(-np.arange(m) / SR / 0.09))
for b0, f in BARS:
    kick_at(b0, 0.95); kick_at(b0 + 1.5 * 0.375, 0.55)
    if b0 + 2 * 0.375 < 6.42: add(MUS, clap(), b0 + 2 * 0.375, 0.45, verb=0.35)
    for e in range(8):                                           # 3-3-2 bass on 8ths
        tb = b0 + e * 0.1875
        if tb >= 6.42: break
        if e in (0, 3, 6): add(MUS, saw_pluck(f, 0.32, 1.0, 5) * 0.9 + saw_pluck(f / 2, 0.32, 0.4, 3) * 0.6, tb, 0.42)
    for e in range(8):                                           # hats
        th = b0 + e * 0.1875
        if th >= 6.40: break
        add(MUS, hat(e == 7), th, 0.11 if e % 2 else 0.06, pan=0.25 if e % 2 else -0.15)
for k in range(6):                                               # hat roll into the chain bar
    add(MUS, hat(), 5.30 - 0.1875 + k * 0.03125, 0.04 + 0.01 * k, pan=0.3)
padA = pad([174.61, 207.65, 261.63, 311.13, 392.00], 5.75, 0.6, 0.25, 1100)   # Fm9 bed under the four scenes
add(MUS, padA, 0.80, 0.2)

# ------------------------------------------------------------------ scene sounds
for tc, f in [(1.165, 3000), (1.52, 2600), (2.62, 1800)]:        # pill, RUNNING pop, reticle lock
    add(SFX, click(f), tc, 0.22, pan=0.2, verb=0.15)
add(SFX, blip(1567, 0.05, False), 2.66, 0.08, pan=0.1)
for i in range(14):                                              # logs typing
    add(SFX, click(5200, 0.012), 1.54 + i * 0.03 + rng.uniform(0, 0.01), 0.05, pan=-0.2)
for i in range(16):                                              # data chatter in the app scene
    add(SFX, blip(rng.choice([880, 1175, 1568, 2349]), 0.03), 0.9 + i * 0.045, 0.035, pan=rng.uniform(-0.5, 0.5))
w = whoosh(0.4, 250, 5000, 0.5, 1.0, tone=0.2)                   # whip pan, content flies right -> left
add(SFX, w, 2.10, 0.65, pan=np.linspace(0.8, -0.8, len(w)), verb=0.1)
add(SFX, crack(0.05, 3000, 9000, 0.01), 2.30, 0.2)
add(SFX, riser(0.6, 400, 1600), 3.12, 0.06)                     # game world air
for i in range(9):                                               # glitch wipe: stutters sweeping right -> left
    tg = 3.60 + i * 0.025
    g = bp(noise(0.018), 600 + 400 * i, 6000) * np.sign(np.sin(np.arange(int(0.018 * SR)) * 0.9))
    add(SFX, np.round(g * 4) / 4, tg, 0.16, pan=0.8 - i * 0.2)
add(SFX, blip(220, 0.08), 3.62, 0.12); add(SFX, blip(330, 0.06), 3.70, 0.1)
w = whoosh(0.7, 3500, 220, 0.18, 1.1)                            # pull back
add(SFX, w, 3.78, 0.5, verb=0.2)
add(SFX, blip(2637, 0.05, False), 4.5, 0.05); add(SFX, whoosh(0.2, 4000, 9000, 0.5), 4.48, 0.06)   # button glint
sides = [-0.85, 0.85, 0.0, 0.0, 0.0]
for i, tk in enumerate([bt(14), bt(14.5), bt(15), bt(15.5), bt(16)]):   # chain cards
    if i < 4:
        w = whoosh(0.16, 500, 3800, 0.85, 1.3)
        add(SFX, w, tk - 0.14, 0.32, pan=np.linspace(sides[i], 0, len(w)))
    else:
        add(SFX, swell(0.16), tk - 0.15, 0.3)
    add(SFX, click(2400 + 300 * i, 0.04), tk, 0.24, verb=0.15)
    add(SFX, kick(110, 60, 0.02, 0.05, 0.12, 0.2), tk, 0.25)

# ------------------------------------------------------------------ tape stop (6.425) + magnetic pull + drop (6.80)
ts = int(6.425 * SR); te = int(6.80 * SR)
seg_len = te - ts; dstop = 0.16
tau = np.arange(seg_len) / SR
rate = np.clip(1 - tau / dstop, 0, 1) ** 1.6
pos = ts + np.cumsum(rate)
for c in range(2):
    MUS[ts:te, c] = np.interp(pos, np.arange(N), MUS[:, c]) * np.where(tau < dstop, 1 - (tau / dstop) ** 3, 0)
MUS[te:] = 0
add(SFX, swell(0.37), 6.43, 0.75, verb=0.15)
t = tt(0.37); f = 28 * (60 / 28) ** (t / 0.37)
add(SFX, np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / 0.37) ** 2, 6.43, 0.5)
add(SFX, riser(0.3, 300, 4000), 6.48, 0.25)
add(SFX, kick(180, 40, 0.03, 0.3, 0.8), 6.80, 1.0, verb=0.3)
add(SFX, boom(62, 30, 2.2, 0.8), 6.80, 0.95)
add(SFX, crack(0.12, 1500, 9000, 0.03), 6.80, 0.45, verb=0.6)
t = tt(1.9)
add(SFX, hp(noise(1.9), 4500) * np.exp(-t / 0.45), 6.80, 0.13, verb=0.3)          # crash
padB = pad([174.61, 261.63, 311.13, 392.00, 523.25], 2.2, 0.03, 0.03, 1700)
add(MUS, padB, 6.80, 0.2)
t = tt(2.1)
for fz, ph in [(1396.9, 0), (2093.0, 1.3), (1568.0, 2.2), (3136.0, 0.4)]:          # shimmer after the flash
    sh = np.sin(2 * np.pi * fz * t + ph) * np.exp(-t / 0.7) * (0.6 + 0.4 * np.sin(2 * np.pi * 5.5 * t + ph))
    add(SFX, sh, 6.84, 0.035, pan=np.sin(ph) * 0.6, verb=0.6)
add(SFX, whoosh(0.5, 2500, 11000, 0.5, 1.2), 7.0, 0.09)         # light sweep across the badge
add(SFX, kick(120, 45, 0.03, 0.18, 0.5, 0.2), bt(20), 0.35)      # tagline
add(SFX, boom(50, 34, 0.8, 0.3), bt(20), 0.25)
add(SFX, whoosh(0.4, 600, 3000, 0.4, 1.0), bt(20) - 0.08, 0.12)
for i in range(4):                                               # APPS / GAMES / WEB / AI
    add(SFX, click(2900 + 250 * i, 0.03), bt(22) + 0.08 * i + 0.03, 0.17, pan=-0.45 + 0.3 * i, verb=0.12)
add(SFX, kick(140, 42, 0.03, 0.2, 0.5, 0.35), bt(23), 0.42, verb=0.2)   # final micro impact
add(SFX, boom(54, 32, 0.6, 0.25), bt(23), 0.28)
add(SFX, click(3600), bt(23), 0.2)

# ------------------------------------------------------------------ mix
duck = 1 - 0.55 * np.convolve(KENV, np.ones(96) / 96, "same")
MUS[:te] *= duck[:te, None]
ir_t = tt(1.3)
IR = np.stack([lp(noise(1.3), 6000) * np.exp(-ir_t / 0.32), lp(noise(1.3), 6000) * np.exp(-ir_t / 0.32)], 1) * 0.05
wet = np.stack([signal.fftconvolve(VERB[:, c], IR[:, c])[:N] for c in range(2)], 1)
mix = MUS * 0.9 + SFX + wet
mix = np.tanh(mix * 0.9) / 0.9                                   # soft clip glue
fo = int(0.03 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2   # clean cut at 9.00
mix[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))[:, None]
(HERE / "out").mkdir(exist_ok=True)
raw = HERE / "out/audio_raw.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", str(raw)],
               input=mix.astype(np.float32).tobytes(), check=True)
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.2:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.2:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
      f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", af, "-ar", str(SR), "-t", f"{T:.3f}", str(HERE / "out/audio.wav")], check=True)
m2 = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(HERE / "out/audio.wav"), "-af", "loudnorm=I=-14:TP=-1.2:print_format=json", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
j2 = json.loads(m2[m2.rindex("{"):m2.rindex("}") + 1])
print(f"audio -> out/audio.wav  in {j['input_i']} LUFS -> {j2['input_i']} LUFS, TP {j2['input_tp']} dBTP")
