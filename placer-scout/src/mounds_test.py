"""Phase 2 Step B1-B4: NAIP clearing detector on ONE test area, plus 50 review clips. Mounds are field-check spots, not a score input.
NAIP 2022 and 2019 (0.6 m) original COGs from Planetary Computer (anonymous SAS token, no account). The USGS NAIPPlus
ImageServer also serves 2022 keylessly but recompresses it."""
import os, io, json, base64, math, csv, hashlib, datetime, requests
import numpy as np, rasterio, geopandas as gpd, pandas as pd
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
from pyproj import Transformer
from scipy.ndimage import gaussian_filter, uniform_filter
from skimage.feature import blob_log
from skimage.registration import phase_cross_correlation
from scipy.ndimage import shift as nd_shift
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), ".."); DATA = os.path.join(ROOT, "data"); NAIP = os.path.join(DATA, "naip"); OUT = os.path.join(ROOT, "out", "review")
LON, LAT, HALF = -114.866, 35.690, 800              # test area: Nelson / Eldorado Canyon, below Rand & Quaker City mines (1.6 km square, open desert)
RES = 0.6
T = Transformer.from_crs(4326, 26911, always_xy=True); Ti = Transformer.from_crs(26911, 4326, always_xy=True)
cx, cy = T.transform(LON, LAT); B = (cx - HALF, cy - HALF, cx + HALF, cy + HALF); N = int(2 * HALF / RES)
dst_tr = rasterio.transform.from_origin(B[0], B[3], RES, RES)

def naip2022():                                         # original 2022 COGs (the USGS mosaic service is visibly recompressed)
    return naip_year(2022)

def naip2019():
    return naip_year(2019)

def naip_year(year):
    p = os.path.join(NAIP, f"test_{year}.tif")
    if not os.path.exists(p):
        q = {"collections": ["naip"], "intersects": {"type": "Point", "coordinates": [LON, LAT]}, "query": {"naip:year": {"eq": str(year)}}, "limit": 10}
        fs = requests.post("https://planetarycomputer.microsoft.com/api/stac/v1/search", json=q, timeout=120).json()["features"]
        tok = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/token/naip", timeout=60).json()["token"]
        out = np.zeros((4, N, N), "float32")
        for f in fs:                                          # mosaic every 2019 quarter-quad touching the box
            with rasterio.open(f["assets"]["image"]["href"] + "?" + tok) as s:
                tmp = np.zeros((4, N, N), "float32")
                reproject(rasterio.band(s, [1, 2, 3, 4]), tmp, dst_transform=dst_tr, dst_crs="EPSG:26911", resampling=Resampling.nearest)
                out = np.where(out.sum(0) == 0, tmp, out)
        with rasterio.open(p, "w", driver="GTiff", height=N, width=N, count=4, dtype="float32", crs="EPSG:26911", transform=dst_tr, compress="deflate") as o: o.write(out)
        json.dump([f["id"] for f in fs], open(os.path.join(NAIP, f"test_{year}_items.json"), "w"))
    with rasterio.open(p) as s: return s.read().astype("float32")

def blobs(img):
    r, g, b, nir = img
    bright = (r + g + b) / 3; ndvi = (nir - r) / (nir + r + 1e-6)
    bd = bright - gaussian_filter(bright, 8)                           # local contrast vs ~5 m surroundings
    z = np.clip(bd / (np.std(bd) + 1e-6), 0, None); z = np.clip(z / np.percentile(z, 99.9), 0, 1)   # robust, same for both years
    bl = blob_log(z, min_sigma=1.2, max_sigma=2.6, num_sigma=8, threshold=0.15)
    return bl, bright, bd, ndvi

a22 = naip2022(); a19 = naip2019()
# co-register 2019 to 2022 (NAIP orthos are often offset by a few metres between years)
g22 = a22[:3].mean(0); g19 = a19[:3].mean(0)
off, err, _ = phase_cross_correlation(g22, g19, upsample_factor=4)
a19 = np.stack([nd_shift(b, off, order=1) for b in a19]); print("2019 -> 2022 shift (px)", off, "err", round(float(err), 3))
# legal/natural mask: BLM land only (towns, patented claims, NPS etc. drop out)
blm = gpd.read_file(os.path.join(DATA, "sma_BLM.geojson")); blm["geometry"] = blm.geometry.make_valid(); blm = blm.to_crs(26911)
from rasterio.features import geometry_mask
box_poly = gpd.GeoSeries.from_xy([B[0], B[2]], [B[1], B[3]], crs=26911).total_bounds
from shapely.geometry import box as sbox
blm_in = blm.clip(sbox(*B))
mask_blm = ~geometry_mask(list(blm_in.geometry), out_shape=(N, N), transform=dst_tr) if len(blm_in) else np.zeros((N, N), bool)
print("BLM share of test area", round(mask_blm.mean(), 3))
bl, bright, bd, ndvi = blobs(a22); bl19, _, bd19, _ = blobs(a19)
print("2022 raw blobs", len(bl), "| 2019 raw blobs", len(bl19))
yy, xx = np.indices((15, 15)) - 7; rr = np.hypot(yy, xx)
rows = []
for (y, x, s) in bl:
    y, x = int(y), int(x); rad = s * math.sqrt(2)                      # blob radius in px
    if y < 10 or x < 10 or y >= N - 10 or x >= N - 10 or not mask_blm[y, x]: continue
    if bright[y - 1:y + 2, x - 1:x + 2].mean() > 200: continue          # white roofs / vehicles / trash, not sandy clearings
    win_bd = bd[y - 7:y + 8, x - 7:x + 8]; win_nd = ndvi[y - 7:y + 8, x - 7:x + 8]
    core = rr <= max(1.5, rad); ring = (rr > rad + 1) & (rr <= rad + 4)
    contrast = float(win_bd[core].mean() - win_bd[ring].mean())
    ndvi_core, ndvi_ring = float(win_nd[core].mean()), float(win_nd[ring].mean())
    # roundness: thresholded bright patch around centre, compare its second moments
    patch = win_bd > (win_bd[core].mean() + win_bd[ring].mean()) / 2
    from skimage.measure import label, regionprops
    lab = label(patch); c = lab[7, 7]
    if c == 0: continue
    rp = [p for p in regionprops(lab) if p.label == c][0]
    ecc = rp.eccentricity; area_m2 = rp.area * RES * RES; diam = 2 * math.sqrt(area_m2 / math.pi)
    # persistence: best 2019 local contrast within 1.2 m of the same spot (after co-registration)
    best19 = -1e9; k = 2                                                 # after co-registration, allow +-2 px (1.2 m)
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            yy2, xx2 = y + dy, x + dx
            if 7 <= yy2 < N - 8 and 7 <= xx2 < N - 8:
                w19 = bd19[yy2 - 7:yy2 + 8, xx2 - 7:xx2 + 8]; best19 = max(best19, float(w19[core].mean() - w19[ring].mean()))
    d19 = best19
    rows.append(dict(px=x, py=y, diam_m=diam, ecc=ecc, contrast=contrast, ndvi_core=ndvi_core, ndvi_ring=ndvi_ring, contrast2019=d19))
