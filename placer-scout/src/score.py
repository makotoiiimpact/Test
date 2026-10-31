"""Step 2: score wash cells. Score = gold_source x flood x trap (each floored at 0.1), legal status is a hard gate.
Every factor and its evidence (source record, gauge, radar date, storm report) is written out so a score can be traced."""
import os, sys, json, math
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.warp import reproject, Resampling
from scipy.ndimage import uniform_filter
from pysheds.grid import Grid
from pysheds.sview import Raster
if not hasattr(np, "in1d"): np.in1d = np.isin

DATA = os.path.join(os.path.dirname(__file__), "..", "data"); OUT = os.path.join(os.path.dirname(__file__), "..", "out")
WINDOWS = {"west": (-115.75, 35.55, -115.15, 36.15), "east": (-115.25, 35.20, -114.55, 35.95)}
STUDY = (-115.7, 35.0, -114.5, 36.1)
EDGE_M = 1500                         # drop cells this close to a window edge (truncated catchments)
STREAM_KM2 = 0.25
L_DECAY, MAX_TRACE = 2000.0, 8000.0   # gold-source distance decay (m) and trace limit (m)
FLOOR = 0.1
CODES = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
DISTRICTS = {"Goodsprings": (-115.43, 35.83), "Eldorado Canyon/Nelson": (-114.80, 35.70),
             "Searchlight": (-114.92, 35.47), "Crescent": (-115.17, 35.46)}

def rd(name, w):
    with rasterio.open(os.path.join(DATA, f"{name}_{w}.tif")) as s:
        return s.read(1), s.transform, s.profile

def window_cells(w):
    z, tr, prof = rd("filled", w); fd, _, _ = rd("fdir", w); acc, _, _ = rd("acc", w); hand, _, _ = rd("hand", w)
    H, W = z.shape; lat0 = tr.f + tr.e * H / 2
    dy = abs(tr.e) * 111_320; dx = tr.a * 111_320 * math.cos(math.radians(lat0)); cell_km2 = dx * dy / 1e6
    thr = STREAM_KM2 / cell_km2
    # downstream index + step length per cell
    dr = np.zeros(256, np.int8); dc = np.zeros(256, np.int8); ln = np.zeros(256, np.float32)
    for k, (a, b) in CODES.items():
        dr[k], dc[k] = a, b; ln[k] = math.hypot(a * dy, b * dx)
    rr, cc = np.indices((H, W), dtype=np.int32)
    nr = rr + dr[fd]; nc = cc + dc[fd]
    ok = (fd > 0) & np.isin(fd, list(CODES)) & (nr >= 0) & (nr < H) & (nc >= 0) & (nc < W)
    down = np.where(ok, nr.astype(np.int64) * W + nc, -1).ravel(); del rr, cc, nr, nc
    step = ln[fd].ravel(); accf = acc.ravel().astype(np.float32)
    # main upstream neighbour (largest contributing area)
    v = np.flatnonzero(down >= 0); order = v[np.argsort(accf[v], kind="stable")]
    up = np.full(H * W, -1, np.int64); up[down[order]] = order; del order, v
    return dict(z=z.ravel(), fd=fd, acc=accf, hand=hand.ravel(), down=down, up=up, step=step, tr=tr, H=H, W=W,
                dx=dx, dy=dy, cell_km2=cell_km2, thr=thr, prof=prof)

def trace(C, start, direction, max_m):
    idx = start.copy(); dist = np.zeros(len(idx), np.float32); act = np.ones(len(idx), bool)
    nxt = C["down"] if direction == "down" else C["up"]
    for _ in range(int(max_m / min(C["dx"], C["dy"])) + 2):
        n = nxt[idx]; ok = act & (n >= 0)
        if not ok.any(): break
        dist[ok] += (C["step"][idx[ok]] if direction == "down" else C["step"][n[ok]])
        idx[ok] = n[ok]; act = ok & (dist < max_m)
    return idx, dist

CORE_GATE_M = 2000     # a recorded gold mine/mill/tailings must lie within this distance upstream along the flow path
PIT_CAP = 0.5          # topo-map shafts/adits/pits together can add at most half a producing mine's worth of influence

