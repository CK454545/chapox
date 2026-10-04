# CHAPO X · intro TikTok 9 s (1080×1920, 60 fps)

## Assets found in the repo (and nothing else)
| File | Used for |
|---|---|
| `Logo.png` (badge 1254 px) | Final hero, cut to its ring (`assets/badge.png`) |
| `DA.png` (board 1254 px) | Every other pixel: brush X icon, flat wordmark, X.002 MOBILE APP, X.003 GAME, X.??? card, website hero image, dashboard and website layouts, palette, type, graphic elements |

The board tiles are tiny (game art ~105 px wide), so:
- photos/illustrations are cropped exactly from the board, the text the board printed over them is inpainted away, then upscaled 4× (Real-ESRGAN, offline, `tools/upscale.py`); the game art 16×.
- UI screens (dashboard "X.001 AI AGENT", website "HOME", project cards) are **rebuilt in code** 1:1 from the board (same copy, layout, colours) so they stay sharp and can animate element by element.
- logos are never redrawn: the X is the DA "ICONE" tile, the nav wordmark is keyed out of the DA hero, the end logo is `Logo.png`.

DA: Neon Green `#86FF00`, Deep Black `#050505`, Light Gray `#F5F5F5`, Mid Gray `#2A2A2A`; Space Grotesk (titles), JetBrains Mono (labels, code). Signature already in the DA: **EXPERIMENT BEYOND LIMITS.** (used instead of "JE CRÉE. TU DÉCOUVRES."). Activity line from the DA hero list (AI / APPS / GAMES / TOOLS): **APPS • GAMES • WEB • AI**.

## Creations (4 + the teaser)
APP / UI = X.001 AI AGENT dashboard · GAME = X.003 · WEB = site HOME · MOBILE APP = X.002 · teaser X.??? SOMETHING IS COMING.

## Beat map (160 BPM half-time, beat k = 0.05 + 0.375 k, one bar per scene)
| Time | Beat | Picture | Camera | Sound |
|---|---|---|---|---|
| 0.00–0.43 | 0–1 | Brush X slams in (frame 0 already shows it), HUD brackets draw, X breathes | locked, micro rotation | impact (kick + sub + crack), digital blips |
| 0.43–0.80 | 1–2 | X inhales (anticipation), the X becomes a window onto the dashboard (neon rim), camera flies **through** it | zoom ×55 log-space, ease-in, twist +9° | reverse swell + riser + whoosh |
| 0.80–2.30 | bar 1 | X.001 AI AGENT dashboard in 2.5D (tilted window, globe, icons at depth, glass glare), UI builds: sidebar, pill, RUNNING, waveform, logs typing | approach (decelerating), window turns to camera, then dives into the waveform card | kick/clap/bass groove, UI clicks on the pops, typing ticks |
| 2.13–2.47 | 6 | whip pan, game screen arrives during the move | whip 1140 px, blur ∝ speed | whoosh panned R→L |
| 2.30–3.80 | bar 2 | X.003 GAME screen, character breaks out of the top edge, reticle locks on, fog, embers, HUD | lateral travelling, roll +3.6°→−1.4°, push-in, rack focus (bg blurs, character sharp) | lock click, airy riser |
| 3.60–3.86 | 10 | glitch-bar wipe (DA glitch element), headline revealed tight | | glitch stutters R→L |
| 3.80–5.30 | bar 3 | WEB HOME, **pull back** reveals APP + GAME + WEB + UI at different depths, tilted, drifting | dolly back ×2.7→×1.12 (true parallax), slow drift | pull-back whoosh, button glint |
| 5.30–6.43 | bar 4 | chain: X.002 MOBILE APP (from left) → X.003 GAME (right) → WEB (bottom) → X.001 AI AGENT (top) → X.??? SOMETHING IS COMING. (from depth); older cards step back into a deck; cluster defocuses | focus pulled to the near plane | whoosh per card panned from its side, click on each landing, snare on the "?" |
| 6.43–6.80 | 17–18 | time brakes, then everything is pulled into one point (spiral, light gathering, field lines) | | tape stop, reverse swell, rising sub |
| 6.80 | 18 | flash + anamorphic streak, CHAPO X badge springs out (scale, −15° rotation, 3D tilt, blur→sharp, small overshoot), glow, light sweep 7.0–7.5 | | drop: kick + boom + crash + chord + shimmer |
| 7.55 | 20 | EXPERIMENT / BEYOND LIMITS. (masked rise per word, tracking in) | slow orbit around the badge (rotateY/X) | soft hit |
| 8.30 | 22 | APPS • GAMES • WEB • AI (stagger) | | 4 ticks |
| 8.68–9.00 | 23 | final micro zoom, clean cut at 9.00 | +4 % | small impact |

Safe zone: all text between y 230 and 1520 and x 60–1020 (TikTok UI stays clear).
