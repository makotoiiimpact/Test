"""Which scored, legal wash spots sit near a mapped trail? BLM GTLF trails (non-motorized, foot/horse, public, not assessed) +
USGS National Map trails. Writes out/trail_washes.csv (best spot per ~1 km cluster)."""
import os, numpy as np, pandas as pd, geopandas as gpd
ROOT = os.path.join(os.path.dirname(__file__), ".."); DATA = os.path.join(ROOT, "data")
d = pd.read_csv(os.path.join(DATA, "scored_cells.csv.gz"), low_memory=False); d = d[d.legal_ok]
tr = pd.concat([gpd.read_file(os.path.join(DATA, f)) for f in ("gtlf_4.geojson", "gtlf_5.geojson", "gtlf_6.geojson", "gtlf_7.geojson", "usgs_trails.geojson")])
tr = gpd.GeoDataFrame(tr, crs=4326).to_crs(26911)
P = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(26911)
j = gpd.sjoin_nearest(P[["geometry"]], tr[["route_class", "name", "geometry"]], how="left", distance_col="trail_m"); j = j[~j.index.duplicated()]
P["trail_m"] = j.trail_m.round(0).values; P["trail_name"] = j.name.fillna("").values; P["trail_class"] = j.route_class.values
near = P[P.trail_m <= 300].sort_values("score", ascending=False)
sel = []
for i, r in near.iterrows():
    if all(r.geometry.distance(near.loc[k].geometry) > 1000 for k in sel): sel.append(i)
    if len(sel) == 12: break
out = near.loc[sel, ["lat", "lon", "district", "score", "f_source", "f_flood", "f_trap", "trap_type", "top_source_name", "top_source_dist_m",
                     "nearest_recorded_gold_upstream_m", "trail_name", "trail_class", "trail_m", "land_status", "recent_max24h_mm", "recent_vs_normal"]]
out.to_csv(os.path.join(ROOT, "out", "trail_washes.csv"), index=False)
pd.set_option("display.width", 260)
print("legal scored wash spots:", len(P), "| within 300 m of a trail:", len(near))
print(out.round(3).to_string(index=False))
