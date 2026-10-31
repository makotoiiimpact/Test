"""Step 1.4a: clip 3DEP 1/3 arc-second (~10 m) DEM windows straight from the COGs on prd-tnm (no login)."""
import os, sys, csv, hashlib, datetime
import rasterio
from rasterio.merge import merge

BASE = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical"
TILES = {  # names verified via TNM Access API on 2026-10-31
    "n36w116": "USGS_13_n36w116_20260610.tif", "n36w115": "USGS_13_n36w115_20261023.tif",
    "n37w116": "USGS_13_n37w116_20260610.tif", "n37w115": "USGS_13_n37w115_20261023.tif",
}
# Hydrology windows (lon_min, lat_min, lon_max, lat_max). Each includes upstream margin.
WINDOWS = {
    "west": (-115.75, 35.55, -115.15, 36.15),   # Goodsprings / Yellow Pine / Potosi + Spring Mtns
    "east": (-115.25, 35.20, -114.55, 35.95),   # Crescent, Searchlight, Nelson/Eldorado Canyon
}
DATA = os.path.join(os.path.dirname(__file__), "..", "data")

def tiles_for(b):
    out = []
    for name in TILES:
        lat_top, lon_w = int(name[1:3]), -int(name[4:7])
        if b[0] < lon_w + 1 and b[2] > lon_w and b[1] < lat_top and b[3] > lat_top - 1:
            out.append(name)
    return out

for wname in (sys.argv[1:] or WINDOWS):
    b = WINDOWS[wname]
    urls = [f"/vsicurl/{BASE}/{t}/{TILES[t]}" for t in tiles_for(b)]
    srcs = [rasterio.open(u) for u in urls]
    arr, tr = merge(srcs, bounds=b, nodata=-999999.0)
    prof = srcs[0].profile
    prof.update(height=arr.shape[1], width=arr.shape[2], transform=tr, compress="deflate", predictor=3, BIGTIFF="IF_SAFER")
    path = os.path.join(DATA, f"dem_{wname}.tif")
    with rasterio.open(path, "w", **prof) as d:
        d.write(arr)
    with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
        csv.writer(f).writerow([f"dem_{wname}", ";".join(u.replace('/vsicurl/', '') for u in urls), os.path.basename(path),
                                arr.shape[1] * arr.shape[2], hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16],
                                datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
    print(wname, arr.shape, os.path.getsize(path) // 1_000_000, "MB", flush=True)