def is_core(src):
    """recorded gold evidence: MRDS gold records (incl. mills/plants) and USMIN tailings/mine dumps"""
    return (src.src_dataset == "MRDS") | (src.kind == "tailings/dump") | (src.kind == "mill/plant")

def source_influence(C, src):
    H, W, tr = C["H"], C["W"], C["tr"]
    col = ((src.geometry.x - tr.c) / tr.a).astype(int).values; row = ((src.geometry.y - tr.f) / tr.e).astype(int).values
    m = (row >= 0) & (row < H) & (col >= 0) & (col < W)
    idx = (row[m].astype(np.int64) * W + col[m]); wts = src.weight.values[m].astype(np.float32); sid = np.flatnonzero(m)
    infl = np.zeros(H * W, np.float32); best = np.zeros(H * W, np.float32); bsrc = np.full(H * W, -1, np.int32); bdist = np.zeros(H * W, np.float32)
    dmin = np.full(H * W, np.inf, np.float32)
    dist = np.zeros(len(idx), np.float32); act = np.ones(len(idx), bool)
    for _ in range(int(MAX_TRACE / min(C["dx"], C["dy"])) + 2):
        c = wts * np.exp(-dist / L_DECAY)
        np.add.at(infl, idx[act], c[act]); np.minimum.at(dmin, idx[act], dist[act])
        up = act & (c > best[idx]); best[idx[up]] = c[up]; bsrc[idx[up]] = sid[up]; bdist[idx[up]] = dist[up]
        n = C["down"][idx]; ok = act & (n >= 0)
        if not ok.any(): break
        dist[ok] += C["step"][idx[ok]]; idx[ok] = n[ok]; act = ok & (dist <= MAX_TRACE)
    return infl, bsrc, bdist, dmin

def altered_fraction(C, w):
    """share of the upstream catchment with co-located Sentinel-2 iron-oxide (z>1.5) and clay (z>1.0) anomaly on slopes > 5 deg"""
    H, W, tr = C["H"], C["W"], C["tr"]
    zz = {}
    for k in ("s2_feox_z", "s2_clay_z"):
        p = os.path.join(DATA, f"{k}_{w}.tif")
        if not os.path.exists(p): return None
        with rasterio.open(p) as s:
            a = np.full((H, W), np.nan, np.float32)
            reproject(s.read(1), a, src_transform=s.transform, src_crs=s.crs, dst_transform=tr, dst_crs="EPSG:4326", resampling=Resampling.average)
        zz[k] = a
    z2 = C["z"].reshape(H, W); gy, gx = np.gradient(z2, C["dy"], C["dx"]); slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    # co-located iron-oxide AND clay anomaly on bedrock slopes (either alone flags red beds / carbonates / playas)
    alt = ((zz["s2_feox_z"] > 1.5) & (zz["s2_clay_z"] > 1.0) & (slope > 5)).astype(np.float64)
    g = Grid.from_raster(os.path.join(DATA, f"fdir_{w}.tif")); fdr = g.read_raster(os.path.join(DATA, f"fdir_{w}.tif"))
    acc_alt = g.accumulation(fdr, weights=Raster(alt, viewfinder=fdr.viewfinder), dirmap=(64, 128, 1, 2, 4, 8, 16, 32))
    return (np.asarray(acc_alt).ravel() / np.maximum(C["acc"], 1)).astype(np.float32), alt

def junction_score(C, cand):
    s = np.flatnonzero(C["acc"] >= C["thr"]); d = C["down"][s]; keep = d >= 0
    df = pd.DataFrame({"d": d[keep], "a": C["acc"][s][keep]}).sort_values(["d", "a"], ascending=[True, False])
    df["rk"] = df.groupby("d").cumcount()
    a1 = df[df.rk == 0].set_index("d")["a"]; a2 = df[df.rk == 1].set_index("d")["a"]
    j = (a2 / a1.reindex(a2.index)).clip(upper=1.0)
    J = np.zeros(C["H"] * C["W"], np.float32); jidx = j.index.values.astype(np.int64); jval = np.clip(j.values / 0.5, 0, 1).astype(np.float32)
    J[jidx] = np.maximum(J[jidx], jval)
    idx = jidx.copy(); dist = np.zeros(len(idx), np.float32)
    for _ in range(int(150 / min(C["dx"], C["dy"])) + 1):          # deposition zone: 150 m below the confluence
        n = C["down"][idx]; ok = (n >= 0) & (dist < 150)
        dist[ok] += C["step"][idx[ok]]; idx[ok] = n[ok]
        np.maximum.at(J, idx[ok], jval[ok])
    return J[cand]

