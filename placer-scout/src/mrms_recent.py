"""Recent-rain layer: MRMS 24 h QPE (12Z) for every day Aug 1 - Oct 30 of 2026, and the same window in 2023-2025 for comparison.
Writes per-cell: recent max 24 h (mm, 5 km mean), recent total (mm), baseline mean total for 2023-25, and the date of the recent max."""
import os, csv, json, hashlib, datetime, concurrent.futures as cf
import numpy as np, rasterio
from rasterio.windows import from_bounds
from scipy.ndimage import uniform_filter
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
NEAR = (-115.9, 35.1, -114.4, 36.25)
URL = "https://noaa-mrms-pds.s3.amazonaws.com/CONUS/MultiSensor_QPE_24H_Pass2_00.00/{d}/MRMS_MultiSensor_QPE_24H_Pass2_00.00_{d}-120000.grib2.gz"
def day(d):
    tag = (d + datetime.timedelta(1)).strftime("%Y%m%d")       # 24 h ending 12Z next day = local storm day
    for _ in range(3):
        try:
            with rasterio.open("/vsigzip//vsicurl/" + URL.format(d=tag)) as s:
                w = from_bounds(*NEAR, s.transform); a = s.read(1, window=w).astype("float32"); a[a < 0] = 0
                return d, a, s.window_transform(w)
        except Exception:
            pass
    return d, None, None
def window(year):
    return [datetime.date(year, 8, 1) + datetime.timedelta(i) for i in range(91)]
res = {}
with cf.ThreadPoolExecutor(6) as ex:
    for y in (2023, 2024, 2025, 2026):
        res[y] = list(ex.map(day, window(y)))
        print(y, "days ok", sum(a is not None for _, a, _ in res[y]), flush=True)
tr = next(t for _, a, t in res[2026] if a is not None)
tot = {y: sum(a for _, a, _ in res[y] if a is not None) for y in res}
r26 = [(d, a) for d, a, _ in res[2026] if a is not None]
sm = np.stack([uniform_filter(a, 5) for _, a in r26]); imax = sm.argmax(0)
recent_max = sm.max(0); recent_date = np.vectorize(lambda i: int(r26[i][0].strftime("%Y%m%d")))(imax).astype("int32")
base = np.mean([tot[y] for y in (2023, 2024, 2025)], axis=0)
prof = dict(driver="GTiff", height=tr and recent_max.shape[0], width=recent_max.shape[1], count=1, crs="EPSG:4326", transform=tr, compress="deflate")
for name, arr, dt in (("recent_max24h_mm", recent_max, "float32"), ("recent_max24h_date", recent_date, "int32"),
                      ("recent_total_mm", uniform_filter(tot[2026], 5), "float32"), ("baseline_total_mm", uniform_filter(base, 5), "float32")):
    with rasterio.open(os.path.join(DATA, f"{name}.tif"), "w", dtype=dt, **prof) as o: o.write(arr.astype(dt), 1)
with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
    csv.writer(f).writerow(["MRMS 24h QPE, Aug 1-Oct 30 of 2023-2026 (recent rain vs baseline)", URL.split("{d}")[0], "recent_*.tif;baseline_total_mm.tif",
                            sum(sum(a is not None for _, a, _ in v) for v in res.values()), hashlib.sha256(recent_max.tobytes()).hexdigest()[:16],
                            datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
box = (slice(None), slice(None))
print("study-area totals (mean over window): 2026 %.0f mm vs 2023-25 mean %.0f mm; recent max 24h %.0f mm" % (tot[2026].mean(), base.mean(), recent_max.max()))
for y in (2023, 2024, 2025, 2026): print(y, "mean total %.0f mm" % tot[y].mean())
