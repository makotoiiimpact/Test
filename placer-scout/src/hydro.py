"""Step 1.4b: drainage network per hydrology window (D8, pysheds). Writes fdir/acc/filled/hand rasters + stream branches."""
import os, sys, json, time, resource
import numpy as np, rasterio
if not hasattr(np, "in1d"): np.in1d = np.isin   # pysheds still calls the removed numpy alias
from pysheds.grid import Grid

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
STREAM_KM2 = 0.25          # contributing area that defines a "wash"
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)

def run(w):
    t = time.time(); path = os.path.join(DATA, f"dem_{w}.tif")
    grid = Grid.from_raster(path); dem = grid.read_raster(path)
    with rasterio.open(path) as s:
        lat = s.bounds.bottom + (s.bounds.top - s.bounds.bottom) / 2
        dy = abs(s.transform.e) * 111_320; dx = s.transform.a * 111_320 * np.cos(np.radians(lat)); prof = s.profile
    cell_km2 = dx * dy / 1e6; thresh = STREAM_KM2 / cell_km2
    dem = grid.fill_pits(dem); dem = grid.fill_depressions(dem); dem = grid.resolve_flats(dem)
    print(w, "filled", round(time.time() - t), "s", flush=True)
    fdir = grid.flowdir(dem, dirmap=DIRMAP)
    acc = grid.accumulation(fdir, dirmap=DIRMAP)
    print(w, "acc", round(time.time() - t), "s; cell", round(dx, 1), "x", round(dy, 1), "m; thresh cells", int(thresh), flush=True)
    streams = acc > thresh
    hand = grid.compute_hand(fdir, dem, streams, dirmap=DIRMAP)
    print(w, "hand", round(time.time() - t), "s", flush=True)
    def wr(name, arr, dtype, nodata):
        p = dict(prof); p.update(dtype=dtype, nodata=nodata, compress="deflate")
        with rasterio.open(os.path.join(DATA, f"{name}_{w}.tif"), "w", **p) as d:
            d.write(np.asarray(arr).astype(dtype), 1)
    wr("filled", dem, "float32", -999999.0); wr("fdir", fdir, "uint8", 0); wr("acc", acc, "float32", -1); wr("hand", hand, "float32", -1)
    net = grid.extract_river_network(fdir, streams, dirmap=DIRMAP)
    json.dump(net, open(os.path.join(DATA, f"streams_{w}.geojson"), "w"))
    json.dump({"window": w, "dx_m": dx, "dy_m": dy, "stream_km2": STREAM_KM2, "thresh_cells": thresh,
               "branches": len(net["features"])}, open(os.path.join(DATA, f"hydro_{w}.json"), "w"))
    print(w, "done", len(net["features"]), "branches", round(time.time() - t), "s; peak RSS GB", round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2), flush=True)

for w in (sys.argv[1:] or ["west", "east"]):
    run(w)