def run(w, src, gauges, storms, sma_ok, sma_bad, claims_act, wild):
    C = window_cells(w); H, W, tr = C["H"], C["W"], C["tr"]
    core = is_core(src).values
    srcC = src[core].reset_index(drop=True); srcP = src[~core].reset_index(drop=True)
    inflC, bsrc, bdist, dcore = source_influence(C, srcC)
    inflP, _, _, _ = source_influence(C, srcP)
    infl = inflC + np.minimum(inflP, PIT_CAP)
    src = srcC                                   # the reported "strongest source" is always a recorded gold source
    af = altered_fraction(C, w)
    Gs = 1 - np.exp(-infl / 2.5)          # saturates slowly: one producing mine at the cell ~0.33, several nearby -> ~1
    A = np.clip(af[0] / 0.05, 0, 1) if af is not None else np.zeros_like(Gs)
    stream = C["acc"] >= C["thr"]
    rows, cols = np.divmod(np.arange(H * W, dtype=np.int64), W)
    edge_px = (EDGE_M / C["dy"], EDGE_M / C["dx"])
    inner = (rows > edge_px[0]) & (rows < H - edge_px[0]) & (cols > edge_px[1]) & (cols < W - edge_px[1])
    cand = np.flatnonzero(stream & inner & (dcore <= CORE_GATE_M) & (Gs > 0.05)); del rows, cols   # gate: recorded gold source <= 2 km upstream
    lon = tr.c + (cand % W + 0.5) * tr.a; lat = tr.f + (cand // W + 0.5) * tr.e
    ins = (lon >= STUDY[0]) & (lon <= STUDY[2]) & (lat >= STUDY[1]) & (lat <= STUDY[3]); cand, lon, lat = cand[ins], lon[ins], lat[ins]
    print(w, "candidate wash cells", len(cand), flush=True)
    # --- trap: slope break ---
    z = C["z"]
    i_dn, d_dn = trace(C, cand, "down", 300); i_up, d_up = trace(C, cand, "up", 300)
    s_dn = np.where(d_dn > 50, (z[cand] - z[i_dn]) / np.maximum(d_dn, 1), np.nan)
    s_up = np.where(d_up > 50, (z[i_up] - z[cand]) / np.maximum(d_up, 1), np.nan)
    drop = (s_up - s_dn) / s_up
    # slope break: 40% gradient drop starts, 90% = full
    SB = np.where(s_up >= 0.02, np.clip((drop - 0.4) / 0.5, 0, 1), 0); SB = np.nan_to_num(SB)
    # --- trap: junction ---
    J = junction_score(C, cand)
    # --- trap: widening (valley-floor width proxy from HAND < 1.5 m in a ~200 m box) ---
    k = int(round(200 / C["dy"])) | 1
    flo = ((C["hand"] >= 0) & (C["hand"] < 1.5)).reshape(H, W).astype(np.float32)
    width = (uniform_filter(flo, size=(k, int(round(200 / C["dx"])) | 1)) * 200).ravel()
    w_here, w_up = width[cand], width[i_up]
    # widening: width x1.3 starts, x3.5 = full
    WD = np.where((w_here >= 15) & (d_up > 50), np.clip((w_here / np.maximum(w_up, 10) - 1.3) / 2.2, 0, 1), 0)
    trapv = np.vstack([SB, J, WD]); T = trapv.max(0); ttype = np.array(["slope_break", "junction", "widening"])[trapv.argmax(0)]
    ttype[T <= 0] = "none"
    # --- gold source ---
    G = np.maximum(Gs[cand], 0.3 * A[cand])          # altered rock alone is a weaker source than a mapped mine
    gtype = np.where(Gs[cand] >= 0.3 * A[cand], "mapped_source", "altered_rock")
    bi = bsrc[cand]
    df = pd.DataFrame({"window": w, "lon": lon, "lat": lat, "elev_m": z[cand], "drain_km2": C["acc"][cand] * C["cell_km2"],
                       "f_source": np.maximum(G, FLOOR), "source_basis": gtype, "source_influence_raw": infl[cand],
                       "influence_recorded_gold": inflC[cand], "influence_topo_pits": inflP[cand], "pits_capped": inflP[cand] > PIT_CAP,
                       "nearest_recorded_gold_upstream_m": dcore[cand],
                       "altered_frac_upstream": af[0][cand] if af is not None else np.nan,
                       "top_source_dataset": np.where(bi >= 0, src.src_dataset.values[np.maximum(bi, 0)], ""),
                       "top_source_id": np.where(bi >= 0, src.src_id.values[np.maximum(bi, 0)], ""),
                       "top_source_name": np.where(bi >= 0, src.name.values[np.maximum(bi, 0)], ""),
                       "top_source_kind": np.where(bi >= 0, src.kind.values[np.maximum(bi, 0)], ""),
                       "top_source_dist_m": np.where(bi >= 0, bdist[cand], np.nan),
                       "top_source_url": np.where(bi >= 0, src.url.values[np.maximum(bi, 0)], ""),
                       "f_trap": np.maximum(T, FLOOR), "trap_type": ttype, "trap_slope_break": SB, "trap_junction": J, "trap_widening": WD,
                       "grad_up": s_up, "grad_down": s_dn, "floor_width_m": w_here, "floor_width_up_m": w_up})
    # thin to the best cell per ~100 m block
    df["blk"] = ((cand // W) // 10) * 100000 + (cand % W) // 10
    df["pre"] = df.f_source * df.f_trap
    df = df.sort_values("pre", ascending=False).drop_duplicates("blk").drop(columns=["blk", "pre"])
    return df

def flood(df, gauges, storms):
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326).to_crs(26911)
    with rasterio.open(os.path.join(DATA, "mrms_max24h_mm.tif")) as s:
        df["radar_max24h_mm"] = [v[0] for v in s.sample(zip(df.lon, df.lat))]
    with rasterio.open(os.path.join(DATA, "mrms_max24h_date.tif")) as s:
        df["radar_max_date"] = [str(v[0]) for v in s.sample(zip(df.lon, df.lat))]
    g = gpd.GeoDataFrame(gauges, geometry=gpd.points_from_xy(gauges.lon, gauges.lat), crs=4326).to_crs(26911)
    j = gpd.sjoin_nearest(pts[["geometry"]], g[["name", "max_day_in", "max_day_date", "geometry"]], how="left", distance_col="gauge_dist_m")
    j = j[~j.index.duplicated()]
    near = j.gauge_dist_m <= 8000
    df["gauge_name"] = np.where(near, j.name, ""); df["gauge_dist_m"] = j.gauge_dist_m.round(0)
    df["gauge_max_day_mm"] = np.where(near, j.max_day_in * 25.4, np.nan); df["gauge_max_date"] = np.where(near, j.max_day_date, "")
    st = storms[storms.EVENT_TYPE.isin(["Flash Flood", "Flood", "Debris Flow"])].dropna(subset=["BEGIN_LAT"])
    sg = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.BEGIN_LON.astype(float), st.BEGIN_LAT.astype(float)), crs=4326).to_crs(26911)
    k = gpd.sjoin_nearest(pts[["geometry"]], sg[["EVENT_ID", "BEGIN_DATE_TIME", "geometry"]], how="left", distance_col="ff_dist_m")
    k = k[~k.index.duplicated()]
    ff = k.ff_dist_m <= 5000
    df["noaa_flood_event_id"] = np.where(ff, k.EVENT_ID, ""); df["noaa_flood_date"] = np.where(ff, k.BEGIN_DATE_TIME, ""); df["noaa_flood_dist_m"] = k.ff_dist_m.round(0)
    for name in ("recent_max24h_mm", "recent_max24h_date", "recent_total_mm", "baseline_total_mm"):
        with rasterio.open(os.path.join(DATA, f"{name}.tif")) as s_:
            df[name] = [v[0] for v in s_.sample(zip(df.lon, df.lat))]
    df["recent_vs_normal"] = (df.recent_total_mm / df.baseline_total_mm.clip(lower=1)).round(2)
    df["gauge_effective_mm"] = df.gauge_max_day_mm * np.exp(-df.gauge_dist_m / 5000)       # a gauge says less about a wash 5 km away
    P = np.fmax(np.fmax(df.radar_max24h_mm.astype(float), df.recent_max24h_mm.astype(float)), df.gauge_effective_mm.astype(float))
    df["rain_basis"] = np.where(np.fmax(df.radar_max24h_mm, df.recent_max24h_mm) >= df.gauge_effective_mm.fillna(-1), "MRMS radar (218 storm days 2021-01..2026-09, 5 km mean)", "RFCD gauge within 8 km (2000 to 2020-10-14)")
    df["storm_max_24h_mm"] = P
    df["fresh_storm_bonus"] = (np.clip((df.recent_max24h_mm - 20) / 60, 0, 1) * 0.2).round(3)   # Aug-Oct 2026 storm: fresh re-sorting
    df["f_flood"] = np.clip(np.clip((P - 20) / 100, 0, 1) + 0.15 * ff.values + df.fresh_storm_bonus, FLOOR, 1.0)   # 20 mm/24 h starts, 120 mm = full
    df["flood_since"] = "2000-01-01 (no claim closing dates in BLM bulk data)"
    return df

