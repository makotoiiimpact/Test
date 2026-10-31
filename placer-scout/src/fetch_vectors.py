"""Step 1.1-1.3: claims, land status, MRDS mines. Logs each pull to data/PROVENANCE.csv."""
import sys, os, json, csv, hashlib, datetime, requests
sys.path.insert(0, os.path.dirname(__file__))
from arcgis import query

BOX = (-115.7, 35.0, -114.5, 36.1)          # admin/mining layers box (see plan)
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
CLAIMS = "https://nlsdbpubgis.blm.gov/arcgis/rest/services/Mining_Claims/MiningClaims/MapServer"
SMA = "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer"
SMA_LAYERS = {22: "BLM", 23: "NPS", 24: "USFS", 25: "USFWS", 26: "USBR", 27: "BIA", 28: "OtherFederal",
              29: "State", 30: "Local", 31: "PrivateOrUnknown", 21: "DOD"}

def log(layer, url, path, n):
    p = os.path.join(DATA, "PROVENANCE.csv")
    new = not os.path.exists(p)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    with open(p, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["layer", "url", "file", "rows", "sha256_16", "pulled_utc"])
        w.writerow([layer, url, os.path.basename(path), n, h, datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])

def save(fc, name, layer, url):
    path = os.path.join(DATA, name)
    json.dump(fc, open(path, "w"))
    log(layer, url, path, len(fc["features"]))
    print(name, len(fc["features"]), flush=True)

what = sys.argv[1:] or ["claims", "sma", "mrds", "wild", "roads", "nca"]
if "claims" in what:
    keep = "ADMIN_STATE,BLM_PROD,CSE_DISP,CSE_TYPE_NR,CSE_NR,CSE_NAME,LOC_DT,RCRD_ACRS,MC_PATENTED,MC_EXCLUDED,MC_CONVEYED,OBJECTID"
    for lid, nm in ((1, "claims_active"), (2, "claims_closed")):
        fc = query(f"{CLAIMS}/{lid}", BOX, out_fields=keep, extra={"geometryPrecision": 5})
        save(fc, nm + ".geojson", nm, f"{CLAIMS}/{lid}")
if "sma" in what:
    for lid, nm in SMA_LAYERS.items():
        try:
            fc = query(f"{SMA}/{lid}", BOX, out_fields="SMA_ID,ADMIN_AGENCY_CODE,ADMIN_UNIT_NAME,ADMIN_UNIT_TYPE,ADMIN_ST", extra={"geometryPrecision": 5})
        except Exception as e:
            print("SMA", nm, "FAILED", e); continue
        for f in fc["features"]: f["properties"]["sma_class"] = nm
        save(fc, f"sma_{nm}.geojson", f"sma_{nm}", f"{SMA}/{lid}")
if "mrds" in what:
    url = "https://mrdata.usgs.gov/services/wfs/mrds"
    r = requests.get(url, params={"service": "WFS", "version": "1.1.0", "request": "GetFeature", "typeName": "mrds",
                                  "bbox": "%s,%s,%s,%s,EPSG:4326" % BOX}, timeout=300)
    path = os.path.join(DATA, "mrds_box.gml"); open(path, "wb").write(r.content)
    print("mrds http", r.status_code, len(r.content), flush=True)
    log("mrds", url, path, -1)
if "wild" in what:
    W = "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer"
    for lid, nm in ((0, "wilderness_blm"), (1, "wsa_blm")):
        fc = query(f"{W}/{lid}", BOX, extra={"geometryPrecision": 5})
        save(fc, nm + ".geojson", nm, f"{W}/{lid}")
if "roads" in what:
    import zipfile, io
    import geopandas as gpd
    parts = []
    for c in ("32003", "06071"):
        url = f"https://www2.census.gov/geo/tiger/TIGER2025/ROADS/tl_2025_{c}_roads.zip"
        r = requests.get(url, timeout=600); d = os.path.join(DATA, "tiger"); os.makedirs(d, exist_ok=True)
        zipfile.ZipFile(io.BytesIO(r.content)).extractall(d)
        g = gpd.read_file(os.path.join(d, f"tl_2025_{c}_roads.shp")).to_crs(4326).cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
        g["src_url"] = url; parts.append(g)
    g = gpd.GeoDataFrame(__import__("pandas").concat(parts), crs=4326)
    path = os.path.join(DATA, "roads.geojson"); g[["LINEARID", "FULLNAME", "MTFCC", "src_url", "geometry"]].to_file(path, driver="GeoJSON")
    log("roads (TIGER 2025)", "https://www2.census.gov/geo/tiger/TIGER2025/ROADS/", path, len(g)); print("roads", len(g))
if "nca" in what:
    for url, nm in (("https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_NM_NCA_poly/MapServer/0", "nca_blm"),
                    ("https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_ACEC/MapServer/0", "acec_blm")):
        fc = query(url, BOX, extra={"geometryPrecision": 5}); save(fc, nm + ".geojson", nm, url)
