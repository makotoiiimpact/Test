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
Network: first check was blocked by the egress policy; owner widened the allowlist on 2026-10-31. Still unreachable
after that: nbmg.unr.edu, www.usgs.gov, www.sciencebase.gov, naip-analytic (requester-pays), data.eol.ucar.edu.
No source needed a login or API key. Total downloads ≈ 2.5 GB (well under the 10 GB cap); peak memory 5.7 GB.

- [x] 1.1 Gold sources → `data/gold_sources.geojson` (7,789 points after removing 1,332 USMIN duplicates repeated across topo editions). MRDS WFS (727 records with AU; mrdata.usgs.gov/services/wfs/mrds),
      USMIN historical-topo mine features (shafts, adits, pits, tailings, mine dumps; mrdata.usgs.gov/services/wfs/usmin),
      GNIS NV names (prd-tnm). USMIN/GNIS features count fully only within 1 km of an MRDS gold record (Goodsprings is mostly Pb-Zn).
      [!] **NBMG district data MISSING** (host blocked). [!] GNIS has almost no "Mine" class features any more (1 mill found).
- [x] 1.2 BLM MLRS claims (nlsdbpubgis.blm.gov MiningClaims MapServer layers 1 and 2): 6,116 active/filed, 51,343 closed.
      [!] **No closing dates and no location dates** (`LOC_DT` empty on all records); [!] `MC_PATENTED` flags all empty.
- [x] 1.3 Land status: BLM SMA (all agency layers), BLM wilderness + WSA, BLM NCAs/National Monuments, ACECs (flag only).
      Added exclusion: **Avi Kwa Ame NM (2023), Red Rock Canyon NCA, Sloan Canyon NCA** — withdrawn from mineral entry.
      [!] Clark County assessor parcels not used; private/patented land relies on SMA "Private or Unknown".
- [x] 1.4 3DEP 1/3 arc-second COG windows (west 6480², east 8100×7560); pysheds fill/D8/accumulation/HAND; wash = 0.25 km².
      Scored area = two hydrology windows covering the districts (+Crescent); open valley floors outside them are not scored.
- [x] 1.5 Sentinel-2 L2A (Earth Search, 3 clear 2025 scenes per tile, 18 scenes): FeOx (B4/B2) and clay (B11/B12) z-scores.
      Altered = FeOx z>1.5 AND clay z>1.0 on slopes >5°. EMIT not used (needs Earthdata login).
- [x] 1.6 RFCD daily gauges 2000–2025 (gustfront zip + gauge GeoJSON, QC for uncorroborated >3 in days); NOAA Storm Events
      2000–2026 (375 flood/heavy-rain records); MRMS 24 h QPE for 218 candidate storm days since 2020-10-15.
      [!] Stage IV (pre-2020 radar) not used: not on reachable hosts in a usable form. RFCD has no 2026 file yet.
