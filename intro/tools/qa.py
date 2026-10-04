"""QA sheets from the master: overview (2 fps), phone-size readability (1 fps), and 12-frame strips around fast moves."""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
V = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "out/chapox_intro.mp4")
Q = HERE / "tmp/qa"; Q.mkdir(parents=True, exist_ok=True)
run = lambda *a: subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
run("-i", V, "-vf", "fps=2,scale=180:-1,tile=9x2:padding=4", "-frames:v", "1", str(Q / "contact.png"))
run("-i", V, "-vf", "fps=1,scale=360:-1,tile=9x1:padding=4", "-frames:v", "1", str(Q / "phone.png"))
for t in [float(x) for x in sys.argv[2:]] or [0.0, 0.70, 2.20, 3.62, 5.15, 6.60]:
    run("-ss", f"{t:.3f}", "-i", V, "-vf", "scale=240:-1,tile=12x1:padding=3", "-frames:v", "1", str(Q / f"strip_{t:.2f}.png"))
print("qa ->", Q)
