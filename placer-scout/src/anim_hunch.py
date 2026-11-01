"""Animation #10 'Hunch checker': highway photo -> mile marker -> computer view -> top-down -> checklist -> NOT GOLD.
Inputs in out/roadside/ (photo, pano_view.png from panorama.py, s2_crop_20261019.jpg = Sentinel-2 mosaic crop offset (300,950)).
Output: out/animations/hunch_checker_i15.mp4"""
import os, math, numpy as np
from PIL import Image, ImageDraw
from anim_common import *
ROOT = os.path.join(os.path.dirname(__file__), ".."); R = os.path.join(ROOT, "out", "roadside")
photo = Image.open(os.path.join(R, "i15_photo.jpg")).convert("RGB")          # 2016x1512
pano = Image.open(os.path.join(R, "pano_view.png")).convert("RGB")           # az 250 + col*0.05 deg
top = Image.open(os.path.join(R, "s2_crop_20261019.jpg")).convert("RGB")     # 10 m pixels
CHUTE_P = (1521, 670); MARK_P = (450, 1075); VIEW_T = (849, 387); CHUTE_T = (237, 381)
BOX_Y, BOX = 430, 1080
wr = Writer(os.path.join(ROOT, "out", "animations", "hunch_checker_i15.mp4"))
def lerp(a, b, t): return a + (b - a) * t
def crop_view(img, cx, cy, w, h, out_w, out_h):
    return img.crop((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))).resize((out_w, out_h), Image.LANCZOS)
def frame(): im = Image.new("RGB", (W, H), BG); return im, ImageDraw.Draw(im)
def step_title(d, a, b): text_c(d, 150, a, 42, GOLD); text_c(d, 215, b, 58, WHITE)
def ring(d, x, y, r, col=RED, w=8): d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=w)
# S1-S2: photo, slow push toward chute, then ring pulse (6 s)
for i in range(180):
    t = ease(i / 179); cx = lerp(1100, 1450, t); cy = lerp(756, 700, t); h = lerp(1512, 900, t); w = h * BOX / BOX
    w = min(w, 2016); im, d = frame(); v = crop_view(photo, cx, cy, w, h, BOX, BOX); im.paste(v, (0, BOX_Y))
    text_c(d, 150, "SPOTTED FROM I-15", 42, GOLD); text_c(d, 215, "Is this a gold wash?", 66, WHITE)
    if i > 90:
        sx = (CHUTE_P[0] - (cx - w / 2)) * BOX / w; sy = BOX_Y + (CHUTE_P[1] - (cy - h / 2)) * BOX / h
        ring(d, sx, sy, 110 + 10 * math.sin(i / 4) * (1 - ease((i - 90) / 60)) * 1.0 * (BOX / w * 1.0) * 0 + 120 * BOX / w * 0.9)
    wr.add(im)
# S3: mile marker (4 s)
for i in range(120):
    t = ease(i / 50); cx = lerp(1450, MARK_P[0], t); cy = lerp(700, MARK_P[1], t); h = lerp(900, 420, t); w = h
    im, d = frame(); im.paste(crop_view(photo, cx, cy, w, h, BOX, BOX), (0, BOX_Y)); step_title(d, "STEP 1", "Read the mile marker")
    if i > 55:
        a = ease((i - 55) / 20); text_c(d, BOX_Y + BOX + 70, "I-15 · San Bernardino Co. · 122.50", 44, WHITE)
        if i > 80: text_c(d, BOX_Y + BOX + 150, "= 35.1187, -116.2348", 58, GOLD)
        text_c(d, BOX_Y + BOX + 250, "(Caltrans postmile map)", 30, GREY, False)
    wr.add(im)
# S4: photo vs computer view wipe (5.5 s)
pb = photo.crop((0, 520, 2016, 860)).resize((W, int(W * 340 / 2016)), Image.LANCZOS)
cb = pano.crop((40, 128, 530, 211)).resize((W, pb.height), Image.LANCZOS)
SCALE = 2.2; pbs = pb.resize((W * 1, int(pb.height * SCALE))); cbs = cb.resize((W, int(cb.height * SCALE)))
cxs = int(W * 1521 / 2016)
for i in range(165):
    im, d = frame(); step_title(d, "STEP 2", "Rebuild the view in 3D")
    y0 = 520; im.paste(pbs, (0, y0)); wipe = int(W * ease((i - 30) / 70)) if i < 110 else int(W * (1 - ease((i - 120) / 40)))
    if wipe > 0: im.paste(cbs.crop((0, 0, wipe, cbs.height)), (0, y0))
    d.line([wipe, y0 - 20, wipe, y0 + cbs.height + 20], fill=GOLD, width=6) if 0 < wipe < W else None
    ring(d, cxs, y0 + cbs.height * 0.45, 70, RED, 7)
    text_c(d, y0 + cbs.height + 60, ("Left: computer view  ·  Right: your photo" if 0 < wipe < W else ("Computer view: terrain + satellite" if wipe >= W else "Your photo")), 38, WHITE, False)
    text_c(d, y0 + cbs.height + 120, "Same ridges. Same chute.", 52, GOLD)
    text_c(d, H - 260, "USGS 10 m terrain · Sentinel-2, Oct 19, 2026", 28, GREY, False)
    wr.add(im)
