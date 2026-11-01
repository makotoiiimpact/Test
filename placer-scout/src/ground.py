"""Step 1.95: drop wash cells on ground the 1950s-map review showed to be poor targets (out/oldmap_review.csv):
  - townsite:  inside a Census town (TIGER 2025 places) AND >= 500 m of named streets within 300 m
  - quarry/pit: within 150 m of a USMIN topo quarry, gravel/borrow/sand/clay pit or open-pit point, or 100 m of such a polygon
  - pipeline:  within 150 m of a mapped natural-gas pipeline (EIA/HIFLD, via FEMA Region 9 copy; positions approximate).
               Never dig over a buried pipeline.
  - power line: within 60 m of a mapped electric transmission line (HIFLD)
Writes ground_ok / ground_reason into data/scored_cells.csv.gz. 'Open slope' (no real channel) is not tested here."""
import os, io, zipfile, csv, datetime, requests, numpy as np, pandas as pd, geopandas as gpd
DATA = os.path.join(os.path.dirname(__file__), "..", "data"); B = "-115.9,35.1,-114.4,36.25"
LAYERS = {"pipelines_gas": "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Natural_Gas_Interstate_and_Intrastate_Pipelines_1/FeatureServer/0",
          "powerlines": "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Electric_Power_Transmission_Lines/FeatureServer/0"}
def layer(name, url):
    p = os.path.join(DATA, f"{name}.geojson")
    if not os.path.exists(p):
        r = requests.get(url + "/query", params={"where": "1=1", "geometry": B, "geometryType": "esriGeometryEnvelope", "inSR": 4326, "outSR": 4326,
                                                 "outFields": "*", "f": "geojson"}, timeout=180); r.raise_for_status(); open(p, "w").write(r.text)
        with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
            csv.writer(f).writerow([name, url, f"{name}.geojson", len(gpd.read_file(p)), "", datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
    return gpd.read_file(p).to_crs(26911)
pipes, power = (layer(k, v) for k, v in LAYERS.items())
place_p = os.path.join(DATA, "tiger_place", "tl_2025_32_place.shp")
if not os.path.exists(place_p):
    z = requests.get("https://www2.census.gov/geo/tiger/TIGER2025/PLACE/tl_2025_32_place.zip", timeout=180).content
    zipfile.ZipFile(io.BytesIO(z)).extractall(os.path.join(DATA, "tiger_place"))
places = gpd.read_file(place_p).to_crs(26911)
roads = gpd.read_file(os.path.join(DATA, "roads.geojson")).to_crs(26911)
streets = roads[roads.MTFCC.isin(["S1400", "S1640", "S1730", "S1740"]) & roads.FULLNAME.notna()]
PIT = ["Quarry", "Quarry - Rock", "Open Pit Mine", "Open Pit Mine or Quarry", "Gravel Pit", "Borrow Pit", "Gravel/Borrow Pit - Undifferentiated",
       "Sand Pit", "Clay Pit", "Disturbed Surface"]
def usmin(f):
    g = gpd.read_file(os.path.join(DATA, f)); g["geometry"] = g.geometry.apply(lambda s: __import__("shapely").ops.transform(lambda x, y, z=None: (y, x), s))
    return g.set_crs(4326, allow_override=True)[lambda d: d.ftr_type.isin(PIT)].to_crs(26911)
pit_pt, pit_pg = usmin("usmin_points.gml"), usmin("usmin_polygons.gml")
p = os.path.join(DATA, "scored_cells.csv.gz")
df = pd.read_csv(p, low_memory=False, dtype={"top_source_id": str, "noaa_flood_event_id": str})
P = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326).to_crs(26911)
def near(g, m):
    if not len(g): return np.zeros(len(P), bool)
    j = gpd.sjoin_nearest(P, g[["geometry"]], how="left", max_distance=m, distance_col="d"); j = j[~j.index.duplicated()]
    return j.d.reindex(P.index).notna().values
in_town = gpd.sjoin(P, places[["geometry"]], how="left", predicate="within"); in_town = in_town[~in_town.index.duplicated()].index_right.notna().values
street_m = np.zeros(len(P))
cand = np.flatnonzero(in_town)
if len(cand):
    sidx = streets.sindex
    for i in cand:
        b = P.geometry.iat[i].buffer(300); hits = streets.iloc[sidx.query(b)]
        street_m[i] = hits.intersection(b).length.sum()
rules = [("townsite", in_town & (street_m >= 500)), ("quarry or pit", near(pit_pt, 150) | near(pit_pg, 100)),
         ("pipeline corridor", near(pipes, 150)), ("power line corridor", near(power, 60))]
reason = np.array([""] * len(df), dtype=object)
for name, m in rules: reason[m & (reason == "")] = name
df["ground_reason"] = reason; df["ground_ok"] = reason == ""
df.to_csv(p, index=False)
print({n: int(m.sum()) for n, m in rules}, "| legal cells removed:", int((~df.ground_ok & df.legal_ok).sum()), "of", int(df.legal_ok.sum()))
