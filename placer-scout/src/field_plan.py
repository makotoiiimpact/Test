"""Field plan for drone + foot surveys: launch point on a public road, walk distance/climb, wash flight line (200 m up, 150 m down
along the 10 m flow path), hazards and legal flags per stop. Writes out/field/field_plan.json + .kml."""
import os, sys, json, math, html
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points, transform
sys.path.insert(0, os.path.dirname(__file__)); import score
ROOT = os.path.join(os.path.dirname(__file__), ".."); DATA = os.path.join(ROOT, "data"); OUT = os.path.join(ROOT, "out", "field"); os.makedirs(OUT, exist_ok=True)
U = 26911
TOP_N = 8                 # owner: focus the field plan on the strong tier (scores >= ~0.15)
INCLUDE_CLIPS = False     # ant-mound scan stopped: 0 of 50 clips confirmed (stop rule: fewer than 5)
t = pd.read_csv(os.path.join(ROOT, "out", "targets.csv")); t = t[t["rank"] <= TOP_N]
clips = pd.DataFrame(json.load(open(os.path.join(ROOT, "out", "review", "clips.json"))))
stops = [dict(kind="target", key=f"T{r['rank']}", rank=int(r["rank"]), name=f"Target #{r['rank']}", district=r.district, lat=r.lat, lon=r.lon,
              score=r.score, trap=r.trap_type, land=r.land_status, boundary=r.boundary_risk if isinstance(r.boundary_risk, str) else "",
              near_excl=r.nearest_exclusion, near_excl_m=r.nearest_exclusion_m, src=r.top_source_name, src_m=r.top_source_dist_m, window=r.window) for _, r in t.iterrows()]
if INCLUDE_CLIPS: stops.append(dict(kind="clips", key="CLIPS", rank=0, name="Ant mound clip area (50 spots)", district="Eldorado Canyon/Nelson",
                  lat=float(clips.lat.mean()), lon=float(clips.lon.mean()), window="east"))
roads = gpd.read_file(os.path.join(DATA, "roads.geojson"))
roads = roads[~roads.MTFCC.isin(["S1740", "S1730", "S1710", "S1820", "S1830"])].to_crs(U)        # drop private roads, alleys, walkways, paths
ridx = roads.sindex
def lay(name):
    g = gpd.read_file(os.path.join(DATA, name)); g["geometry"] = g.geometry.make_valid(); return g.to_crs(U)
