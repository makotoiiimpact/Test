"""Re-cut the 50 review clips (same ids/locations as out/review/clips.json) as plain crops at two extents: 30 m and 60 m,
1 pixel = 0.6 m, no ring drawn in (the page overlays it so it can be hidden)."""
import os, io, json, base64
import numpy as np, rasterio
from pyproj import Transformer
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), ".."); NAIP = os.path.join(ROOT, "data", "naip"); OUT = os.path.join(ROOT, "out", "review")
clips = json.load(open(os.path.join(OUT, "clips.json")))
srcs = {y: rasterio.open(os.path.join(NAIP, f"test_{y}.tif")) for y in (2022, 2019)}
PAD = 60
arr = {y: np.pad(s.read([1, 2, 3]), ((0, 0), (PAD, PAD), (PAD, PAD))) for y, s in srcs.items()}   # blank beyond the test-area edge
T = Transformer.from_crs(4326, 26911, always_xy=True)
def crop(y, lon, lat, half):
    x, yy = T.transform(lon, lat); r, c = srcs[y].index(x, yy); r += PAD; c += PAD
    a = np.clip(arr[y][:, r - half:r + half, c - half:c + half].transpose(1, 2, 0), 0, 255).astype("uint8")
    buf = io.BytesIO(); Image.fromarray(a).save(buf, "PNG"); return base64.b64encode(buf.getvalue()).decode()
out = [{"id": c["id"], "close22": crop(2022, c["lon"], c["lat"], 25), "close19": crop(2019, c["lon"], c["lat"], 25),
        "wide22": crop(2022, c["lon"], c["lat"], 50), "wide19": crop(2019, c["lon"], c["lat"], 50)} for c in clips]
json.dump(out, open(os.path.join(OUT, "clips_plain.json"), "w"))
print(len(out), "clips;", sum(len(v) for o in out for k, v in o.items() if k != "id") // 1024, "KB")
