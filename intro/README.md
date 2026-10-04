# CHAPO X · intro TikTok (9 s, 1080×1920, 60 fps)

Final file: `out/chapox_intro.mp4` (H.264 High, yuv420p BT.709 TV range, AAC 256 kbps 48 kHz, −14 LUFS).
Storyboard, beat map and asset choices: `STORYBOARD.md`.

## How it is built
Everything is code and deterministic: `chapox_intro.html` computes every frame from `window.seek(t)` (no timers, no CSS transitions, seeded randomness), Playwright Chromium captures it, ffmpeg encodes it.

```
pip install pillow numpy scipy opencv-python playwright ncnn realesrgan-ncnn-py
python tools/prep_assets.py      # crops from DA.png / Logo.png -> assets/ (inpaint + 4x Real-ESRGAN, offline)
python tools/game_layers.py      # X.003 game art -> background + character layers (parallax, pop-out)
python audio.py                  # synthesized sound design -> out/audio.wav (-14 LUFS)
python render.py probe 0.5 3 7   # stills -> tmp/probe/sheet.png
python render.py full 4          # 540 frames, adaptive motion-blur subframes, 4 parallel Chromium
python render.py encode          # -> out/chapox_intro.mp4
python render.py pops            # single-frame pop / flash scan
```

Preview: serve the folder (`python -m http.server`) and open `chapox_intro.html`: Space play/pause, ←/→ ±0.5 s (Shift = 1 frame), R replay, `?t=6.8` to jump.

## Swapping in real project captures
The four creations come from the DA board tiles (`PROJETS / EXEMPLES`, `SITE WEB - HOME`, `INTERFACE / UI EXEMPLE`). When real screenshots exist, drop them in `assets/` with the same names (`app.png`, `game_x16.png` + `tools/game_layers.py`, `site_hero.png`) or replace the rebuilt screens in `dashHTML()` / `webHTML()`, then re-run `render.py full` + `encode`.
