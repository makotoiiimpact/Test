"""Minimal paginated ArcGIS REST query helper (no keys, bbox in WGS84)."""
import json, time, requests

def query(url, bbox, where="1=1", out_fields="*", geometry=True, page=2000, max_pages=200, extra=None):
    xmin, ymin, xmax, ymax = bbox
    params = {
        "where": where, "geometry": f"{xmin},{ymin},{xmax},{ymax}",
        "geometryType": "esriGeometryEnvelope", "inSR": 4326, "outSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "outFields": out_fields,
        "returnGeometry": str(geometry).lower(), "f": "geojson",
        "resultRecordCount": page,
    }
    if extra: params.update(extra)
    feats, offset = [], 0
    for _ in range(max_pages):
        params["resultOffset"] = offset
        for attempt in range(4):
            r = requests.get(url + "/query", params=params, timeout=120)
            if r.status_code == 200 and "error" not in r.text[:200]:
                break
            time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"query failed: {r.status_code} {r.text[:300]}")
        d = r.json()
        batch = d.get("features", [])
        feats += batch
        if not batch or not d.get("exceededTransferLimit", len(batch) >= page):
            break
        offset += len(batch)
    return {"type": "FeatureCollection", "features": feats}