def legal(df, sma_ok, sma_bad, claims_act, wild, claims_closed):
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
    for g in (sma_ok, sma_bad, claims_act, wild, claims_closed):       # several source polygons are self-intersecting
        g["geometry"] = g.geometry.make_valid()
    def hit(layer, col=None):
        j = gpd.sjoin(pts[["geometry"]], layer[[c for c in [col] if c] + ["geometry"]], how="left", predicate="within")
        j = j[~j.index.duplicated()]
        return j.index_right.notna().reindex(pts.index).values, (j[col].reindex(pts.index).values if col else None)
    blm, blm_unit = hit(sma_ok, "ADMIN_UNIT_NAME")
    bad, bad_cls = hit(sma_bad, "sma_class")
    act, act_nr = hit(claims_act, "CSE_NR")
    wl, wl_nm = hit(wild, "NLCS_NAME") if "NLCS_NAME" in wild.columns else hit(wild)
    clo, clo_nr = hit(claims_closed, "CSE_NR")
    df["land_status"] = np.where(bad, "EXCLUDED: " + pd.Series(bad_cls).astype(str).values,
                         np.where(~blm, "EXCLUDED: not mapped as BLM", np.where(wl, "EXCLUDED: BLM wilderness",
                         np.where(act, "EXCLUDED: inside active mining claim", "BLM (likely open - verify)"))))
    acec = gpd.read_file(os.path.join(DATA, "acec_blm.geojson")); acec["geometry"] = acec.geometry.make_valid()
    ac, ac_nm = hit(acec, "ACEC_NAME")
    df["acec_flag"] = np.where(ac, pd.Series(ac_nm).astype(str).values, "")
    df["blm_unit"] = blm_unit; df["active_claim_case"] = np.where(act, act_nr, ""); df["closed_claim_case"] = np.where(clo, clo_nr, "")
    df["legal_ok"] = blm & ~bad & ~act & ~wl
    return df

