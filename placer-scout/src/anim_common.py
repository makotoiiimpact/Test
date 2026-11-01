"""Shared helpers for explainer animations (vertical 1080x1920, 30 fps, piped to ffmpeg)."""
import subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H, FPS = 1080, 1920, 30
BG = (14, 17, 22); GOLD = (244, 190, 60); WHITE = (240, 240, 240); GREY = (150, 155, 165); RED = (226, 64, 52); GREEN = (90, 200, 120)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_fc = {}
def font(size, bold=True):
    k = (size, bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(FB if bold else FR, size)
    return _fc[k]
def text_c(d, y, s, size, fill=WHITE, bold=True, stroke=0):
    f = font(size, bold); w = d.textlength(s, font=f)
    d.text(((W - w) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
def ease(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)
class Writer:
    def __init__(self, path):
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                   "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium", "-movflags", "+faststart", path],
                                  stdin=subprocess.PIPE)
        self.n = 0
    def add(self, im): self.p.stdin.write(np.asarray(im.convert("RGB"), dtype=np.uint8).tobytes()); self.n += 1
    def close(self): self.p.stdin.close(); self.p.wait(); return self.n