D = pd.DataFrame(rows)
print("candidates after shape pass", len(D))
D = D[(D.diam_m.between(1.5, 4.5)) & (D.ecc < 0.85) & (D.contrast > 0)]
# score: contrast (z), shrub ring greener than core, roundness, persistence in 2019
zc = (D.contrast - D.contrast.mean()) / D.contrast.std()
D["score"] = (1 / (1 + np.exp(-zc))) * 0.45 + np.clip((D.ndvi_ring - D.ndvi_core) * 20, 0, 1) * 0.2 + (1 - D.ecc) * 0.15 + (D.contrast2019 >= 0.5 * D.contrast) * 0.2
# drop tracks/roads: within 8 m of a TIGER road
x_m = B[0] + (D.px + 0.5) * RES; y_m = B[3] - (D.py + 0.5) * RES
lon, lat = Ti.transform(x_m.values, y_m.values); D["lon"], D["lat"] = lon, lat
roads = gpd.read_file(os.path.join(DATA, "roads.geojson")).to_crs(26911)
P = gpd.GeoDataFrame(D, geometry=gpd.points_from_xy(x_m, y_m), crs=26911)
j = gpd.sjoin_nearest(P[["geometry"]], roads[["geometry"]], how="left", distance_col="road_m"); j = j[~j.index.duplicated()]
D["road_m"] = j.road_m.values; D = D[D.road_m > 8]
D = D.sort_values("score", ascending=False).reset_index(drop=True)
print("final candidates", len(D), "| persistent in 2019:", int((D.contrast2019 >= 0.5 * D.contrast).sum()))
D.drop(columns=[]).to_csv(os.path.join(DATA, "mounds_test_candidates.csv"), index=False)

# 50 review clips: top 35 + 15 spread over the 50-95th percentile band (so the review says something about lower scores too)
rng = np.random.default_rng(42)
top = D.head(35); rest = D.iloc[35:]
lower = rest[rest.score >= rest.score.quantile(0.5)]
pick = pd.concat([top.assign(band="top"), lower.sample(min(15, len(lower)), random_state=42).assign(band="lower")]).sample(frac=1, random_state=7).reset_index(drop=True)
def clip(img, x, y, half=25, up=5):
    rgb = np.clip(img[:3, y - half:y + half, x - half:x + half].transpose(1, 2, 0), 0, 255).astype("uint8")
    im = Image.fromarray(rgb).resize((2 * half * up, 2 * half * up), Image.NEAREST); d = ImageDraw.Draw(im)
    r3 = 1.5 / RES * up; c = half * up
    d.ellipse([c - r3 * 2.2, c - r3 * 2.2, c + r3 * 2.2, c + r3 * 2.2], outline=(255, 40, 40), width=2)   # ring at ~6.6 m diameter, centre left clear
    d.line([5, 2 * half * up - 8, 5 + 5 / RES * up, 2 * half * up - 8], fill=(255, 255, 0), width=3)       # 5 m scale bar
    buf = io.BytesIO(); im.save(buf, "PNG"); return base64.b64encode(buf.getvalue()).decode()
clips = []
for i, r in pick.iterrows():
    clips.append({"id": f"c{i+1:02d}", "lat": round(r.lat, 6), "lon": round(r.lon, 6), "score": round(float(r.score), 3), "band": r.band,
                  "diam_m": round(r.diam_m, 1), "in_2019": bool(r.contrast2019 >= 0.5 * r.contrast), "img2022": clip(a22, int(r.px), int(r.py)), "img2019": clip(a19, int(r.px), int(r.py))})
json.dump(clips, open(os.path.join(OUT, "clips.json"), "w"))
with open(os.path.join(DATA, "PROVENANCE.csv"), "a", newline="") as f:
    for nm, url in (("test_2022.tif", "https://planetarycomputer.microsoft.com/api/stac/v1 naip 2022 (0.6 m)"),
                    ("test_2019.tif", "https://planetarycomputer.microsoft.com/api/stac/v1 naip 2019 (0.6 m)")):
        p = os.path.join(NAIP, nm)
        csv.writer(f).writerow([f"NAIP test area ({nm})", url, f"naip/{nm}", N * N, hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16], datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
print("clips", len(clips), pick.band.value_counts().to_dict())
