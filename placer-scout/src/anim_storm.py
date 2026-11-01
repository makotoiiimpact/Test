"""Animation #8 'Storm replay': MRMS daily radar rain over the districts, Oct 1-31 2026, with the official Las Vegas gauge counter,
then the 1937-2026 October ranking. Inputs from src/anim_data.py. Output: out/animations/storm_replay_oct2026.mp4"""
import os, json, numpy as np
from PIL import Image, ImageDraw
from anim_common import *
ROOT = os.path.join(os.path.dirname(__file__), ".."); C = os.path.join(ROOT, "cache", "anim")
r = np.load(os.path.join(C, "radar_oct.npz")); days, rain = list(r["days"]), r["rain"]
dm = np.load(os.path.join(C, "dem.npz")); dem, (x0, y0, x1, y1) = dm["dem"], dm["bounds"]
lv = json.load(open(os.path.join(C, "lv_oct.json")))
RANK = [("2005", 1.45), ("2026", 1.31), ("1992", 1.22), ("2015", 1.16), ("1941", 1.13), ("1947", 1.13)]  # ACIS LASthr 1937-2026 (out/notes/rain_record_check.md)
# --- basemap: hillshade + water tint
MW = W; MH = int(W * dem.shape[0] / dem.shape[1]); MY = 360
z = np.nan_to_num(dem, nan=np.nanmin(dem)); dy_m = 0.002 * 111000; dx_m = dy_m * np.cos(np.radians(35.7))
gy, gx = np.gradient(z, dy_m, dx_m); slope = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
az, alt = np.radians(315), np.radians(40)
hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - asp); hs = np.clip(hs, 0, 1)
base = np.dstack([hs * 150 + 30, hs * 140 + 30, hs * 125 + 30])
water = (np.hypot(gx, gy) < 0.002) & (z < 400)
base[water] = (40, 80, 130)
basemap = Image.fromarray(base.astype(np.uint8)).resize((MW, MH), Image.LANCZOS)
def xy(lon, lat): return ((lon - x0) / (x1 - x0) * MW, MY + (y1 - lat) / (y1 - y0) * MH)
LABELS = [("Las Vegas", -115.14, 36.17), ("Goodsprings", -115.43, 35.83), ("Nelson", -114.83, 35.71), ("Searchlight", -114.92, 35.46),
          ("Lake Mead", -114.72, 36.12), ("Lake Mohave", -114.78, 35.58)]
GAUGE = (-115.1633, 36.0719)
def cmap(mm):
    stops = np.array([2, 10, 25, 50, 90]); cols = np.array([[150, 210, 255], [60, 140, 255], [110, 70, 235], [210, 50, 200], [255, 70, 110]])
    v = np.clip(mm, 2, 90); out = np.zeros(mm.shape + (3,))
    for c in range(3): out[..., c] = np.interp(v, stops, cols[:, c])
    a = np.interp(mm, [2, 8, 25, 60], [0, 0.35, 0.6, 0.75])
    return out, a
def map_frame(rmm, fade):
    im = Image.new("RGB", (W, H), BG); m = np.asarray(basemap).astype(float)
    if rmm is not None:
        rr = np.asarray(Image.fromarray(rmm).resize((MW, MH), Image.BILINEAR))
        col, a = cmap(rr); a = (a * fade)[..., None]; m = m * (1 - a) + col * a
    im.paste(Image.fromarray(m.astype(np.uint8)), (0, MY)); d = ImageDraw.Draw(im)
    for n, lo, la in LABELS:
        x, y = xy(lo, la); f = font(30)
        if not n.startswith("Lake"): d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=GOLD if n != "Las Vegas" else WHITE)
        d.text((x + 12, y - 18), n, font=font(30 if not n.startswith("Lake") else 26, not n.startswith("Lake")), fill=WHITE if not n.startswith("Lake") else (170, 200, 235), stroke_width=3, stroke_fill=(0, 0, 0))
    gx_, gy_ = xy(*GAUGE); d.rectangle([gx_ - 8, gy_ - 8, gx_ + 8, gy_ + 8], outline=GOLD, width=4)
    if rmm is not None:
        lx = 20; ly = MY + MH - 50; d.rectangle([lx - 10, ly - 14, lx + 560, ly + 40], fill=(0, 0, 0))
        for j, mm_ in enumerate((5, 15, 30, 60)):
            c, _ = cmap(np.array([[float(mm_)]])); d.rectangle([lx + j * 135, ly, lx + j * 135 + 30, ly + 26], fill=tuple(int(v) for v in c[0, 0]))
            d.text((lx + j * 135 + 38, ly - 2), f"{mm_} mm", font=font(24, False), fill=WHITE)
        d.text((lx + 548 - 0, ly - 2), "", font=font(24, False), fill=WHITE)
    return im, d
