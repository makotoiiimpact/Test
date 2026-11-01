"""Step 3b: out/map.html - local Leaflet map (folium) with toggleable layers. Basemaps are keyless USGS / OSM tiles."""
import os, json, base64, io, html
import numpy as np, pandas as pd, geopandas as gpd, rasterio, folium
from folium.plugins import MarkerCluster
from matplotlib import cm, colors
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

DATA = os.path.join(os.path.dirname(__file__), "..", "data"); OUT = os.path.join(os.path.dirname(__file__), "..", "out")
t = pd.read_csv(os.path.join(OUT, "targets.csv"), dtype=str)
cand = pd.read_csv(os.path.join(DATA, "candidates_top600.csv"))
m = folium.Map(location=[35.65, -115.1], zoom_start=10, tiles=None, control_scale=True)
# USGS basemaps only: they load from a downloaded file. OpenStreetMap's servers refuse file:// pages (no Referer) with "Access blocked".
USGS = "https://basemap.nationalmap.gov/arcgis/rest/services/{}/MapServer/tile/{{z}}/{{y}}/{{x}}"
for svc, name, on in (("USGSTopo", "USGS Topo", True), ("USGSImageryTopo", "USGS Imagery + Topo", False), ("USGSImageryOnly", "USGS Imagery", False)):
    folium.TileLayer(USGS.format(svc), attr="USGS The National Map", name=name, max_zoom=16, show=on).add_to(m)

