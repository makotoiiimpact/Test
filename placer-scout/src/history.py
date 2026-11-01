"""Step 1.9: historical placer-record factor (f_hist) from two old government reports, then re-score.
  - USGS Bulletin 1356 (Johnson 1973, Placer gold deposits of Nevada), Clark County p. 6-10 and table 1
  - USBM Information Circular 6964 (Vanderburg 1937), Eldorado Empire Mining Co. / C. E. L. Gresh
  f_hist = 1.0  inside T26S R64E Sec 4 (the 'Gresh Group' placer claims named in Bulletin 1356)
         = 0.9  rest of Eldorado Canyon district (about 470 oz placer gold estimated; placers in the canyon gravels)
         = 0.75 Searchlight (placer gold recorded, but mostly east of the lode area)
         = 0.6  Goodsprings, Crescent and other (no recorded placer production)
A gentle multiplier, not a gate: no record is not proof of no gold. Notes: out/notes/usgs_b1356_placers.md"""
import os, requests, numpy as np, pandas as pd, geopandas as gpd
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SEC = os.path.join(DATA, "history_gresh_T26S_R64E_sec04.geojson")
if not os.path.exists(SEC):
    url = "https://gis.blm.gov/arcgis/rest/services/Cadastral/BLM_Natl_PLSS_CadNSDI/MapServer/3/query"
    g = gpd.read_file(requests.get(url, params={"where": "TWNSHPLAB='26S 64E' AND FRSTDIVLAB='04' AND PRINMER='Mount Diablo Meridian'",
        "outFields": "TWNSHPLAB,FRSTDIVLAB", "returnGeometry": "true", "outSR": 4326, "f": "geojson"}, timeout=120).text)
    if not len(g):   # fall back to an envelope query near Nelson
        g = gpd.read_file(requests.get(url, params={"geometry": "-114.86,35.69,-114.80,35.73", "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "outFields": "TWNSHPLAB,FRSTDIVLAB", "returnGeometry": "true", "outSR": 4326, "f": "geojson"}, timeout=120).text)
        g = g[(g.TWNSHPLAB == "26S 64E") & (g.FRSTDIVLAB.astype(str).str.zfill(2) == "04")]
    g = g.dissolve().set_crs(4326, allow_override=True); g.to_file(SEC, driver="GeoJSON")
sec = gpd.read_file(SEC)
p = os.path.join(DATA, "scored_cells.csv.gz")
df = pd.read_csv(p, low_memory=False, dtype={"top_source_id": str, "noaa_flood_event_id": str})
base = {"Eldorado Canyon/Nelson": (0.9, "Eldorado Canyon placer district (USGS Bull. 1356, p. 6-7)"),
        "Searchlight": (0.75, "Searchlight placers recorded, mostly east of the lode area (USGS Bull. 1356, p. 9-10)")}
df["f_hist"] = [base.get(d, (0.6, ""))[0] for d in df.district]
df["hist_basis"] = [base.get(d, (0.6, "No recorded placer production in USGS Bull. 1356"))[1] for d in df.district]
pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
inside = pts.within(sec.geometry.iloc[0]).values
df.loc[inside, "f_hist"] = 1.0
df.loc[inside, "hist_basis"] = "Inside T26S R64E Sec 4, the Gresh placer claims (USGS Bull. 1356, p. 7; USBM IC 6964)"
# 1942 shutdown (WPB Order L-208): +0.1 when the strongest upstream gold source is within 300 m of a strong/medium L-208 candidate
L208 = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "out", "l208_mines.csv")).dropna(subset=["lat"])
L208 = L208[L208.l208_class.str.contains(r"L-208 candidate \((strong|medium)\)", regex=True)]
srcs = gpd.read_file(os.path.join(DATA, "gold_sources.geojson"))[["src_id", "geometry"]].drop_duplicates("src_id").to_crs(26911)
lg = gpd.GeoDataFrame(L208[["name"]], geometry=gpd.points_from_xy(L208.lon, L208.lat), crs=4326).to_crs(26911)
js = gpd.sjoin_nearest(srcs, lg, how="left", max_distance=300, distance_col="d"); js = js[~js.index.duplicated()]
l208_src = dict(zip(js.src_id.astype(str), js.name))
df["l208_upstream"] = df.top_source_id.astype(str).map(l208_src)
hit = df.l208_upstream.notna()
df.loc[hit, "f_hist"] = np.minimum(1.0, df.loc[hit, "f_hist"] + 0.1)
df.loc[hit, "hist_basis"] = df.loc[hit, "hist_basis"] + "; + 1942 shutdown mine upstream (" + df.loc[hit, "l208_upstream"] + ", out/l208_mines.csv)"
print("L-208 boosted cells:", int(hit.sum()), df.loc[hit, "l208_upstream"].value_counts().to_dict())
df["score"] = df.f_source * df.f_flood * df.f_trap * df.f_hist
df.to_csv(p, index=False)
print("f_hist counts:", df.f_hist.value_counts().to_dict(), "| cells in Gresh section:", int(inside.sum()), "legal:", int((inside & df.legal_ok).sum()))