- [x] 1.7 Sentinel-2 before/after (top 25 only, each target's biggest radar-era storm): **no visible change at any target**.

### Step 2 — Score wash segments
- [x] Factors stored separately (`data/scored_cells.csv.gz`, 31,945 wash cells thinned to ~100 m; 7,213 pass the legal gate): source (distance-decayed trace,
      L=2 km, 8 km cap; altered rock capped at 0.3), flood (radar from 2020-10, gauges ≤8 km before that; 20→120 mm; +0.15 NOAA
      flood ≤5 km), trap (max of slope break / junction / widening). Floors 0.1. Legal = hard gate. Flood cut-off is 2000 everywhere
      because MLRS has no closing dates.
- [x] Top 25: ≥1 km apart, ≤10 per district. 1 m lidar (FEMA R9, Mountain Pass 2019, NV Southern, LV 2016) on all 25; 8 spots whose
      10 m widening was not confirmed were rejected and replaced (3 rounds). 2 of 25 within 300 m of a named mine → stop rule not hit.

### Step 3 — Outputs
- [x] `out/targets.csv` (25 rows, every factor + evidence + land status + road + PLSS + live BLM claim-check link)
- [x] `out/map.html` (folium, keyless USGS basemaps, 3 basemaps + 12 toggleable layers)
- [x] `out/REPORT.md` (top 10, plain language, limits, legal notes, safety)
- [x] `run_all.sh` rebuilds outputs from `data/`

### Step 4 — Verify
- [x] Verifier subagent run (independent re-trace + live BLM/USGS queries). PASS: every source, radar, gauge, NOAA event, PLSS and
      f_source value traced to raw data; no target on excluded land (local and live checks). Defects found and FIXED:
      map crashed (GeometryCollection in Leaflet 1.9.3 → polygons only; now 0 errors, 25 markers, 12 overlays, headless-checked);
      report said "closest" source (now "strongest"); 1,332 duplicate USMIN features; radar label overstated coverage (218 storm
      days, not continuous); off-by-one in MRMS date init (no cells affected); lidar date was publication date (renamed);
      unsupported "worked here" sentence removed. Added `nearest_exclusion_m` / `boundary_risk` (6 targets < 100 m).
- [ ] Not built: scripted `src/verify.py` (the verifier's scripts are in the session scratchpad only).

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

---
## Phase 2: L-208 shutdown mines + harvester ant mounds
Gate: Phase 1 passed its verifier (yes, 2026-10-31).

### Spec fixes from Phase 2 review
- **L-208 facts**: WPB Order L-208 issued Oct 8, 1942; effective Dec 8, 1942; revoked effective July 1, 1945 (June 30 in some sources).
  Small mines (≤1,200 tons in 1941) and copper/lead/zinc mines were exempt, so Goodsprings Pb-Zn mines are poor test cases.
- **Test changed**: "no production after 1942" alone is not enough. Classes: *strong* = active 1942, stopped Dec 1942, no record through 1947;
  *medium* = active 1942, stopped 1943; *stopped at L-208, reopened*; *possible* = last record 1941 (1942 yearbook silent ≠ shutdown);
  *not a candidate*. Field is "last recorded year" in the yearbooks, never inferred from silence.
- **Yearbook years**: 1939 and 1940 editions report the prior year; 1940 data is in the separate "Review of 1940" volume; 1941+ report
  their own year. All verified from each volume's text.
- **Scoring rule (A7)**: a 1942 shutdown does not add gold to washes; kept as the owner asked but small and visible
  (`l208_boost` on the source weight), mill tailings being the one physical reason.
- **Ant mounds**: the common Mojave harvester (*Veromessor pergandei*) makes 30–45 cm craters with no cleared disc; 1–3 m discs are
  *Pogonomyrmex*, sparse in creosote scrub. At 0.6 m NAIP a 2.5–3 m disc is 4–5 px. Kept the owner-review gate; clips sample 35 top +
  15 lower-band picks; 2019 is shown beside 2022 for persistence. Field note: harvester ants sting; scan, don't dig.
- **NAIP**: newest Nevada NAIP is 2022 at 0.6 m (not coarser than 60 cm, so no stop). Original COGs from Planetary Computer
  (anonymous SAS token, no account); the USGS NAIPPlus service is keyless but recompressed. 2019 (0.6 m) used for persistence.

### Steps
- [x] A1 Minerals Yearbooks 1939–1947 + Review of 1940 (archive.org OCR, page-indexed) → Clark County passages
- [x] A2–A6 `out/l208_mines.csv` (19 mines) + `data/l208/l208_evidence.csv` (59 records, every quote auto-verified on its cited page).
      [!] NBMG Clark County bulletins and Nevada Inspector of Mines reports not reachable (nbmg.unr.edu, HathiTrust blocked).
      [!] 1947 Searchlight paragraph partly unreadable in OCR (continues after a rotated table).
- [ ] A4 dumps/mill sites near candidates (USMIN tailings/dump polygons + NAIP clips)
- [ ] A7 `l208_boost` in scoring, then rerun Phase 1 pipeline
- [x] B1 NAIP resolution check (2022, 0.6 m)
- [x] B3–B4 detector on one test area (Nelson, below Rand/Quaker City, BLM only); 50 clips; review page published
      (private artifact with saved answers). **Waiting for owner review.**
- [!] B5 **STOPPED by the stop rule**: owner review (2026-10-31) = 0 yes, 24 no, 26 not sure out of 50 (`out/review/labels.json`).
      The 0.6 m NAIP scan is not finding mounds; no tuning, no full scan. A drone survey (~1–2 cm/px) could revisit the question.
- [!] B6 not built (no mounds to list)
- [ ] C REPORT Phase 2 section + verifier

---
## Model v2 (2026-10-31, owner request after Searchlight review)
- [x] Gold source must include a **recorded** gold source (MRDS gold record, mill/plant, or USMIN tailings/mine dump) within
      **2 km upstream** along the flow path; topo-map shafts/adits/pits add at most 0.5 (half a producing mine). Altered rock only
      boosts spots that pass this gate.
- [x] Trap within **30 m of a mapped road** counts half (road ditches/culverts/embankments fake junctions in 10 m DEMs);
      1 m lidar confirmation restores it for the top 25.
- [x] Flood: rain gauge value fades with distance (×e^(-d/5 km)); radar now read for **every day Aug 1 – Oct 30 2026** (incl. the
      Oct 30–31 storm) plus the same window in 2023–25. Aug–Oct 2026 averaged 91 mm vs 54 mm (2023–25 mean). A "fresh storm"
      bonus (up to +0.2) for this season's biggest 24 h rain.
- [x] Result: 4,124 gated wash cells (1,106 legal) vs ~32,000 before; 15 of 25 targets replaced; 15 lidar rejections in 4 rounds.
- [x] Trails: BLM GTLF routes + USGS National Map trails added. No legal scored wash is within 300 m of a mapped hiking trail
      (closest 4.2 km); 141 are within 300 m of BLM-managed (mostly "limited motorized") routes → `out/blm_route_washes.csv`.

## Field plan v3 (2026-10-31)
- [x] Field plan narrowed to the top 8 targets (strong tier); ant-mound clip stops removed; after-rain safety section added.
- [x] Radar check (2026-10-31): MRMS Aug–Oct totals vs official RFCD daily files, 2023–25, at 25 study-area gauges: radar/gauge median
      1.49 (radar high). Year-to-year comparisons (radar vs radar) stand; absolute mm read high. The live gauge API
      (gaugeservices/geojson) returns 0 for past windows (tested on 2025 storms), so it cannot check 2026; Oct 30–31 storm unconfirmed.
