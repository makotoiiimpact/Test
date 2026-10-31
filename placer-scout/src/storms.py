"""Step 1.6b: NOAA Storm Events (NCEI bulk CSV, no login) -> flash-flood / heavy-rain events in or near the study area, 2000-2026."""
import os, io, re, gzip, csv, hashlib, datetime, requests
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
BASE = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
TYPES = {"Flash Flood", "Flood", "Heavy Rain", "Debris Flow"}
NEAR = (-115.9, 35.1, -114.4, 36.25)
listing = requests.get(BASE, timeout=120).text
files = sorted(set(re.findall(r"StormEvents_details-ftp_v1\.0_d(\d{4})_c\d+\.csv\.gz", listing)))
names = {y: re.search(rf"StormEvents_details-ftp_v1\.0_d{y}_c\d+\.csv\.gz", listing).group(0) for y in files}
out, nbytes = [], 0
for y in sorted(names):
    if int(y) < 2000: continue
    r = requests.get(BASE + names[y], timeout=300); nbytes += len(r.content)
    df = pd.read_csv(io.BytesIO(gzip.decompress(r.content)), dtype=str, low_memory=False)
    df = df[df.EVENT_TYPE.isin(TYPES) & df.STATE.isin(["NEVADA", "CALIFORNIA", "ARIZONA"])]
    for c in ("BEGIN_LAT", "BEGIN_LON", "END_LAT", "END_LON"): df[c] = pd.to_numeric(df[c], errors="coerce")
    inbox = df.BEGIN_LON.between(NEAR[0], NEAR[2]) & df.BEGIN_LAT.between(NEAR[1], NEAR[3])
    clark = (df.STATE == "NEVADA") & df.CZ_NAME.str.contains("CLARK|LAS VEGAS|SPRING MOUNTAINS|LAKE MEAD|SOUTHERN|SEARCHLIGHT|NELSON|EASTERN", na=False)
    keep = df[inbox | (clark & df.BEGIN_LAT.isna())]
    out.append(keep); print(y, len(df), "->", len(keep), flush=True)
ev = pd.concat(out)
cols = ["EVENT_ID", "EPISODE_ID", "EVENT_TYPE", "STATE", "CZ_TYPE", "CZ_NAME", "BEGIN_YEARMONTH", "BEGIN_DAY", "BEGIN_DATE_TIME",
        "END_DATE_TIME", "BEGIN_LOCATION", "BEGIN_LAT", "BEGIN_LON", "END_LAT", "END_LON", "FLOOD_CAUSE", "SOURCE", "EVENT_NARRATIVE"]
ev = ev[cols]; path = os.path.join(DATA, "storm_events.csv"); ev.to_csv(path, index=False)
with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
    csv.writer(f).writerow(["NOAA Storm Events (flood/heavy rain, 2000-2026)", BASE, "storm_events.csv", len(ev),
                            hashlib.sha256(open(path, "rb").read()).hexdigest()[:16], datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
print("downloaded MB", nbytes // 1_000_000, "events kept", len(ev), "with coords", ev.BEGIN_LAT.notna().sum())
print(ev.EVENT_TYPE.value_counts())
