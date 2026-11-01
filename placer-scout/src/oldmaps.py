"""Scan historical USGS topo GeoPDFs for mining labels (placer, mill, tailings, dump, diggings) with Tesseract OCR.
Each hit is placed on the ground with the GeoPDF's own georeferencing and saved with an image crop for human checking.
Writes data/oldmaps/hits.csv and out/oldmap_hits/<map>_<n>.png."""
import os, re, sys, csv, hashlib, datetime, requests
import numpy as np, pandas as pd, rasterio
from rasterio.warp import transform as warp_xy
import pytesseract, subprocess, json
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), ".."); D = os.path.join(ROOT, "data", "oldmaps"); O = os.path.join(ROOT, "out", "oldmap_hits")
WANT = [("Nelson", "1:96000", 1926), ("Searchlight", "1:62500", 1959), ("Nelson", "1:62500", 1958), ("Goodsprings", "1:62500", 1960),
        ("Crescent Peak", "1:62500", 1956), ("Shenandoah Peak", "1:62500", 1956), ("Mountain Springs", "1:62500", 1957), ("Las Vegas", "1:250000", 1908)]
KEY = re.compile(r"^(placers?|mill|mills|millsite|tailings?|dumps?|diggings?|arrastra|smelter|stamp|cyanide|gold|searchlight|nelson|goodsprings)$", re.I)   # town names = georeference check
maps = pd.read_csv(os.path.join(ROOT, "out", "old_maps.csv"))
# map frame (neatline) corners from the USGS catalog record of each sheet
cat = []
for off in (0, 200):
    cat += requests.get("https://tnmaccess.nationalmap.gov/api/v1/products", params={"datasets": "Historical Topographic Maps", "bbox": "-115.7,35.2,-114.6,36.1",
                        "max": 200, "offset": off, "outputFormat": "JSON"}, timeout=120).json().get("items", [])
BBOX = {i["downloadURL"]: i["boundingBox"] for i in cat}

def render(fn, dpi=250):
    out = fn[:-4] + f"_{dpi}"
    if not os.path.exists(out + ".png"): subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", fn, out], check=True)
    return np.array(Image.open(out + ".png").convert("RGB")).transpose(2, 0, 1)

def georef(fn, dpi, bb):
    """GeoPDF neatline (page points) corners <-> catalog frame corners (lat/lon, NAD27 ~ WGS84 within ~100 m) -> bilinear map
    from rendered pixel to lon/lat. pdftoppm renders the CropBox; page y runs up, pixel y runs down."""
    from pypdf import PdfReader
    pg = PdfReader(fn).pages[0]; cb = pg.cropbox; rot = int(pg.get("/Rotate", 0) or 0)
    if rot not in (0, None): raise RuntimeError(f"rotated page ({rot}) not handled")
    nl = np.array([float(v) for v in pg["/LGIDict"][0]["/Neatline"]]).reshape(-1, 2)
    sc = dpi / 72.0
    px = (nl[:, 0] - float(cb.left)) * sc; py = (float(cb.top) - nl[:, 1]) * sc
    i_bl = np.argmin(nl[:, 0] + nl[:, 1]); i_tr = np.argmax(nl[:, 0] + nl[:, 1]); i_tl = np.argmin(nl[:, 0] - nl[:, 1]); i_br = np.argmax(nl[:, 0] - nl[:, 1])
    P = np.array([[px[i], py[i]] for i in (i_bl, i_br, i_tr, i_tl)])
    LL = np.array([[bb["minX"], bb["minY"]], [bb["maxX"], bb["minY"]], [bb["maxX"], bb["maxY"]], [bb["minX"], bb["maxY"]]])
    A = np.c_[np.ones(4), P[:, 0], P[:, 1], P[:, 0] * P[:, 1]]
    cl = np.linalg.solve(A, LL[:, 0]); ca = np.linalg.solve(A, LL[:, 1])
    f = lambda x, y: (float(cl @ [1, x, y, x * y]), float(ca @ [1, x, y, x * y]))
    return f, (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())

rows, diag = [], []
for name, scale, year in (WANT if len(sys.argv) == 1 else [w for w in WANT if w[0] in sys.argv[1:]]):
    m = maps[(maps.map_name == name) & (maps.scale == scale) & (maps.year == year)].iloc[0]
    fn = os.path.join(D, os.path.basename(m.url).replace("%20", "_"))
    if not os.path.exists(fn):
        open(fn, "wb").write(requests.get(m.url, timeout=600).content)
        with open(os.path.join(ROOT, "data", "PROVENANCE.csv"), "a", newline="") as f:
            csv.writer(f).writerow([f"USGS historical topo {name} {scale} {year}", m.url, f"oldmaps/{os.path.basename(fn)}", 1,
                                    hashlib.sha256(open(fn, "rb").read()).hexdigest()[:16], datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
    img = render(fn); gray = img.mean(0).astype("uint8"); H, W = gray.shape
    bb = BBOX[m.url]; to_ll, (L, Tp, R, B) = georef(fn, 250, bb)
    print(name, year, scale, "pixels", W, "x", H, "frame", (L, Tp, R, B), "bbox", bb, flush=True)
    T, OV = 1600, 200
    seen = set(); n = 0
    for y0 in range(0, H, T - OV):
        for x0 in range(0, W, T - OV):
            tile = gray[y0:y0 + T, x0:x0 + T]
            if tile.min() > 200: continue
            d = pytesseract.image_to_data(Image.fromarray(tile), config="--psm 11", output_type=pytesseract.Output.DICT)
            ws = [re.sub(r"[^A-Za-z]", "", t).lower() for t, c in zip(d["text"], d["conf"]) if t.strip() and float(c) >= 50]
            diag.append(dict(map=name + " " + str(year), words=len(ws), mine=sum(w in ("mine", "mines") for w in ws), wash=sum(w == "wash" for w in ws)))
            for i, word in enumerate(d["text"]):
                w = re.sub(r"[^A-Za-z]", "", word or "")
                if not w or not KEY.match(w) or float(d["conf"][i]) < 50: continue
                cx, cy = x0 + d["left"][i] + d["width"][i] / 2, y0 + d["top"][i] + d["height"][i] / 2
                k = (w.lower(), int(cx // 40), int(cy // 40))
                if k in seen: continue
                seen.add(k); n += 1
                if not (L <= cx <= R and Tp <= cy <= B): continue           # collar text (legend, title) is not a place
                lon, lat = to_ll(cx, cy)
                # context line: the OCR words on the same line (helps tell "Mill" from a mill name)
                same = [d["text"][j] for j in range(len(d["text"])) if d["block_num"][j] == d["block_num"][i] and d["line_num"][j] == d["line_num"][i] and d["text"][j].strip()]
                crop = img[:, max(0, int(cy) - 120):int(cy) + 120, max(0, int(cx) - 220):int(cx) + 220].transpose(1, 2, 0)
                cpath = os.path.join(O, f"{name.replace(' ', '_')}_{year}_{n:03d}.png"); Image.fromarray(crop.astype("uint8")).save(cpath)
                rows.append(dict(map=f"{name} {year} ({scale})", word=w, context=" ".join(same), conf=float(d["conf"][i]), lat=round(lat, 6), lon=round(lon, 6),
                                 px=int(cx), py=int(cy), crop=os.path.relpath(cpath, ROOT), source=m.url))
    print("  hits", n, flush=True)
pd.DataFrame(rows).to_csv(os.path.join(D, "hits.csv"), index=False)
print(pd.DataFrame(diag).groupby("map").sum().to_string())
print("total hits", len(rows))
