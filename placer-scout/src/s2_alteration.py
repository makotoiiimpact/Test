"""Step 1.5: Sentinel-2 L2A (Earth Search / AWS COGs, no login) iron-oxide and clay band ratios on each hydrology window."""
import os, sys, json, csv, hashlib, datetime
import numpy as np, rasterio
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.windows import from_bounds
from rasterio.transform import from_origin

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
RES = 0.0002                                   # ~18-22 m target grid (geographic)
WINDOWS = {"west": (-115.75, 35.55, -115.15, 36.15), "east": (-115.25, 35.20, -114.55, 35.95)}
BANDS = ("blue", "red", "nir08", "swir16", "swir22", "scl")
scenes = json.load(open(os.path.join(DATA, "s2_scenes.json")))

def run(w):
    b = WINDOWS[w]; W = int(round((b[2] - b[0]) / RES)); H = int(round((b[3] - b[1]) / RES))
    dst_tr = from_origin(b[0], b[3], RES, RES)
    out = {k: np.full((H, W), np.nan, dtype="float32") for k in BANDS}
    used = []
    for sc in scenes:
        for k in BANDS:
            with rasterio.open(sc["assets"][k]) as s:
                sb = transform_bounds("EPSG:4326", s.crs, *b)
                l, bt, r, t = max(sb[0], s.bounds.left), max(sb[1], s.bounds.bottom), min(sb[2], s.bounds.right), min(sb[3], s.bounds.top)
                if l >= r or bt >= t: break
                win = from_bounds(l, bt, r, t, s.transform)
                f = max(1, int(round(20 / s.res[0])))                         # read 10 m bands at 20 m via overviews
                shape = (max(1, int(win.height // f)), max(1, int(win.width // f)))
                a = s.read(1, window=win, out_shape=shape, resampling=Resampling.nearest if k == "scl" else Resampling.average).astype("float32")
                src_tr = s.window_transform(win) * rasterio.Affine.scale(win.width / shape[1], win.height / shape[0])
                if k != "scl": a[a == 0] = np.nan
                else: a[a == 0] = np.nan
                tmp = np.full((H, W), np.nan, dtype="float32")
                reproject(a, tmp, src_transform=src_tr, src_crs=s.crs, dst_transform=dst_tr, dst_crs="EPSG:4326",
                          src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.nearest if k == "scl" else Resampling.bilinear)
                fill = np.isnan(out[k]) & ~np.isnan(tmp); out[k][fill] = tmp[fill]
        else:
            used.append(sc["id"])
    bl, rd, nir, s1, s2, scl = (out[k] for k in BANDS)
    ndvi = (nir - rd) / (nir + rd)
    bad = np.isin(scl, [0, 1, 3, 6, 8, 9, 10, 11]) | (ndvi > 0.25) | np.isnan(bl) | (rd < 300)
    fe = rd / bl; oh = s1 / s2
    fe[bad] = np.nan; oh[bad] = np.nan
    z = lambda x: (x - np.nanmean(x)) / np.nanstd(x)
    zfe, zoh = z(fe), z(oh)
    prof = dict(driver="GTiff", height=H, width=W, count=1, crs="EPSG:4326", transform=dst_tr, dtype="float32", compress="deflate", nodata=np.nan)
    for name, arr in (("s2_feox_z", zfe), ("s2_clay_z", zoh)):
        p = os.path.join(DATA, f"{name}_{w}.tif")
        with rasterio.open(p, "w", **prof) as o: o.write(arr.astype("float32"), 1)
    with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
        csv.writer(f).writerow([f"Sentinel-2 L2A FeOx/clay z-scores ({w})", "https://earth-search.aws.element84.com/v1 :: " + ";".join(used),
                                f"s2_feox_z_{w}.tif;s2_clay_z_{w}.tif", int(np.isfinite(zfe).sum()),
                                hashlib.sha256(zfe.tobytes()).hexdigest()[:16], datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
    print(w, "scenes", used, "valid px", int(np.isfinite(zfe).sum()), "of", H * W, flush=True)

for w in (sys.argv[1:] or WINDOWS):
    run(w)
