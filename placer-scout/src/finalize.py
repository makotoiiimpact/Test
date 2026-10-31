"""Step 2c: apply the 1 m lidar check to the top 25 and re-rank them. Original 10 m score stays visible."""
import os
import numpy as np, pandas as pd
OUT = os.path.join(os.path.dirname(__file__), "..", "out"); FLOOR = 0.1
t = pd.read_csv(os.path.join(OUT, "targets.csv"))
if "rank_10m" not in t.columns: t["rank_10m"] = t["rank"]
alt = np.maximum.reduce([t.trap_slope_break.fillna(0), t.trap_junction.fillna(0), t.trap_widening.fillna(0)])
fallback = np.where(t.trap_type == "widening", np.maximum(t.trap_slope_break, t.trap_junction),
           np.where(t.trap_type == "slope_break", np.maximum(t.trap_junction, t.trap_widening), alt))
t["f_trap_lidar"] = np.where(t.lidar_confirms_trap == "no", np.maximum(fallback, FLOOR), t.f_trap)
# a trap halved for sitting by a road gets its full value back when 1 m lidar confirms it is a real channel feature
t["f_trap_lidar"] = np.where((t.lidar_confirms_trap == "yes") & t.trap_road_penalty.astype(bool), np.minimum(1.0, t.f_trap * 2), t.f_trap_lidar).round(3)
t["score_10m"] = t.score
t["score"] = (t.f_source * t.f_flood * t.f_trap_lidar).round(3)
t = t.sort_values(["score", "score_10m"], ascending=False).reset_index(drop=True); t["rank"] = range(1, len(t) + 1)
import glob, geopandas as gpd
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
P = gpd.GeoDataFrame(t[["rank"]], geometry=gpd.points_from_xy(t.lon, t.lat), crs=4326).to_crs(26911)
layers = [(os.path.basename(f)[4:-8], f) for f in glob.glob(os.path.join(DATA, "sma_*.geojson")) if not f.endswith("sma_BLM.geojson")]
layers += [("BLM monument/NCA", os.path.join(DATA, "nca_blm.geojson")), ("BLM wilderness", os.path.join(DATA, "wilderness_blm.geojson")),
           ("active claim", os.path.join(DATA, "claims_active.geojson"))]
best_d = np.full(len(t), np.inf); best_n = np.array([""] * len(t), dtype=object)
for name, f in layers:
    g = gpd.read_file(f)
    if not len(g): continue
    g = g.assign(geometry=g.geometry.make_valid()).to_crs(26911)
    j = gpd.sjoin_nearest(P[["geometry"]], g[["geometry"]], how="left", distance_col="d"); j = j[~j.index.duplicated()]
    d = j.d.reindex(P.index).values; better = d < best_d
    best_d[better] = d[better]; best_n[better] = name
t["nearest_exclusion"] = best_n; t["nearest_exclusion_m"] = np.round(best_d, 0)
t["boundary_risk"] = np.where(best_d < 100, "YES: within 100 m, check on the ground", "")
first = ["rank", "rank_10m", "lat", "lon", "district", "score", "score_10m", "f_source", "f_flood", "f_trap", "f_trap_lidar", "land_status", "nearest_exclusion", "nearest_exclusion_m", "boundary_risk", "acec_flag",
         "nearest_road", "nearest_road_m", "plss", "mlrs_active_claims_check", "mlrs_research_map"]
t = t[first + [c for c in t.columns if c not in first]]
t.to_csv(os.path.join(OUT, "targets.csv"), index=False)
print(t[["rank", "rank_10m", "district", "score", "score_10m", "f_source", "f_flood", "f_trap", "f_trap_lidar", "trap_type", "lidar_confirms_trap"]].to_string())