def counter(d, val, date_lbl):
    text_c(d, MY + MH + 30, date_lbl, 64, WHITE)
    text_c(d, MY + MH + 120, "Official Las Vegas rain gauge", 36, GREY, False)
    text_c(d, MY + MH + 170, f'{val:.2f}"', 150, GOLD)
    bx0, bx1, by = 90, W - 90, MY + MH + 370; scale = (bx1 - bx0) / 1.6
    d.rounded_rectangle([bx0, by, bx1, by + 44], 22, fill=(40, 44, 52))
    d.rounded_rectangle([bx0, by, bx0 + max(44, val * scale), by + 44], 22, fill=GOLD)
    for lab, v, c in (("normal 0.32", 0.32, GREY), ("record 1.45", 1.45, RED)):
        x = bx0 + v * scale; d.line([x, by - 12, x, by + 56], fill=c, width=5)
        d.text((x - d.textlength(lab, font=font(28, False)) / 2, by + 64), lab, font=font(28, False), fill=c)
def header(d, a="LAS VEGAS · OCTOBER 2026", b="How much rain really fell?"):
    text_c(d, 120, a, 44, GOLD); text_c(d, 190, b, 56, WHITE)
def note(d): text_c(d, MY + MH + 470 + 60, "Radar days run 5 AM to 5 AM and read high here.", 28, GREY, False); text_c(d, MY + MH + 470 + 100, "The gauge counts midnight to midnight.", 28, GREY, False)
def footer(d): text_c(d, H - 90, "Radar: NOAA MRMS · Gauge: National Weather Service, records since 1937", 26, GREY, False)
wr = Writer(os.path.join(ROOT, "out", "animations", "storm_replay_oct2026.mp4"))
# A: hook (2.5 s)
for i in range(75):
    im, d = map_frame(None, 0); header(d); counter(d, 0, "Oct 1"); footer(d); wr.add(im)
# B: days
cum = 0.0
for k, ds in enumerate(days):
    mm = rain[k]; wet = float(np.percentile(mm, 99)); n = 5 if wet < 3 else int(np.clip(10 + wet * 1.2, 20, 60))
    start, add = cum, lv.get(ds, 0.0); cum += add; lbl = "Oct " + str(int(ds[-2:]))
    for i in range(n):
        t = ease(i / max(1, n * 0.6)); im, d = map_frame(mm, min(1, i / 4) if n > 5 else 1)
        header(d, b="Daily rain from weather radar" if wet >= 3 else "How much rain really fell?"); counter(d, start + add * t, lbl)
        if wet >= 3: note(d)
        footer(d); wr.add(im)
for i in range(45):
    im, d = map_frame(None, 0); header(d); counter(d, cum, "Oct 31 · month total"); footer(d); wr.add(im)
# C: ranking (bars grow)
def rank_frame(t, hl):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    text_c(d, 150, "WETTEST OCTOBERS IN LAS VEGAS", 46, GOLD); text_c(d, 220, "90 Octobers on record, 1937–2026", 38, GREY, False)
    y = 420; bx0 = 260; bmax = W - 120 - bx0
    for j, (yr, v) in enumerate(RANK):
        tt = ease(t * 1.6 - j * 0.12); is26 = yr == "2026"; col = GOLD if is26 else (90, 100, 115)
        d.text((80, y + 20), yr, font=font(56), fill=GOLD if is26 else WHITE)
        d.rounded_rectangle([bx0, y, bx0 + max(30, bmax * v / 1.5 * tt), y + 100], 16, fill=col)
        d.text((bx0 + 20, y + 22), f'{v * tt:.2f}"', font=font(48), fill=(20, 20, 20) if tt > 0.3 else WHITE)
        if j == 0 and tt > 0.95: d.text((bx0 + 210, y + 30), "RECORD", font=font(40), fill=(255, 230, 225))
        y += 150
    if hl > 0:
        a = int(255 * ease(hl)); ov = Image.new("RGBA", (W, H)); od = ImageDraw.Draw(ov)
        f = font(110); s = "#2 of 90"; od.text(((W - od.textlength(s, font=f)) / 2, 1360), s, font=f, fill=GOLD + (a,), stroke_width=4, stroke_fill=(0, 0, 0, a))
        f2 = font(52); s2 = "Not a record. Close."; od.text(((W - od.textlength(s2, font=f2)) / 2, 1520), s2, font=f2, fill=WHITE + (a,))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"); d = ImageDraw.Draw(im)
    footer(d); return im
for i in range(105): wr.add(rank_frame(i / 70, 0))
for i in range(90): wr.add(rank_frame(1.5, i / 20))
# D: end card
for i in range(90):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    text_c(d, 640, "Second-wettest October", 70, GOLD); text_c(d, 740, "Las Vegas has ever recorded.", 58, WHITE)
    text_c(d, 900, "Did the floods move any gold?", 50, WHITE, False); text_c(d, 980, "Follow the hunt.", 50, GOLD)
    text_c(d, 1600, "Hunting Gold with AI", 44, GREY); footer(d); wr.add(im)
print("frames", wr.close())
