# placer-scout — Implementation Plan

Hobby project. Local only. Nothing deployed. Nothing committed without owner OK.
Status key: [ ] not started · [~] in progress · [x] done · [!] blocked / layer missing

## Environment notes (read first)
- Runs in a Linux cloud container (16 GB RAM, ~30 GB disk), not the owner's Mac. Project lives in
  `/home/user/Test/placer-scout`. Copy it to `~/Projects/placer-scout` on the Mac if wanted.
- Outbound network goes through a proxy; every source must be re-verified here before use.
- All raster work is windowed / COG-based. Total downloads capped at 10 GB (tracked in `data/PROVENANCE.csv`).

## Spec fixes from Step 0 review
| Original | Fix |
|---|---|
| Box 35.3–36.0N, 115.6–114.6W | **Admin/mining layers:** 35.0–36.1N, 115.7–114.5W (covers southern county edge + margin). **Hydrology buffer:** 35.2–36.4N, 115.9–114.4W so upstream catchments (Spring Mtns) are whole; results clipped to study box. All three districts confirmed inside: Goodsprings ~35.83N 115.43W, Eldorado Canyon/Nelson ~35.70N 114.80W, Searchlight ~35.47N 114.92W. |
| MRDS as gold-source | MRDS frozen since 2011 → combine MRDS + USMIN + NBMG + GNIS mine/mill. A mapped mine is a weak signal. |
| Claim polygons prove open/closed | MLRS geometry is ~quarter-section accurate. "Open" is reported as **"likely open — verify"**, with MLRS re-check link. |
| NPS/wilderness/private only | Also exclude: USFS, state, tribal, military/DOE, wildlife refuge, patented/private parcels (Clark County assessor parcels if obtainable), desert tortoise habitat flagged. |
| Product score zeroes out | Legal status = **hard gate**. Other factors are multiplicative but floored at 0.1 so one missing record cannot erase a site; every factor stays visible. |
| "Flood since last worked" | Claim closure ≠ worked. Defined as peak rainfall index in catchment after latest closure (or 2000). Reported with data basis (gauge / radar / none) and uncertainty. Not claimed as a confirmed flood unless gauge or imagery supports it. |
| Gold trap features additive | Slope break / junction / widening are correlated → take max (not sum). 10 m DEM = coarse screen only; 1 m lidar refines top 25 where it exists. |
| Source "upstream" binary | Distance-decayed and drainage-area weighted. |
| Top 25 | Diversity rule: max per district, minimum spacing. Stop and report if all are named mines. |
| Sentinel-2 change detection | Optional hint only (10 m, cloud/shadow/moisture false positives). Cloud mask via SCL. |
| CRS | Process in EPSG:26911; display in WGS84. Check NAD27/NAD83 in old mine data. |
| Model honesty | Output is a rough prioritisation, not a gold prediction. Not legal land status. Claimant names removed. |

## Steps

### Step 0 — Review and plan
- [x] Fresh-context reviewer run; findings folded into this plan
- [x] Project folder + this plan created

### Step 1 — Gather layers (verify each URL live; log in `data/PROVENANCE.csv`)
**Network check 2026-10-31 (this container):** egress policy returns 403 on CONNECT for these hosts, so those layers are **MISSING / unverified** (nothing mocked):
- gis.blm.gov (MLRS claims, SMA land status)
- mrdata.usgs.gov (MRDS), nbmg.unr.edu (NBMG), services.arcgis.com (MRDS/USMIN mirrors)
- earth-search.aws.element84.com, planetarycomputer.microsoft.com (Sentinel-2 STAC)
- www.ncei.noaa.gov (Storm Events), gustfront.ccrfcd.org (Clark County rainfall)
Reachable: prd-tnm.s3.amazonaws.com (3DEP DEM), noaa-mrms-pds.s3.amazonaws.com (MRMS rain), pypi.
Only layers 1.4 (DEM) and part of 1.6 (MRMS) can be built until the allowlist is widened. Work paused on the rest.

- [ ] 1.1 Gold sources: MRDS, USMIN, NBMG district data, GNIS mills/mines
- [ ] 1.2 BLM MLRS claims, not-closed + closed (ArcGIS REST, paginated, bbox query), with filing/closing dates
- [ ] 1.3 Land status: BLM SMA + NPS/Lake Mead NRA, wilderness, USFS, refuge, private/parcels
- [ ] 1.4 3DEP ~10 m DEM (COG, windowed); fill pits, flow accumulation, wash segments, junctions, slope breaks, widening
- [ ] 1.5 Sentinel-2 L2A iron-oxide / clay ratios (no-login STAC); EMIT only if credentials already exist
- [ ] 1.6 Rain/flood: Clark County RFCD rainfall, NOAA Storm Events, MRMS/Stage IV for ungauged areas
- [ ] 1.7 Sentinel-2 before/after wash change around biggest storms (optional hint)

