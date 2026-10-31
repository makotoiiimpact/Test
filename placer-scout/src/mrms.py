"""Step 1.6c: MRMS multi-sensor 24 h rainfall (AWS open data, no login) for candidate storm days since 2020-10-15.
Writes per-cell max 24 h rain (5x5 km smoothed) and the date of that max."""
import os, csv, hashlib, datetime, json
import numpy as np, pandas as pd, rasterio
from rasterio.windows import from_bounds
from scipy.ndimage import uniform_filter

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
NEAR = (-115.9, 35.1, -114.4, 36.25)
STUDY_GAUGE_BOX = (-115.75, 35.2, -114.55, 35.98)
URL = "https://noaa-mrms-pds.s3.amazonaws.com/CONUS/MultiSensor_QPE_24H_Pass2_00.00/{d}/MRMS_MultiSensor_QPE_24H_Pass2_00.00_{d}-120000.grib2.gz"

r = pd.read_csv(os.path.join(DATA, "rain_gauge_daily.csv.gz"), parse_dates=["date"])
g = pd.read_csv(os.path.join(DATA, "rain_gauges_summary.csv"))
g = g[g.lon.between(STUDY_GAUGE_BOX[0], STUDY_GAUGE_BOX[2]) & g.lat.between(STUDY_GAUGE_BOX[1], STUDY_GAUGE_BOX[3]) & (g.max_day_in <= 5)]
days = set(r[r.numid.isin(g.numid) & (r["in"] >= 0.5) & (r.date >= "2020-10-15")].date.dt.date)
ev = pd.read_csv(os.path.join(DATA, "storm_events.csv"), dtype=str)
evd = pd.to_datetime(ev.BEGIN_DATE_TIME, format="%d-%b-%y %H:%M:%S", errors="coerce").dt.date
days |= {d for d in evd.dropna() if d >= datetime.date(2020, 10, 15)}
days |= {datetime.date(2026, 7, 1) + datetime.timedelta(i) for i in range(92)}        # no RFCD file for 2026 yet
days = sorted(days)
print("candidate days", len(days), flush=True)

best = None; best_day = None; used = []; nbytes = 0
for d in days:
    # 24 h accumulation ending 12Z next day covers the local storm day (monsoon storms peak in the afternoon/evening)
    tag = (d + datetime.timedelta(1)).strftime("%Y%m%d")
    try:
        with rasterio.open("/vsigzip//vsicurl/" + URL.format(d=tag)) as s:
            w = from_bounds(*NEAR, s.transform); a = s.read(1, window=w).astype("float32"); tr = s.window_transform(w)
    except Exception as e:
        print("miss", d, str(e)[:80], flush=True); continue
    a[a < 0] = np.nan
    a = uniform_filter(np.nan_to_num(a), size=5)          # ~5 km mean: radar cell noise vs. small catchments
    if best is None:
        best = a.copy(); best_day = np.full(a.shape, int(d.strftime("%Y%m%d")), dtype="int32")
    upd = a > best; best[upd] = a[upd]; best_day[upd] = int(d.strftime("%Y%m%d"))
    used.append(str(d)); nbytes += 3_400_000
prof = dict(driver="GTiff", height=best.shape[0], width=best.shape[1], count=1, crs="EPSG:4326", transform=tr, compress="deflate")
with rasterio.open(os.path.join(DATA, "mrms_max24h_mm.tif"), "w", dtype="float32", **prof) as o: o.write(best, 1)
with rasterio.open(os.path.join(DATA, "mrms_max24h_date.tif"), "w", dtype="int32", **prof) as o: o.write(best_day, 1)
json.dump(used, open(os.path.join(DATA, "mrms_days_used.json"), "w"))
with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
    csv.writer(f).writerow(["MRMS 24h QPE Pass2 (max over candidate storm days, 5 km smoothed)", URL.split("{d}")[0], "mrms_max24h_mm.tif", len(used),
                            hashlib.sha256(open(os.path.join(DATA, "mrms_max24h_mm.tif"), "rb").read()).hexdigest()[:16],
                            datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
print("days used", len(used), "approx MB", nbytes // 1_000_000, "max mm", float(np.nanmax(best)))