from shapely.ops import unary_union
def polys_only(geom):
    """make_valid/clip can return GeometryCollections, which crash Leaflet's tooltip code; keep only polygon parts"""
    if geom is None or geom.is_empty: return None
    if geom.geom_type in ("Polygon", "MultiPolygon"): return geom
    parts = [p for p in getattr(geom, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")]
    return unary_union(parts) if parts else None

def simp(path, tol=0.0003, clip=None, cols=()):
    g = gpd.read_file(os.path.join(DATA, path))
    g["geometry"] = g.geometry.make_valid()
    if clip is not None: g = g.clip(clip)
    g["geometry"] = g.geometry.simplify(tol).apply(polys_only)
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    return g[[c for c in cols if c in g.columns] + ["geometry"]]
area = gpd.GeoSeries.from_xy(cand.lon, cand.lat, crs=4326).to_crs(26911).buffer(6000).union_all()
area = gpd.GeoSeries([area], crs=26911).to_crs(4326).iloc[0]
box = (-115.7, 35.0, -114.5, 36.1)

# --- excluded / special land ---
fg = folium.FeatureGroup(name="Excluded land (NPS, USFS, private, state, other)", show=True)
for n, col in (("NPS", "#7b3294"), ("USFS", "#1b7837"), ("PrivateOrUnknown", "#d6604d"), ("State", "#4393c3"), ("Local", "#4393c3"),
               ("OtherFederal", "#878787"), ("USBR", "#878787"), ("BIA", "#b35806"), ("DOD", "#000000"), ("USFWS", "#5aae61")):
    g = simp(f"sma_{n}.geojson", clip=box, cols=["ADMIN_UNIT_NAME"])
    if len(g): folium.GeoJson(g, style_function=lambda f, c=col: {"color": c, "weight": 1, "fillColor": c, "fillOpacity": 0.25},
                              tooltip=folium.GeoJsonTooltip(["ADMIN_UNIT_NAME"], aliases=[n])).add_to(fg)
fg.add_to(m)
fg = folium.FeatureGroup(name="BLM wilderness / monuments / NCAs (excluded)", show=True)
folium.GeoJson(simp("wilderness_blm.geojson", clip=box, cols=["NLCS_NAME"]), style_function=lambda f: {"color": "#006837", "weight": 2, "fillOpacity": 0.2, "dashArray": "4"},
               tooltip=folium.GeoJsonTooltip(["NLCS_NAME"], aliases=["Wilderness"])).add_to(fg)
folium.GeoJson(simp("nca_blm.geojson", clip=box, cols=["NCA_NAME"]), style_function=lambda f: {"color": "#a50026", "weight": 2, "fillOpacity": 0.12, "dashArray": "8"},
               tooltip=folium.GeoJsonTooltip(["NCA_NAME"], aliases=["Monument/NCA"])).add_to(fg)
fg.add_to(m)
fg = folium.FeatureGroup(name="ACEC (flag only: extra rules, e.g. desert tortoise)", show=False)
folium.GeoJson(simp("acec_blm.geojson", clip=box, cols=["ACEC_NAME"]), style_function=lambda f: {"color": "#fdae61", "weight": 1, "fillOpacity": 0.1},
               tooltip=folium.GeoJsonTooltip(["ACEC_NAME"], aliases=["ACEC"])).add_to(fg)
fg.add_to(m)
# --- claims ---
fg = folium.FeatureGroup(name="Active mining claims (BLM MLRS)", show=True)
folium.GeoJson(simp("claims_active.geojson", 0.0001, clip=area, cols=["CSE_NR", "CSE_NAME", "BLM_PROD", "CSE_DISP"]),
               style_function=lambda f: {"color": "#e41a1c", "weight": 1, "fillOpacity": 0.15},
               tooltip=folium.GeoJsonTooltip(["CSE_NR", "CSE_NAME", "BLM_PROD", "CSE_DISP"])).add_to(fg)
fg.add_to(m)
fg = folium.FeatureGroup(name="Closed mining claims near candidates", show=False)
folium.GeoJson(simp("claims_closed.geojson", 0.0001, clip=area, cols=["CSE_NR", "CSE_NAME", "BLM_PROD"]),
               style_function=lambda f: {"color": "#999999", "weight": 0.5, "fillOpacity": 0.05},
               tooltip=folium.GeoJsonTooltip(["CSE_NR", "CSE_NAME", "BLM_PROD"])).add_to(fg)
fg.add_to(m)
# --- gold sources ---
src = gpd.read_file(os.path.join(DATA, "gold_sources.geojson"))
fg = folium.FeatureGroup(name="Gold sources: MRDS gold records + tailings/mills", show=True)
for _, r in src[(src.src_dataset == "MRDS") | (src.kind != "mine/deposit")].iterrows():
    c = {"mill/plant": "#ff7f00", "tailings/dump": "#a65628"}.get(r.kind, "#ffd700")
    folium.CircleMarker([r.geometry.y, r.geometry.x], radius=4, color="#333", weight=1, fill=True, fill_color=c, fill_opacity=0.9,
                        tooltip=html.escape(f"{r['name']} [{r.src_dataset} {r.src_id}] {r.detail}")).add_to(fg)
fg.add_to(m)
fg = folium.FeatureGroup(name="Old shafts/adits/pits near gold records (USMIN topo)", show=False)
for _, r in src[(src.src_dataset == "USMIN_topo") & src.near_mrds_gold.astype(bool) & (src.kind == "mine/deposit")].iterrows():
    folium.CircleMarker([r.geometry.y, r.geometry.x], radius=2, color="#555", weight=0, fill=True, fill_opacity=0.8, tooltip=html.escape(str(r.detail))).add_to(fg)
fg.add_to(m)
# --- washes near candidates ---
fg = folium.FeatureGroup(name="Washes (drainage >= 0.25 km2) near candidates", show=False)
for w in ("west", "east"):
    s = gpd.read_file(os.path.join(DATA, f"streams_{w}.geojson")).set_crs(4326, allow_override=True)
    s = s[s.intersects(area)]; s["geometry"] = s.geometry.simplify(0.0001)
    folium.GeoJson(s[["geometry"]], style_function=lambda f: {"color": "#2171b5", "weight": 1}).add_to(fg)
fg.add_to(m)
# --- rain ---
with rasterio.open(os.path.join(DATA, "mrms_max24h_mm.tif")) as s:
    a = s.read(1); b = s.bounds
norm = colors.Normalize(0, 100); rgba = (cm.viridis(norm(a)) * 255).astype(np.uint8); rgba[..., 3] = np.where(a > 5, 150, 0)
buf = io.BytesIO(); plt.imsave(buf, rgba, format="png")
folium.raster_layers.ImageOverlay("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), bounds=[[b.bottom, b.left], [b.top, b.right]],
                                  name="Biggest 24 h radar rain on 218 storm days 2021-2026 (MRMS, 0-100 mm)", show=False).add_to(m)
fg = folium.FeatureGroup(name="NOAA flood reports (2000-2026) + RFCD rain gauges", show=False)
ev = pd.read_csv(os.path.join(DATA, "storm_events.csv"), dtype=str).dropna(subset=["BEGIN_LAT"])
for _, r in ev.iterrows():
    folium.CircleMarker([float(r.BEGIN_LAT), float(r.BEGIN_LON)], radius=4, color="#08519c", fill=True, fill_opacity=0.7,
                        tooltip=html.escape(f"{r.EVENT_TYPE} {r.BEGIN_DATE_TIME} (NOAA event {r.EVENT_ID})")).add_to(fg)
g = pd.read_csv(os.path.join(DATA, "rain_gauges_summary.csv"))
for _, r in g[g.max_day_in <= 5].iterrows():
    folium.RegularPolygonMarker([r.lat, r.lon], number_of_sides=3, radius=6, color="#00441b", fill=True,
                                tooltip=html.escape(f"RFCD gauge {r['name']}: max day {r.max_day_in:.2f} in on {r.max_day_date}")).add_to(fg)
fg.add_to(m)
# --- candidates + targets ---
fg = folium.FeatureGroup(name="Top 600 scored wash spots (legal only)", show=False)
cmap = cm.YlOrRd
for _, r in cand.iterrows():
    folium.CircleMarker([r.lat, r.lon], radius=3, weight=0, fill=True, fill_opacity=0.8, fill_color=colors.to_hex(cmap(min(1, r.score / cand.score.max()))),
                        tooltip=f"score {r.score:.3f} = source {r.f_source:.2f} x flood {r.f_flood:.2f} x trap {r.f_trap:.2f} x history {r.f_hist:.2f}").add_to(fg)
fg.add_to(m)
fg = folium.FeatureGroup(name="TOP 25 TARGETS", show=True)
for _, r in t.iterrows():
    pop = f"""<b>#{r['rank']} — {html.escape(r.district)}</b><br>{r.lat}, {r.lon}<br>
<b>Score {float(r.score):.3f}</b> = gold source {float(r.f_source):.2f} × flood {float(r.f_flood):.2f} × trap {float(r.f_trap):.2f} × placer history {float(r.f_hist):.2f}<br>
Source: {html.escape(str(r.top_source_name))} ({html.escape(str(r.top_source_dataset))} {html.escape(str(r.top_source_id))}), {float(r.top_source_dist_m):.0f} m upstream<br>
Trap: {html.escape(r.trap_type)} · Storm: {float(r.storm_max_24h_mm):.0f} mm in 24 h ({html.escape(r.rain_basis)})<br>
Land: {html.escape(r.land_status)} {('· ACEC: ' + html.escape(r.acec_flag)) if isinstance(r.acec_flag, str) and r.acec_flag != 'nan' else ''}<br>
Road: {html.escape(r.nearest_road)}, {float(r.nearest_road_m):.0f} m · {html.escape(r.plss)}<br>
<a href="{html.escape(r.mlrs_active_claims_check)}" target="_blank" rel="noopener noreferrer">Re-check active claims here (BLM)</a> ·
<a href="{r.mlrs_research_map}" target="_blank" rel="noopener noreferrer">MLRS research map</a>"""
    folium.Marker([float(r.lat), float(r.lon)], popup=folium.Popup(pop, max_width=380), tooltip=f"#{r['rank']} score {float(r.score):.3f}",
                  icon=folium.DivIcon(html=f'<div style="background:#d7301f;color:#fff;border:2px solid #fff;border-radius:50%;width:24px;height:24px;line-height:20px;text-align:center;font:bold 11px sans-serif">{r["rank"]}</div>')).add_to(fg)
fg.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)
m.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:8px;left:8px;z-index:9999;background:#fff;padding:6px 8px;font:12px sans-serif;border:1px solid #999;max-width:420px">placer-scout: rough prioritisation, not a gold prediction and not legal land status. Re-check claims and land status before any visit. Never enter mine workings; stay out of washes when storms are possible.</div>'))
m.save(os.path.join(OUT, "map.html"))
print("map.html MB", round(os.path.getsize(os.path.join(OUT, "map.html")) / 1e6, 1))