### Step 2 — Score wash segments
- [ ] Gold-source, flood, trap, legal factors computed and stored separately
- [ ] Diversity rule + top 25 selection; 1 m lidar check for top 25 where coverage exists

### Step 3 — Outputs
- [ ] `out/targets.csv`
- [ ] `out/map.html` (layer toggles)
- [ ] `out/REPORT.md` (top 10, 9th-grade level, safety note)

### Step 4 — Verify
- [ ] Scripted checks (`src/verify.py`): provenance of every score, no excluded land, map opens
- [ ] Verifier subagent run; fixes applied; report to owner

## Stop conditions
Login/API key needed · downloads >10 GB or memory trouble · unverifiable source (mark layer missing) ·
top 25 all named mines · any commit/repo/push (run `git rev-parse --show-toplevel`, show diff, wait for OK).

---
## Add-on: 3D terrain view + Google links (runs AFTER Phase 1 passes its verifier)
Gate: needs `out/targets.csv` (top 25) and `out/map.html`. If either is missing, build nothing and invent no targets.
Status: [ ] waiting on Phase 1 (blocked by network allowlist; see Step 1 note)

### Spec fixes from review (items marked VERIFY must be checked live before use)
- MapLibre GL JS needs no key. Vendor the JS/CSS locally (no CDN). Use a minimal style with no glyph/sprite URLs.
- Must be served over `http://localhost` (e.g. `python -m http.server`); `file://` will not load tiles/workers. A `serve.sh` is part of the deliverable.
- Terrain tiles: raster-dem, terrarium or mapbox encoding, written by a numpy/GDAL script as XYZ PNG folders per target (gdal2tiles alone does not make DEM tiles). Hillshade uses its own raster-dem source.
- 1 km box shows a void when tilted: add a coarser 10 m DEM + NAIP margin around each box, and cap pitch.
- 1 m vs 10 m: detect 1 m coverage via TNM Access API / WESM (VERIFY). Never infer source from requested resolution (the 3DEP ImageServer resamples). Require 1 m coverage across the whole box, else use 10 m, or label "mixed". Store `dem_source, native_res_m, workunit, year` per target and show it in the panel.
- NAIP: public domain. Keyless source = USGS National Map NAIP ImageServer (VERIFY endpoint, year, GSD per target; record them). AWS `naip-analytic` is requester-pays and Planetary Computer needs a SAS token, so neither is used. If no keyless source is reachable, mark the NAIP drape MISSING and ship shaded relief only.
- Slider 1x–4x (default 2x) via `map.setTerrain({exaggeration})`, debounced. Use one reusable map instance (or `map.remove()` between targets) to avoid the WebGL context cap.
- Google, links only; no Google imagery fetched, stored or screenshotted:
  - Maps: `https://www.google.com/maps/@?api=1&map_action=map&center=LAT,LON&zoom=18&basemap=satellite` (documented).
  - Earth web: `https://earth.google.com/web/@LAT,LON,ALTa,DISTd,35y,0h,0t,0r` (undocumented, VERIFY); fallback `earth.google.com/web/search/LAT,LON`.
  - Links use `target="_blank" rel="noopener noreferrer"`. "Tested" = URL string/coordinate match against targets.csv; cannot test Google's rendering headlessly.
  - `targets.kml`: namespace `http://www.opengis.net/kml/2.2`, `coordinates` = `lon,lat,0` (longitude first), clampToGround, XML-escaped names, a LookAt per Placemark.
- REPORT.md sentence is softened: Earth Pro's historical imagery slider can compare a wash before and after a storm *where imagery dates exist*. Add a land-status reminder (BLM, claims, private) before any visit.
- Size: expected well under 300 MB; the build script stops if tiles exceed 2 GB. `tiles/` and caches stay out of git. Build is idempotent with a manifest.
- Verifier: serve over localhost, Chromium with `--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist`; click 3 targets; wait for `idle`; check `map.getTerrain()` non-null, tiles all 200, no console errors, `queryTerrainElevation` close to the GeoTIFF value, non-blank screenshot, relief at 4x ≈ 2× relief at 2x; compare coordinates in links and KML to targets.csv.

### Steps
- [ ] A1 Coverage check + `dem_source.json` per target
- [ ] A2 Terrain tiles (1 m or 10 m) + margin; NAIP image per target (or mark MISSING)
- [ ] A3 Side-panel 3D view in map.html: terrain/NAIP/hillshade toggle, 1x–4x slider, source label
- [ ] A4 Google Earth / Maps links per target
- [ ] A5 `out/targets.kml` + REPORT.md sentence
- [ ] A6 Verifier subagent + fixes + report to owner
