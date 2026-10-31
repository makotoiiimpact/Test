"""Step 2b: 1 m lidar check for the top 25 targets only (USGS 3DEP 1 m DEM COGs, windowed reads, no login)."""
import os, sys, math, json, requests
import numpy as np, pandas as pd, rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer
sys.path.insert(0, os.path.dirname(__file__))
import score

DATA = os.path.join(os.path.dirname(__file__), "..", "data"); OUT = os.path.join(os.path.dirname(__file__), "..", "out")
t = pd.read_csv(os.path.join(OUT, "targets.csv"))
API = "https://tnmaccess.nationalmap.gov/api/v1/products"

def tiles_at(lon, lat):
    r = requests.get(API, params={"datasets": "Digital Elevation Model (DEM) 1 meter", "bbox": f"{lon-0.002},{lat-0.002},{lon+0.002},{lat+0.002}",
                                  "max": 20, "outputFormat": "JSON"}, timeout=120).json()
    items = [i for i in r.get("items", []) if i["boundingBox"]["minX"] <= lon <= i["boundingBox"]["maxX"] and i["boundingBox"]["minY"] <= lat <= i["boundingBox"]["maxY"]]
    return sorted(items, key=lambda i: i.get("publicationDate", ""), reverse=True)

rows = []
cells = {}
for w in ("west", "east"):
    if (t.window == w).any(): cells[w] = score.window_cells(w)
for _, r in t.iterrows():
    out = {"rank": r["rank"], "lidar_available": False, "lidar_tile": "", "lidar_published": "", "lidar_project": "", "lidar_url": ""}
    items = tiles_at(r.lon, r.lat)
    it = None
    for cand in items:                      # newest tile that actually has data at the target (projects are clipped at state lines)
        with rasterio.open(cand["downloadURL"]) as s:
            x, y = Transformer.from_crs(4326, s.crs, always_xy=True).transform(r.lon, r.lat)
            v = next(s.sample([(x, y)]))[0]
            if s.nodata is None or (v != s.nodata and np.isfinite(v) and v > -1000): it = cand; break
    if it is not None:
        out.update(lidar_available=True, lidar_tile=it["title"], lidar_published=it.get("publicationDate", ""), lidar_project=it["title"].split()[-1], lidar_url=it["downloadURL"])
        C = cells[r.window]; tr = C["tr"]
        i0 = np.array([int((r.lat - tr.f) / tr.e) * C["W"] + int((r.lon - tr.c) / tr.a)])
        path_dn, path_up = [i0[0]], [i0[0]]
        for nxt, path in ((C["down"], path_dn), (C["up"], path_up)):
            d = 0.0; c = i0[0]
            while d < 150 and nxt[c] >= 0:
                c = nxt[c]; d += C["step"][c]; path.append(c)
        ll = lambda c: (tr.c + (c % C["W"] + 0.5) * tr.a, tr.f + (c // C["W"] + 0.5) * tr.e)
        with rasterio.open(it["downloadURL"]) as s:
            T = Transformer.from_crs(4326, s.crs, always_xy=True)
            xs, ys = T.transform(*zip(*[ll(c) for c in path_up + path_dn]))
            pad = 40; b = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
            win = from_bounds(*b, s.transform).round_offsets().round_lengths()
            z = s.read(1, window=win, masked=True).astype("float64").filled(np.nan); wt = s.window_transform(win)
        def zmin(x, y, rad=5):
            cc, rr = ~wt * (x, y); cc, rr = int(cc), int(rr)
            a = z[max(0, rr - rad):rr + rad + 1, max(0, cc - rad):cc + rad + 1]
            return np.nanmin(a) if a.size and np.isfinite(a).any() else np.nan
        def floor_width(x, y, rad=30):
            cc, rr = ~wt * (x, y); cc, rr = int(cc), int(rr)
            a = z[max(0, rr - rad):rr + rad + 1, max(0, cc - rad):cc + rad + 1]
            if not np.isfinite(a).any(): return np.nan
            return float((a < np.nanmin(a) + 0.5).sum()) / (2 * rad)        # area of near-bed ground / box width = mean floor width (m)
        n_up = len(path_up); xt, yt = xs[0], ys[0]
        xu, yu = xs[n_up - 1], ys[n_up - 1]; xd, yd = xs[-1], ys[-1]
        zt, zu, zd = zmin(xt, yt), zmin(xu, yu), zmin(xd, yd)
        du, dd = math.hypot(xu - xt, yu - yt), math.hypot(xd - xt, yd - yt)
        gu = (zu - zt) / du if du > 30 else np.nan; gd = (zt - zd) / dd if dd > 30 else np.nan
        wt_, wu_ = floor_width(xt, yt), floor_width(xu, yu)
        out.update(lidar_grad_up=round(gu, 4), lidar_grad_down=round(gd, 4), lidar_floor_width_m=round(wt_, 1), lidar_floor_width_up_m=round(wu_, 1))
        checks = []
        if r.trap_type == "slope_break": checks.append(np.isfinite(gu) and np.isfinite(gd) and gu > 0.02 and gd < 0.6 * gu)
        if r.trap_type == "widening": checks.append(np.isfinite(wt_) and np.isfinite(wu_) and wt_ > 1.3 * max(wu_, 3))
        if r.trap_type == "junction": checks.append(None)       # a confluence is a planform feature; 1 m adds nothing beyond the 10 m network
        out["lidar_confirms_trap"] = {True: "yes", False: "no"}.get(checks[0], "not tested") if checks else "not tested"
    else:
        out["lidar_confirms_trap"] = "no lidar (10 m only)"
    rows.append(out); print(r["rank"], out["lidar_tile"][-40:], out.get("lidar_grad_up"), out.get("lidar_grad_down"), out.get("lidar_floor_width_m"), out.get("lidar_floor_width_up_m"), out["lidar_confirms_trap"], flush=True)
L = pd.DataFrame(rows)
t = t.drop(columns=[c for c in L.columns if c != "rank" and c in t.columns]).merge(L, on="rank", how="left")
t.to_csv(os.path.join(OUT, "targets.csv"), index=False)
rej = t[t.lidar_confirms_trap == "no"][["lat", "lon", "trap_type", "lidar_tile"]]
rp = os.path.join(DATA, "lidar_rejected.csv")
if len(rej):
    rej = pd.concat([pd.read_csv(rp), rej]) if os.path.exists(rp) else rej
    rej.drop_duplicates(["lat", "lon"]).to_csv(rp, index=False)
print("LIDAR_REJECTED_THIS_ROUND", int((t.lidar_confirms_trap == "no").sum()))
