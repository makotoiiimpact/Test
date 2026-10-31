"""Step 1.6a: Clark County RFCD daily gauge rainfall (2000-2025) -> per-gauge storm table for gauges in/near the study area."""
import os, io, json, zipfile, csv, hashlib, datetime
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
RF = os.path.join(DATA, "rfcd")
NEAR = (-115.9, 35.1, -114.4, 36.25)   # hydrology buffer + margin

g = json.load(open(os.path.join(RF, "gauges_rain.geojson")))
gauges = pd.DataFrame([dict(numid=f["properties"]["numid"], name=f["properties"]["name"],
                            lon=f["geometry"]["coordinates"][0], lat=f["geometry"]["coordinates"][1]) for f in g["features"]])
gauges = gauges[gauges.lon.between(NEAR[0], NEAR[2]) & gauges.lat.between(NEAR[1], NEAR[3])]

frames = []
for y in range(2000, 2026):
    z = zipfile.ZipFile(os.path.join(RF, f"rainfall_{y}.zip"))
    raw = z.open(z.namelist()[0]).read().decode("utf-8-sig")
    first = raw.split("\n", 1)[0].split(",")[0].strip()
    df = pd.read_csv(io.StringIO(raw), header=0 if not first.isdigit() else None)
    df = df.iloc[:, :3]; df.columns = ["numid", "date", "in"]
    df["date"] = pd.to_datetime(df["date"], format="mixed").dt.normalize()
    df["in"] = pd.to_numeric(df["in"], errors="coerce")
    frames.append(df[df.numid.isin(gauges.numid)])
r = pd.concat(frames).dropna(subset=["in"])
r = r.groupby(["numid", "date"], as_index=False)["in"].sum()
r = r[(r["in"] >= 0) & (r["in"] < 15)]      # drop obvious sensor errors (>15 in/day)
# QC: a day above 3 in at one gauge is kept only if a gauge within 15 km got >= 25% of it the same day
import numpy as np
xy = gauges.set_index("numid")[["lon", "lat"]]
def km(a, b):
    (x1, y1), (x2, y2) = xy.loc[a], xy.loc[b]
    return np.hypot((x1 - x2) * 90.4, (y1 - y2) * 111.0)
big = r[r["in"] > 3.0]
bad = []
for i, row in big.iterrows():
    same = r[(r.date == row.date) & (r.numid != row.numid)]
    ok = any(km(row.numid, o.numid) <= 15 and o["in"] >= 0.25 * row["in"] for _, o in same.iterrows())
    if not ok: bad.append(i)
print("QC dropped", len(bad), "uncorroborated >3 in gauge-days")
r = r.drop(index=bad)
r.to_csv(os.path.join(DATA, "rain_gauge_daily.csv.gz"), index=False)

top = (r.sort_values("in", ascending=False).groupby("numid").head(5)
         .merge(gauges, on="numid").sort_values(["numid", "in"], ascending=[True, False]))
summ = r.groupby("numid").agg(days=("in", "size"), first=("date", "min"), last=("date", "max"),
                              max_day_in=("in", "max")).reset_index().merge(gauges, on="numid")
summ["max_day_date"] = summ.numid.map(r.loc[r.groupby("numid")["in"].idxmax()].set_index("numid")["date"])
summ.to_csv(os.path.join(DATA, "rain_gauges_summary.csv"), index=False)
for p, n in (("rain_gauge_daily.csv.gz", len(r)), ("rain_gauges_summary.csv", len(summ))):
    with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
        csv.writer(f).writerow([f"RFCD rainfall ({p})", "https://gustfront.ccrfcd.org/data/rainfall_1988_to_2025.zip + gaugeservices/geojson?type=STG",
                                p, n, hashlib.sha256(open(os.path.join(DATA, p), "rb").read()).hexdigest()[:16],
                                datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
box = summ[summ.lon.between(-115.75, -114.55) & summ.lat.between(35.2, 35.98)]
print(box.sort_values("lat")[["numid", "name", "days", "first", "last", "max_day_in", "max_day_date"]].to_string())
# storm days: any gauge in the area with >= 1.0 in
big = r[r["in"] >= 1.0].groupby("date")["in"].agg(["max", "size"]).sort_values("max", ascending=False)
big.to_csv(os.path.join(DATA, "rain_storm_days.csv"))
print("storm days >=1in:", len(big)); print(big.head(15))
