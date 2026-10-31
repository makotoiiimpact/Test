"""Step 1.7 (hint only, top 25): did the wash bed change in Sentinel-2 SWIR across each target's biggest radar-era storm?"""
import os, json, datetime, requests
import numpy as np, pandas as pd, rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer

OUT = os.path.join(os.path.dirname(__file__), "..", "out"); DATA = os.path.join(os.path.dirname(__file__), "..", "data")
STAC = "https://earth-search.aws.element84.com/v1/search"
t = pd.read_csv(os.path.join(OUT, "targets.csv"))

def scene(lon, lat, d0, d1, latest):
    q = {"collections": ["sentinel-2-l2a"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
         "datetime": f"{d0}T00:00:00Z/{d1}T23:59:59Z", "query": {"eo:cloud_cover": {"lt": 10}}, "limit": 50}
    fs = requests.post(STAC, json=q, timeout=120).json().get("features", [])
    fs = [f for f in fs if (f["properties"].get("s2:nodata_pixel_percentage") or 0) < 50]
    fs.sort(key=lambda f: f["properties"]["datetime"], reverse=latest)
    return fs

def read(f, lon, lat, k, half=200):
    with rasterio.open(f["assets"][k]["href"]) as s:
        x, y = Transformer.from_crs(4326, s.crs, always_xy=True).transform(lon, lat)
        w = from_bounds(x - half, y - half, x + half, y + half, s.transform)
        return s.read(1, window=w, boundless=True, fill_value=0).astype("float32"), s.res[0]

rows = []
for _, r in t.iterrows():
    out = {"rank": r["rank"], "s2_storm_date": "", "s2_before": "", "s2_after": "", "s2_wash_change": np.nan, "s2_ring_change": np.nan, "s2_bed_changed": "no data"}
    d = pd.to_datetime(str(int(r.radar_max_date)), format="%Y%m%d").date() if pd.notna(r.radar_max_date) else None
    if d is None or d < datetime.date(2017, 1, 1):
        rows.append(out); continue
    out["s2_storm_date"] = str(d)
    for f_b in scene(r.lon, r.lat, d - datetime.timedelta(45), d - datetime.timedelta(1), latest=True)[:4]:
        for f_a in scene(r.lon, r.lat, d + datetime.timedelta(1), d + datetime.timedelta(45), latest=False)[:4]:
            if f_a["properties"]["grid:code"] != f_b["properties"]["grid:code"]: continue
            sb, res = read(f_b, r.lon, r.lat, "swir16"); sa, _ = read(f_a, r.lon, r.lat, "swir16")
            cb, _ = read(f_b, r.lon, r.lat, "scl"); ca, _ = read(f_a, r.lon, r.lat, "scl")
            n = min(sb.shape[0], sa.shape[0], cb.shape[0], ca.shape[0]); m = min(sb.shape[1], sa.shape[1], cb.shape[1], ca.shape[1])
            sb, sa, cb, ca = sb[:n, :m], sa[:n, :m], cb[:n, :m], ca[:n, :m]
            ok = (sb > 0) & (sa > 0) & np.isin(cb, [4, 5]) & np.isin(ca, [4, 5])          # clear vegetation / bare-soil pixels only
            yy, xx = np.indices(sb.shape); rr = np.hypot((yy - n / 2) * res, (xx - m / 2) * res)
            wash, ring = ok & (rr <= 25), ok & (rr >= 100) & (rr <= 150)
            if wash.sum() < 3 or ring.sum() < 20: continue
            dl = np.abs(sa - sb) / 10000.0
            cw, cr = float(dl[wash].mean()), float(dl[ring].mean())
            out.update(s2_before=f_b["id"], s2_after=f_a["id"], s2_wash_change=round(cw, 4), s2_ring_change=round(cr, 4),
                       s2_bed_changed="yes (hint)" if (cw > 2 * cr and cw > 0.02) else "no visible change")
            break
        if out["s2_before"]: break
    rows.append(out); print(out, flush=True)
C = pd.DataFrame(rows)
C.to_csv(os.path.join(DATA, "s2_change_top25.csv"), index=False)
print(C.s2_bed_changed.value_counts())
t = t.drop(columns=[c for c in C.columns if c != "rank" and c in t.columns]).merge(C, on="rank", how="left")
t.to_csv(os.path.join(OUT, "targets.csv"), index=False)