if __name__ == "__main__":
    src = gpd.read_file(os.path.join(DATA, "gold_sources.geojson"))
    src["name"] = src.name.where(src.name.fillna("").str.strip().str.len() > 0, src.detail)
    gauges = pd.read_csv(os.path.join(DATA, "rain_gauges_summary.csv")); gauges = gauges[gauges.max_day_in <= 5]
    # gauges only fill the pre-radar years (2000 - 2020-10-14); from 2020-10-15 MRMS radar measures each wash directly
    daily = pd.read_csv(os.path.join(DATA, "rain_gauge_daily.csv.gz"), parse_dates=["date"])
    pre = daily[daily.date < "2020-10-15"]; mx = pre.loc[pre.groupby("numid")["in"].idxmax()].set_index("numid")
    gauges = gauges.assign(max_day_in=gauges.numid.map(mx["in"]), max_day_date=gauges.numid.map(mx["date"].dt.strftime("%Y-%m-%d"))).dropna(subset=["max_day_in"])
    storms = pd.read_csv(os.path.join(DATA, "storm_events.csv"), dtype=str)
    sma = {n: gpd.read_file(os.path.join(DATA, f"sma_{n}.geojson")) for n in
           ("BLM", "NPS", "USFS", "USFWS", "USBR", "BIA", "OtherFederal", "State", "Local", "PrivateOrUnknown", "DOD")}
    sma_ok = sma["BLM"]; sma_bad = pd.concat([g for n, g in sma.items() if n != "BLM" and len(g)])
    sma_bad = gpd.GeoDataFrame(sma_bad, geometry="geometry", crs=4326)
    claims_act = gpd.read_file(os.path.join(DATA, "claims_active.geojson")); claims_closed = gpd.read_file(os.path.join(DATA, "claims_closed.geojson"))
    pat = pd.concat([claims_act, claims_closed]); pat = pat[pat.MC_PATENTED.fillna("").astype(str).str.upper().isin(["Y", "YES", "TRUE", "1"])]
    if len(pat):     # patented claims are private land
        pat = pat.assign(sma_class="PatentedClaim")[["sma_class", "geometry"]]; sma_bad = gpd.GeoDataFrame(pd.concat([sma_bad, pat]), crs=4326)
    wild = gpd.read_file(os.path.join(DATA, "wilderness_blm.geojson"))
    nca = gpd.read_file(os.path.join(DATA, "nca_blm.geojson"))      # National Monuments / NCAs: withdrawn from mineral entry
    nca = nca.assign(sma_class="BLM monument/NCA: " + nca.NCA_NAME.fillna("?") + " (withdrawn from mineral entry)")[["sma_class", "geometry"]]
    sma_bad = gpd.GeoDataFrame(pd.concat([sma_bad, nca]), crs=4326)
    frames = []
    for w in (sys.argv[1:] or WINDOWS):
        frames.append(run(w, src, gauges, storms, sma_ok, sma_bad, claims_act, wild))
    df = pd.concat(frames, ignore_index=True)
    roads = gpd.read_file(os.path.join(DATA, "roads.geojson")).to_crs(26911)
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326).to_crs(26911)
    jr = gpd.sjoin_nearest(pts, roads[["geometry"]], how="left", distance_col="road_m"); jr = jr[~jr.index.duplicated()]
    df["road_m"] = jr.road_m.round(0).values
    df["trap_road_penalty"] = df.road_m < 30
    df["f_trap"] = np.where(df.trap_road_penalty, np.maximum(df.f_trap * 0.5, FLOOR), df.f_trap)
    df = flood(df, gauges, storms)
    df = legal(df, sma_ok, sma_bad, claims_act, wild, claims_closed)
    df["score"] = df.f_source * df.f_flood * df.f_trap
    d = {k: (v[0], v[1]) for k, v in DISTRICTS.items()}
    def district(lo, la):
        dd = {k: math.hypot((lo - x) * 90.4, (la - y) * 111.0) for k, (x, y) in d.items()}
        k = min(dd, key=dd.get); return k if dd[k] <= 25 else "other"
    df["district"] = [district(a, b) for a, b in zip(df.lon, df.lat)]
    df.to_parquet(os.path.join(DATA, "scored_cells.parquet")) if False else df.to_csv(os.path.join(DATA, "scored_cells.csv.gz"), index=False)
    print("scored cells", len(df), "legal", int(df.legal_ok.sum()))
    print(df.land_status.value_counts())
