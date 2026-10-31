"""Pick up to 3 clear Sentinel-2 L2A scenes per MGRS tile (most complete coverage first) for the alteration composite."""
import os, json, requests
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
q = {"collections": ["sentinel-2-l2a"], "bbox": [-115.75, 35.2, -114.55, 36.15],
     "datetime": "2025-06-01T00:00:00Z/2025-11-30T00:00:00Z", "query": {"eo:cloud_cover": {"lt": 2}}, "limit": 500}
d = requests.post("https://earth-search.aws.element84.com/v1/search", json=q, timeout=120).json()
by = {}
for f in d["features"]:
    by.setdefault(f["properties"]["grid:code"], []).append(f)
sel = []
for k, fs in sorted(by.items()):
    fs = sorted(fs, key=lambda f: (round(f["properties"].get("s2:nodata_pixel_percentage", 100)), f["properties"]["eo:cloud_cover"]))[:3]
    for f in fs:
        p = f["properties"]
        sel.append({"tile": k, "id": f["id"], "date": p["datetime"][:10], "cloud": p["eo:cloud_cover"],
                    "nodata_pct": p.get("s2:nodata_pixel_percentage"),
                    "assets": {b: f["assets"][b]["href"] for b in ("blue", "red", "nir08", "swir16", "swir22", "scl")}})
json.dump(sel, open(os.path.join(DATA, "s2_scenes.json"), "w"), indent=1)
for s in sel: print(s["tile"], s["id"], round(s["cloud"], 3), round(s["nodata_pct"], 1))
