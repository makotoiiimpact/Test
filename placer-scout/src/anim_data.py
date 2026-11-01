"""Data for explainer animations: MRMS daily 24 h QPE for Oct 1-31 2026 over the districts, a coarse hillshade basemap,
and Las Vegas airport daily rain (GHCN-Daily + NWS CLI). Writes cache/anim/*.npz|json (not committed)."""
import os, json, datetime, concurrent.futures as cf, requests, numpy as np, rasterio, pandas as pd
from rasterio.windows import from_bounds
from rasterio.vrt import WarpedVRT
from rasterio.transform import from_origin
OUT = os.path.join(os.path.dirname(__file__), "..", "cache", "anim"); os.makedirs(OUT, exist_ok=True)
NEAR = (-115.9, 35.1, -114.4, 36.25)
URL = "https://noaa-mrms-pds.s3.amazonaws.com/CONUS/MultiSensor_QPE_24H_Pass2_00.00/{d}/MRMS_MultiSensor_QPE_24H_Pass2_00.00_{d}-120000.grib2.gz"
def day(d):
    tag = (d + datetime.timedelta(1)).strftime("%Y%m%d")
    for _ in range(3):
        try:
            with rasterio.open("/vsigzip//vsicurl/" + URL.format(d=tag)) as s:
                w = from_bounds(*NEAR, s.transform); a = s.read(1, window=w).astype("float32"); a[a < 0] = 0; return d, a
        except Exception: pass
    return d, None
days = [datetime.date(2026, 10, 1) + datetime.timedelta(i) for i in range(31)]
if not os.path.exists(os.path.join(OUT, "radar_oct.npz")):
  with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(day, days))
  ok = [(d, a) for d, a in res if a is not None]; print("radar days", len(ok), "missing", [str(d) for d, a in res if a is None])
  np.savez_compressed(os.path.join(OUT, "radar_oct.npz"), days=np.array([d.isoformat() for d, _ in ok]), rain=np.stack([a for _, a in ok]))
# hillshade basemap on a 0.002 deg grid
res_ = 0.002; W = int((NEAR[2]-NEAR[0])/res_); H = int((NEAR[3]-NEAR[1])/res_); tr = from_origin(NEAR[0], NEAR[3], res_, res_)
BASE = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/"
tiles = {"n36w116": "USGS_13_n36w116_20260610.tif", "n36w115": "USGS_13_n36w115_20261023.tif", "n37w116": "USGS_13_n37w116_20260610.tif", "n37w115": "USGS_13_n37w115_20261023.tif"}
dem = np.full((H, W), np.nan, "float32")
for k, f in (tiles.items() if not os.path.exists(os.path.join(OUT, "dem.npz")) else []):
    with rasterio.open("/vsicurl/" + BASE + f"{k}/{f}") as s, WarpedVRT(s, crs="EPSG:4326", transform=tr, width=W, height=H, resampling=rasterio.enums.Resampling.average) as v:
        a = v.read(1, masked=True).filled(np.nan); m = np.isnan(dem) & ~np.isnan(a); dem[m] = a[m]
if not os.path.exists(os.path.join(OUT, "dem.npz")): np.savez_compressed(os.path.join(OUT, "dem.npz"), dem=dem, bounds=np.array(NEAR))
# Las Vegas airport daily rain, inches
g = pd.read_csv("https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/USW00023169.csv", usecols=["DATE", "PRCP"], low_memory=False)
g = g[g.DATE.str.startswith("2026-10")].dropna(); lv = {r.DATE: round(r.PRCP/254.0, 2) for r in g.itertuples()}
hdr = {"User-Agent": "placer-scout (hobby research)"}
prods = requests.get("https://api.weather.gov/products/types/CLI/locations/LAS", headers=hdr, timeout=60).json()["@graph"]
for p in prods:
    t = requests.get(p["@id"], headers=hdr, timeout=60).json()["productText"]
    if "CLIMATE SUMMARY FOR OCTOBER" not in t: continue
    dnum = int(t.split("CLIMATE SUMMARY FOR OCTOBER")[1].split()[0])
    try: pr = [l for l in t.split("PRECIPITATION (IN)")[1].splitlines() if l.strip().startswith("YESTERDAY")][0].split()[1]
    except Exception: continue
    key = f"2026-10-{dnum:02d}"
    if key not in lv: lv[key] = 0.0 if pr == "T" else float(pr)
json.dump(dict(sorted(lv.items())), open(os.path.join(OUT, "lv_oct.json"), "w"), indent=0)
print("LV days", len(lv), "total", round(sum(lv.values()), 2))
