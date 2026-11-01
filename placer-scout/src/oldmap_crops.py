"""Cut a ~3 km window of the matching 1950s USGS 15' sheet around each top-8 target (400 dpi), mark the target, for reading by eye."""
import os, sys, subprocess, requests, numpy as np, pandas as pd
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.join(os.path.dirname(__file__), ".."); D = os.path.join(ROOT, "data", "oldmaps"); O = os.path.join(ROOT, "out", "oldmap_crops"); os.makedirs(O, exist_ok=True)
from pypdf import PdfReader
maps = pd.read_csv(os.path.join(ROOT, "out", "old_maps.csv"))
cat = []
for off in (0, 200):
    cat += requests.get("https://tnmaccess.nationalmap.gov/api/v1/products", params={"datasets": "Historical Topographic Maps", "bbox": "-115.7,35.2,-114.6,36.1",
                        "max": 200, "offset": off, "outputFormat": "JSON"}, timeout=120).json().get("items", [])
BBOX = {i["downloadURL"]: i["boundingBox"] for i in cat}
sheets = maps[(maps.scale == "1:62500") & maps.year.between(1950, 1960)].copy()
t = pd.read_csv(os.path.join(ROOT, "out", "targets.csv")).head(8)
if len(sys.argv) > 1: t = t[t["rank"].isin([int(a) for a in sys.argv[1:]])]   # only these ranks
DPI, HALF_M = 400, 1500
for _, r in t.iterrows():
    cand = [(row, BBOX[row.url]) for row in sheets.itertuples() if row.url in BBOX and BBOX[row.url]["minX"] <= r.lon <= BBOX[row.url]["maxX"] and BBOX[row.url]["minY"] <= r.lat <= BBOX[row.url]["maxY"]]
    if not cand: print(r["rank"], "no 1950s 15' sheet"); continue
    row, bb = sorted(cand, key=lambda c: -c[0].year)[0]
    fn = os.path.join(D, os.path.basename(row.url).replace("%20", "_"))
    if not os.path.exists(fn): open(fn, "wb").write(requests.get(row.url, timeout=600).content)
    pg = PdfReader(fn).pages[0]; cb = pg.cropbox
    nl = np.array([float(v) for v in pg["/LGIDict"][0]["/Neatline"]]).reshape(-1, 2)
    i_bl, i_tr, i_tl, i_br = np.argmin(nl.sum(1)), np.argmax(nl.sum(1)), np.argmin(nl[:, 0] - nl[:, 1]), np.argmax(nl[:, 0] - nl[:, 1])
    P = nl[[i_bl, i_br, i_tr, i_tl]]
    LL = np.array([[bb["minX"], bb["minY"]], [bb["maxX"], bb["minY"]], [bb["maxX"], bb["maxY"]], [bb["minX"], bb["maxY"]]])
    A = np.c_[np.ones(4), LL]; cx = np.linalg.lstsq(A, P[:, 0], rcond=None)[0]; cy = np.linalg.lstsq(A, P[:, 1], rcond=None)[0]   # lon/lat -> page points (near-affine)
    xp, yp = cx @ [1, r.lon, r.lat], cy @ [1, r.lon, r.lat]
    m_per_pt = (bb["maxY"] - bb["minY"]) * 111000 / (P[2, 1] - P[0, 1])
    hpt = HALF_M / m_per_pt; sc = DPI / 72
    x0 = int((xp - hpt - float(cb.left)) * sc); y0 = int((float(cb.top) - yp - hpt) * sc); w = int(2 * hpt * sc)
    out = os.path.join(O, f"target_{r.lat:.4f}_{r.lon:.4f}_{row.map_name.replace(' ', '_')}_{row.year}")   # named by location, not rank
    subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-singlefile", "-x", str(max(0, x0)), "-y", str(max(0, y0)), "-W", str(w), "-H", str(w), fn, out], check=True)
    im = Image.open(out + ".png").convert("RGB"); d = ImageDraw.Draw(im); c = w / 2
    d.ellipse([c - 18, c - 18, c + 18, c + 18], outline=(255, 0, 0), width=4)
    im.save(out + ".png")
    print(r["rank"], r.district, "->", row.map_name, row.year, "|", os.path.relpath(out + ".png", ROOT), "| px", w)
