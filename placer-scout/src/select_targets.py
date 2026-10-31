"""Step 3a: pick top 25 legal targets (spacing + per-district cap), attach road, PLSS and claim-check links -> out/targets.csv"""
import os, json, math, urllib.parse, requests
import numpy as np, pandas as pd, geopandas as gpd

DATA = os.path.join(os.path.dirname(__file__), "..", "data"); OUT = os.path.join(os.path.dirname(__file__), "..", "out")
N, MIN_SPACING_M, MAX_PER_DISTRICT, NAMED_MINE_M = 25, 1000, 10, 300
CLAIMS = "https://nlsdbpubgis.blm.gov/arcgis/rest/services/Mining_Claims/MiningClaims/MapServer"
PLSS = "https://gis.blm.gov/arcgis/rest/services/Cadastral/BLM_Natl_PLSS_CadNSDI/MapServer/3/query"

df = pd.read_csv(os.path.join(DATA, "scored_cells.csv.gz"), dtype={"top_source_id": str, "noaa_flood_event_id": str})
legal = df[df.legal_ok].sort_values("score", ascending=False).reset_index(drop=True)
pts = gpd.GeoDataFrame(legal, geometry=gpd.points_from_xy(legal.lon, legal.lat), crs=4326).to_crs(26911)
rej_path = os.path.join(DATA, "lidar_rejected.csv")        # spots whose 10 m trap was not confirmed by 1 m lidar (see lidar.py)
if os.path.exists(rej_path):
    rej = pd.read_csv(rej_path)
    rg = gpd.GeoDataFrame(rej, geometry=gpd.points_from_xy(rej.lon, rej.lat), crs=4326).to_crs(26911)
    jj = gpd.sjoin_nearest(pts[["geometry"]], rg[["geometry"]], how="left", distance_col="d"); jj = jj[~jj.index.duplicated()]
    keep = ~(jj.d <= 150).values
    print("skipping", int((~keep).sum()), "cells within 150 m of", len(rej), "lidar-rejected spots")
    pts = pts[keep].reset_index(drop=True); legal = legal[keep].reset_index(drop=True)

# named-mine check: within 300 m of a named mine/mill/dump record
src = gpd.read_file(os.path.join(DATA, "gold_sources.geojson"))
named = src[src.name.fillna("").str.strip().str.len().gt(0) & ~src.name.fillna("").str.fullmatch(r"(?i)(tunnel|shaft|adit|prospect|mine|pit)s?")].to_crs(26911)
j = gpd.sjoin_nearest(pts[["geometry"]], named[["name", "src_dataset", "geometry"]], how="left", distance_col="d")
j = j[~j.index.duplicated()]
pts["nearest_named_mine"] = j.name.values; pts["nearest_named_mine_m"] = j.d.round(0).values
pts["at_named_mine"] = pts.nearest_named_mine_m <= NAMED_MINE_M

sel, cnt = [], {}
xy = np.c_[pts.geometry.x, pts.geometry.y]
for i in range(len(pts)):
    if len(sel) == N: break
    dkey = pts.district.iat[i]
    if cnt.get(dkey, 0) >= MAX_PER_DISTRICT: continue
    if sel and np.min(np.hypot(*(xy[sel] - xy[i]).T)) < MIN_SPACING_M: continue
    sel.append(i); cnt[dkey] = cnt.get(dkey, 0) + 1
t = pts.iloc[sel].copy().reset_index(drop=True)

roads = gpd.read_file(os.path.join(DATA, "roads.geojson")).to_crs(26911)
r = gpd.sjoin_nearest(t[["geometry"]], roads[["FULLNAME", "MTFCC", "geometry"]], how="left", distance_col="d")
r = r[~r.index.duplicated()]
mt = {"S1100": "primary road", "S1200": "secondary road", "S1400": "local road", "S1500": "4WD/vehicular trail", "S1640": "service drive",
      "S1730": "alley", "S1740": "private road", "S1820": "bike path", "S1830": "bridle path", "S1710": "walkway", "S1500 ": "4WD trail"}
t["nearest_road"] = [f"{(n if isinstance(n, str) and n else 'unnamed')} ({mt.get(m, m)})" for n, m in zip(r.FULLNAME, r.MTFCC)]
t["nearest_road_m"] = r.d.round(0).values

def plss(lon, lat):
    try:
        f = requests.get(PLSS, params={"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                                       "outFields": "PRINMER,TWNSHPLAB,FRSTDIVLAB,SECDIVLAB", "returnGeometry": "false", "f": "json"}, timeout=60).json()["features"][0]["attributes"]
        return f"{f['PRINMER']} T{f['TWNSHPLAB'].split()[0]} R{f['TWNSHPLAB'].split()[1]} Sec {f['FRSTDIVLAB']} {f['SECDIVLAB'] or ''}".strip()
    except Exception:
        return "lookup failed"
t["plss"] = [plss(a, b) for a, b in zip(t.lon, t.lat)]
def claim_url(layer, lon, lat):
    q = {"geometry": f"{lon:.6f},{lat:.6f}", "geometryType": "esriGeometryPoint", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
         "outFields": "CSE_NR,CSE_NAME,CSE_DISP,BLM_PROD", "returnGeometry": "false", "f": "html"}
    return f"{CLAIMS}/{layer}/query?" + urllib.parse.urlencode(q)
t["mlrs_active_claims_check"] = [claim_url(1, a, b) for a, b in zip(t.lon, t.lat)]
t["mlrs_research_map"] = "https://mlrs.blm.gov/s/research-map"
t.insert(0, "rank", range(1, len(t) + 1))
t["lat"] = t.lat.round(6); t["lon"] = t.lon.round(6)
cols = ["rank", "lat", "lon", "district", "score", "f_source", "f_flood", "f_trap", "land_status", "acec_flag", "nearest_road", "nearest_road_m",
        "plss", "mlrs_active_claims_check", "mlrs_research_map", "source_basis", "top_source_name", "top_source_dataset", "top_source_id",
        "top_source_kind", "top_source_dist_m", "top_source_url", "altered_frac_upstream", "trap_type", "trap_slope_break", "trap_junction",
        "trap_widening", "grad_up", "grad_down", "floor_width_m", "floor_width_up_m", "drain_km2", "elev_m", "storm_max_24h_mm", "rain_basis",
        "radar_max24h_mm", "radar_max_date", "gauge_name", "gauge_dist_m", "gauge_max_day_mm", "gauge_max_date", "noaa_flood_event_id",
        "noaa_flood_date", "noaa_flood_dist_m", "flood_since", "closed_claim_case", "nearest_named_mine", "nearest_named_mine_m", "at_named_mine", "window"]
for c in ("score", "f_source", "f_flood", "f_trap", "altered_frac_upstream", "trap_slope_break", "trap_junction", "trap_widening", "grad_up", "grad_down",
          "storm_max_24h_mm", "radar_max24h_mm", "gauge_max_day_mm", "drain_km2"):
    t[c] = t[c].astype(float).round(3)
t[cols].to_csv(os.path.join(OUT, "targets.csv"), index=False)
legal.head(600).to_csv(os.path.join(DATA, "candidates_top600.csv"), index=False)
print(t[["rank", "district", "score", "f_source", "f_flood", "f_trap", "trap_type", "top_source_name", "top_source_dist_m", "nearest_named_mine_m", "at_named_mine", "plss"]].to_string())
print("districts:", cnt, "| all at named mines:", bool(t.at_named_mine.all()), "| at named mine count:", int(t.at_named_mine.sum()))