nps, priv, wild, act, blm, nca = lay("sma_NPS.geojson"), lay("sma_PrivateOrUnknown.geojson"), lay("wilderness_blm.geojson"), lay("claims_active.geojson"), lay("sma_BLM.geojson"), lay("nca_blm.geojson")
usp = gpd.read_file(os.path.join(DATA, "usmin_points.gml")); usp["geometry"] = usp.geometry.apply(lambda g: transform(lambda x, y, z=None: (y, x), g))
haz = usp[usp.ftr_type.isin(["Mine Shaft", "Adit"])].set_crs(4326, allow_override=True).to_crs(U)
dist = lambda g, p: float(g.distance(p).min()) if len(g) else float("inf")
inside = lambda g, p: bool(len(g) and g.contains(p).any())
T4 = lambda x, y: gpd.GeoSeries([Point(x, y)], crs=U).to_crs(4326).iloc[0]
dems = {w: rasterio.open(os.path.join(DATA, f"dem_{w}.tif")) for w in ("west", "east")}
def elev(w, lon, lat): return float(next(dems[w].sample([(lon, lat)]))[0])
cells = {w: score.window_cells(w) for w in ("west", "east")}
def flow_line(w, lon, lat):
    C = cells[w]; tr = C["tr"]; i0 = int((lat - tr.f) / tr.e) * C["W"] + int((lon - tr.c) / tr.a)
    def walk(nxt, max_m):
        out, d, c = [i0], 0.0, i0
        while d < max_m and nxt[c] >= 0:
            n = nxt[c]; d += C["step"][c if nxt is C["down"] else n]; c = n; out.append(c)
        return out
    up = walk(C["up"], 200)[::-1]; dn = walk(C["down"], 150)
    ll = lambda c: (tr.c + (c % C["W"] + 0.5) * tr.a, tr.f + (c // C["W"] + 0.5) * tr.e)
    pts = [ll(c) for c in up + dn[1:]]
    return pts[::max(1, len(pts) // 12)] + [pts[-1]]
rows = []
for s in stops:
    p = gpd.GeoSeries([Point(s["lon"], s["lat"])], crs=4326).to_crs(U).iloc[0]
    cand = roads.iloc[list(ridx.query(p.buffer(5000)))] if len(ridx.query(p.buffer(5000))) else roads
    best = None
    for _, rd in cand.iterrows():                                # nearest public road point that is not NPS/private/wilderness ground
        q = nearest_points(rd.geometry, p)[0]; d = q.distance(p)
        bad = inside(nps, q) or inside(priv, q) or inside(wild, q)
        key = (bad, d)
        if best is None or key < best[0]: best = (key, q, rd)
    (bad, dwalk), q, rd = best
    L = T4(q.x, q.y); w = s["window"]
    z0, z1 = elev(w, L.x, L.y), elev(w, s["lon"], s["lat"])
    line = LineString([q, p]); zs = [elev(w, *T4(*line.interpolate(f, normalized=True).coords[0]).coords[0]) for f in np.linspace(0, 1, 15)]
    steep = max(abs(zs[i + 1] - zs[i]) / (line.length / 14) for i in range(14)) if line.length > 60 else 0   # 10 m DEM is meaningless over shorter walks
    climb = sum(max(0, zs[i + 1] - zs[i]) for i in range(14))
    rating = "easy" if dwalk < 400 and climb < 30 and steep < 0.15 else ("hard" if dwalk > 1200 or climb > 100 or steep > 0.35 else "moderate")
    fl = flow_line(w, s["lon"], s["lat"])
    nshaft = int((haz.distance(p) <= 300).sum()); dshaft = dist(haz, p)
    rows.append({**s, "launch_lat": round(L.y, 6), "launch_lon": round(L.x, 6), "launch_road": (rd.FULLNAME if isinstance(rd.FULLNAME, str) and rd.FULLNAME else "unnamed road"),
                 "launch_road_type": {"S1100": "primary highway", "S1200": "highway", "S1400": "local road", "S1500": "4WD / dirt track", "S1640": "service road"}.get(rd.MTFCC, rd.MTFCC),
                 "launch_ok": not bad, "walk_m": round(dwalk), "climb_m": round(climb), "steepest_pct": round(steep * 100), "walk_rating": rating,
                 "elev_launch_m": round(z0), "elev_target_m": round(z1),
                 "flight_line": [[round(a, 6), round(b, 6)] for a, b in fl], "video_start": [round(fl[0][1], 6), round(fl[0][0], 6)], "video_end": [round(fl[-1][1], 6), round(fl[-1][0], 6)],
                 "shafts_adits_300m": nshaft, "nearest_shaft_m": round(dshaft), "nps_m": round(dist(nps, p)), "wilderness_m": round(dist(wild, p)),
                 "monument_m": round(dist(nca, p)), "active_claim_m": round(dist(act, p)), "private_m": round(dist(priv, p)),
                 "on_blm": inside(blm, p)})
R = pd.DataFrame(rows)
# trip order: per district, start at the stop closest to a highway, then nearest-neighbour
hw = roads[roads.MTFCC.isin(["S1100", "S1200"])]
R["trip"] = R.district.map({"Eldorado Canyon/Nelson": "A · Nelson / Eldorado", "Searchlight": "B · Searchlight", "Goodsprings": "C · Goodsprings", "other": "D · Other"}).fillna("D · Other")
order = []
for trip, g in R.groupby("trip"):
    pts = {i: gpd.GeoSeries([Point(r.lon, r.lat)], crs=4326).to_crs(U).iloc[0] for i, r in g.iterrows()}
    cur = min(pts, key=lambda i: hw.distance(pts[i]).min()); seq = [cur]
    while len(seq) < len(pts):
        cur = min((i for i in pts if i not in seq), key=lambda i: pts[i].distance(pts[seq[-1]])); seq.append(cur)
    order += [(i, n + 1) for n, i in enumerate(seq)]
for i, n in order: R.loc[i, "stop_no"] = n
R = R.sort_values(["trip", "stop_no"])
R.to_json(os.path.join(OUT, "field_plan.json"), orient="records", indent=1)
pm = []
for r in R.itertuples():
    pm.append(f"<Placemark><name>{html.escape(r.trip[0] + str(int(r.stop_no)) + ' launch: ' + r.name)}</name><Point><coordinates>{r.launch_lon},{r.launch_lat},0</coordinates></Point></Placemark>")
    pm.append(f"<Placemark><name>{html.escape(r.trip[0] + str(int(r.stop_no)) + ' ' + r.name)}</name><Point><coordinates>{r.lon:.6f},{r.lat:.6f},0</coordinates></Point></Placemark>")
    pm.append(f"<Placemark><name>{html.escape(r.name + ' wash video line (upstream to downstream)')}</name><Style><LineStyle><color>ff0080ff</color><width>3</width></LineStyle></Style><LineString><tessellate>1</tessellate><coordinates>{' '.join(f'{a},{b},0' for a, b in r.flight_line)}</coordinates></LineString></Placemark>")
open(os.path.join(OUT, "field_plan.kml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>placer-scout field plan</name>{"".join(pm)}</Document></kml>')
pd.set_option("display.width", 250)
print(R[["trip", "stop_no", "name", "launch_road", "launch_road_type", "launch_ok", "walk_m", "climb_m", "steepest_pct", "walk_rating", "shafts_adits_300m", "nearest_shaft_m", "nps_m", "wilderness_m", "active_claim_m", "private_m"]].to_string())