# S5: top-down zoom along the sight line (5 s)
for i in range(150):
    t = ease(i / 110); cx = lerp(543, CHUTE_T[0], t); cy = lerp(384, CHUTE_T[1], t); w = lerp(740, 190, t)
    im, d = frame(); im.paste(crop_view(top, cx, cy, w, w, BOX, BOX), (0, BOX_Y)); step_title(d, "STEP 3", "Find it from above")
    def P(p): return ((p[0] - (cx - w / 2)) * BOX / w, BOX_Y + (p[1] - (cy - w / 2)) * BOX / w)
    a, b = P(VIEW_T), P(CHUTE_T); d.line([a, b], fill=GOLD, width=5)
    if 0 <= a[0] <= W: d.ellipse([a[0] - 14, a[1] - 14, a[0] + 14, a[1] + 14], fill=GOLD); d.text((a[0] - 150, a[1] + 22), "You, on I-15", font=font(34), fill=WHITE, stroke_width=3, stroke_fill=(0, 0, 0))
    ring(d, b[0], b[1], 40 + 60 * t, RED, 7)
    text_c(d, BOX_Y + BOX + 60, "4 miles west, Soda Mountains", 46, WHITE)
    text_c(d, BOX_Y + BOX + 130, "Pale sand packed into a ravine", 40, GOLD, False)
    wr.add(im)
# S6: checklist (6 s)
bg = crop_view(top, CHUTE_T[0], CHUTE_T[1], 190, 190, BOX, BOX); bg = Image.blend(bg, Image.new("RGB", bg.size, BG), 0.72)
ROWS = [("Gold mine draining into it?", "No. Nearest is 3 miles away, wrong side."),
        ("Flood trap that holds gold?", "No. Wind-blown sand, too light."),
        ("Legal to dig?", "No. Soda Mountains Wilderness.")]
for i in range(180):
    im, d = frame(); im.paste(bg, (0, BOX_Y)); step_title(d, "STEP 4", "Check it like a prospector")
    for j, (q, a) in enumerate(ROWS):
        tt = ease((i - j * 45) / 15)
        if tt <= 0: continue
        y = BOX_Y + 90 + j * 300; x = 70 - (1 - tt) * 80
        d.text((x, y), q, font=font(46), fill=WHITE)
        d.text((x, y + 75), "✗", font=font(70), fill=RED); d.text((x + 80, y + 90), a, font=font(36, False), fill=(235, 200, 195))
    wr.add(im)
# S7: stamp (4 s) + end card (3 s)
for i in range(120):
    im, d = frame(); im.paste(bg, (0, BOX_Y)); step_title(d, "VERDICT", "")
    s = lerp(2.2, 1.0, ease(i / 10)); st = Image.new("RGBA", (900, 320), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([10, 10, 890, 310], 30, outline=RED + (255,), width=18); f = font(170)
    sd.text(((900 - sd.textlength("NOT GOLD", font=f)) / 2, 55), "NOT GOLD", font=f, fill=RED + (255,))
    st = st.rotate(-8, expand=True, resample=Image.BICUBIC); st = st.resize((int(st.width * s), int(st.height * s)))
    im = im.convert("RGBA"); im.alpha_composite(st, (int((W - st.width) / 2), int(BOX_Y + BOX / 2 - st.height / 2))); im = im.convert("RGB"); d = ImageDraw.Draw(im)
    if i > 30: text_c(d, BOX_Y + BOX + 70, "Checked in minutes", 56, WHITE); text_c(d, BOX_Y + BOX + 150, "with free public data.", 48, GOLD, False)
    wr.add(im)
for i in range(90):
    im, d = frame(); text_c(d, 700, "Spot something from the road?", 56, WHITE)
    text_c(d, 790, "Send a photo with a mile marker.", 50, GOLD); text_c(d, 1600, "Hunting Gold with AI", 44, GREY); wr.add(im)
print("frames", wr.close())
