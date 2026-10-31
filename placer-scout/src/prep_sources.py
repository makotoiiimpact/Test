"""Step 1.1: combine MRDS + USMIN topo mine features + GNIS into one gold-source point layer.
Every row keeps its origin dataset and record id so a score can be traced back."""
import os, csv, hashlib, datetime
import pandas as pd, geopandas as gpd
from shapely.ops import transform

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
BOX = (-115.7, 35.0, -114.5, 36.1)
NEAR_AU_M = 1000   # USMIN/GNIS features count as gold-related only within this distance of an MRDS gold record
swap = lambda g: transform(lambda x, y, z=None: (y, x), g)   # WFS 1.1 EPSG:4326 returns lat,lon

def read_wfs(name):
    g = gpd.read_file(os.path.join(DATA, name))
    g["geometry"] = g.geometry.apply(swap)
    return g.set_crs(4326, allow_override=True)

# --- MRDS ---
m = read_wfs("mrds_box.gml")
codes = m.code_list.fillna("").str.split()
m = m[codes.apply(lambda c: "AU" in c)].copy()
w_stat = {"Producer": 1.0, "Past Producer": 1.0, "Plant": 1.0, "Prospect": 0.5, "Occurrence": 0.4, "Unknown": 0.3}
mrds = gpd.GeoDataFrame({
    "src_dataset": "MRDS", "src_id": m.dep_id.astype(str), "name": m.site_name,
    "kind": m.dev_stat.map(lambda s: "mill/plant" if s == "Plant" else "mine/deposit"),
    "detail": m.dev_stat + " | " + m.code_list, "weight": m.dev_stat.map(w_stat).fillna(0.3),
    "url": m.url}, geometry=m.geometry, crs=4326)

au_utm = mrds.to_crs(26911)
def near_au(g):
    d = gpd.sjoin_nearest(g.to_crs(26911), au_utm[["geometry"]], how="left", distance_col="_d")
    d = d[~d.index.duplicated()]
    return (d["_d"] <= NEAR_AU_M).reindex(g.index).fillna(False).values

# --- USMIN topo mine features ---
pt = read_wfs("usmin_points.gml"); pg = read_wfs("usmin_polygons.gml")
pg = pg.assign(geometry=pg.geometry.representative_point())
u = pd.concat([pt, pg], ignore_index=True)
base = {"Mine Shaft": 0.6, "Adit": 0.6, "Open Pit Mine": 0.6, "Mine": 0.6, "Prospect Pit": 0.3,
        "Tailings - Undifferentiated": 0.8, "Tailings - Pond": 0.8, "Mine Dump": 0.8, "Disturbed Surface": 0.3}
u = u[u.ftr_type.isin(base)].copy()
u = gpd.GeoDataFrame(u, geometry="geometry", crs=4326)
# the same shaft/adit/pit is often digitised from several topo editions: keep one per type within 30 m
uu = u.to_crs(26911); uu["_k"] = uu.ftr_type + "_" + (uu.geometry.x // 30).astype(int).astype(str) + "_" + (uu.geometry.y // 30).astype(int).astype(str)
keep = ~uu.duplicated("_k")
pairs = gpd.sjoin(uu[keep][["ftr_type", "geometry"]], uu[keep][["ftr_type", "geometry"]].assign(geometry=lambda g: g.buffer(30)), predicate="within")
pairs = pairs[(pairs.index != pairs.index_right) & (pairs.ftr_type_left == pairs.ftr_type_right)]
drop = set(max(a, b) for a, b in zip(pairs.index, pairs.index_right))
keep &= ~uu.index.isin(drop)
print("USMIN duplicates across topo editions removed:", int((~keep).sum()))
u = u[keep.values]
nau = near_au(u)
usmin = gpd.GeoDataFrame({
    "src_dataset": "USMIN_topo", "src_id": u.gml_id.astype(str), "name": u.ftr_name.fillna(""),
    "kind": u.ftr_type.map(lambda t: "tailings/dump" if ("Tailings" in t or "Dump" in t) else "mine/deposit"),
    "detail": u.ftr_type + " | topo " + u.topo_name.fillna("") + " " + u.topo_date.fillna("").astype(str),
    "weight": [base[t] if a else round(base[t] * 0.25, 3) for t, a in zip(u.ftr_type, nau)],
    "url": u.url}, geometry=u.geometry, crs=4326)
usmin["near_mrds_gold"] = nau

# --- GNIS mines and mills ---
gn = pd.read_csv(os.path.join(DATA, "gnis/Text/DomesticNames_NV.txt"), sep="|", dtype=str, encoding="utf-8-sig")
gn["lat"] = gn.prim_lat_dec.astype(float); gn["lon"] = gn.prim_long_dec.astype(float)
gn = gn[(gn.lon.between(BOX[0], BOX[2])) & (gn.lat.between(BOX[1], BOX[3]))]
is_mill = gn.feature_name.str.contains(r"\bMill\b", case=False, regex=True) & ~gn.feature_name.str.contains("Spring|Canyon|Wash", case=False)
gn = gn[(gn.feature_class == "Mine") | is_mill.reindex(gn.index, fill_value=False)]
gn = gpd.GeoDataFrame(gn, geometry=gpd.points_from_xy(gn.lon, gn.lat), crs=4326)
nau_g = near_au(gn)
gnis = gpd.GeoDataFrame({
    "src_dataset": "GNIS", "src_id": gn.feature_id, "name": gn.feature_name,
    "kind": ["mill/plant" if "mill" in n.lower() else "mine/deposit" for n in gn.feature_name],
    "detail": gn.feature_class + " | " + gn.map_name.fillna(""),
    "weight": [0.5 if a else 0.2 for a in nau_g],
    "url": "https://edits.nationalmap.gov/apps/gaz-domestic/public/summary/" + gn.feature_id}, geometry=gn.geometry, crs=4326)
gnis["near_mrds_gold"] = nau_g

out = pd.concat([mrds.assign(near_mrds_gold=True), usmin, gnis], ignore_index=True)
out = gpd.GeoDataFrame(out, geometry="geometry", crs=4326)
out = out.cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
path = os.path.join(DATA, "gold_sources.geojson"); out.to_file(path, driver="GeoJSON")
with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
    csv.writer(f).writerow(["gold_sources (derived: MRDS AU + USMIN topo + GNIS)", "src/prep_sources.py", "gold_sources.geojson", len(out),
                            hashlib.sha256(open(path, "rb").read()).hexdigest()[:16], datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
print(out.groupby(["src_dataset", "kind"]).agg(n=("weight", "size"), w=("weight", "mean")))
print("bounds", out.total_bounds)
