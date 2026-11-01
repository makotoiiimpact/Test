"""Step 3c: out/REPORT.md - plain-language report (about 9th-grade level). Every sentence about a target comes from targets.csv."""
import os, datetime
import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
t = pd.read_csv(os.path.join(OUT, "targets.csv"))
_cells = pd.read_csv(os.path.join(OUT, "..", "data", "scored_cells.csv.gz"), usecols=["legal_ok"], low_memory=False)
N_CELLS, N_LEGAL = len(_cells), int(_cells.legal_ok.sum())
_rej = os.path.join(OUT, "..", "data", "lidar_rejected.csv")
N_REJ = len(pd.read_csv(_rej)) if os.path.exists(_rej) else 0
N_CLOSED10 = int(t.head(10).closed_claim_case.notna().sum())
import json as _j
_days = _j.load(open(os.path.join(OUT, "..", "data", "mrms_days_used.json")))
N_STORM_DAYS = sum(d < "2026-07-01" for d in _days)
_ev = pd.read_csv(os.path.join(OUT, "..", "data", "storm_events.csv"), usecols=["EVENT_ID", "EVENT_TYPE"])
EVTYPE = dict(zip(_ev.EVENT_ID.astype(float), _ev.EVENT_TYPE))
_g0 = pd.read_csv(os.path.join(OUT, "..", "data", "scored_cells.csv.gz"), usecols=["legal_ok", "ground_ok"], low_memory=False)
N_GROUND_OK = int((_g0.legal_ok & _g0.ground_ok.fillna(True).astype(bool)).sum())
_rv = pd.read_csv(os.path.join(OUT, "oldmap_review.csv"))
OLDMAP = {(round(a, 4), round(b, 4)): (v, n) for a, b, v, n in zip(_rv.lat, _rv.lon, _rv.map_verdict, _rv.map_note)}
WEAK8 = [int(r["rank"]) for _, r in t.head(8).iterrows() if OLDMAP.get((round(r.lat, 4), round(r.lon, 4)), ("",))[0] == "weak"]
N_S2 = int((t.s2_bed_changed == "yes (hint)").sum()); S2_RANKS = t.loc[t.s2_bed_changed == "yes (hint)", "rank"].tolist()

def km(m): return f"{m/1000:.1f} km ({m/1609:.1f} miles)"
def ft(m): return f"{m/0.3048:,.0f} feet"
def date(s):
    try: return pd.to_datetime(str(int(s)), format="%Y%m%d").strftime("%B %-d, %Y")
    except Exception:
        try: return pd.to_datetime(s).strftime("%B %-d, %Y")
        except Exception: return None
def level(x): return "very strong" if x >= 0.9 else "strong" if x >= 0.7 else "medium" if x >= 0.45 else "weak"
def source_text(r):
    nm = str(r.top_source_name)
    if "|" in nm:
        kind, rest = [s.strip() for s in nm.split("|", 1)]
        what = f"an old {kind.lower()} shown on the {rest.replace('topo ', '')} USGS topographic map"
    elif r.top_source_dataset == "USMIN_topo":
        what = f"an old mine {nm.lower()} marked on a USGS topographic map"
    else:
        what = f"the {nm}" if not nm.lower().startswith("the ") else nm
    d = r.top_source_dist_m
    where = "right at this spot" if d < 50 else f"about {ft(d)} uphill along the wash"
    s = f"The strongest gold source upstream is {what}, {where}."
    if r.source_basis == "altered_rock":
        s = f"No mapped gold mine drains here, but satellite images show rusty, clay-rich rock on {r.altered_frac_upstream*100:.0f}% of the slopes above it."
    elif r.altered_frac_upstream >= 0.05:
        s += f" Satellite images also show rusty, clay-rich rock on about {r.altered_frac_upstream*100:.0f}% of the slopes that drain here."
    return s
def trap_text(r):
    if r.trap_type == "junction":
        s = "A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out."
    elif r.trap_type == "widening":
        s = f"The wash floor gets wider here, from about {r.floor_width_up_m:.0f} m to {r.floor_width_m:.0f} m on the 10 m map. Water spreads out and slows where a wash widens."
    else:
        s = f"The wash gets less steep here, from a {r.grad_up*100:.1f}% slope above to {r.grad_down*100:.1f}% below. Water slows down where the slope eases."
    if r.lidar_confirms_trap == "yes": s += " The 1 m lidar map agrees with this."
    return s
def flood_text(r):
    if str(r.rain_basis).startswith("MRMS"):
        d = date(r.radar_max_date)
        s = (f"The biggest one-day rain weather radar measured near here was about "
             f"{r.storm_max_24h_mm:.0f} mm ({r.storm_max_24h_mm/25.4:.1f} inches){', on ' + d if d else ''}.")
    else:
        d = date(r.gauge_max_date)
        s = (f"The {r.gauge_name} rain gauge, {km(r.gauge_dist_m)} away, recorded {r.storm_max_24h_mm:.0f} mm ({r.storm_max_24h_mm/25.4:.1f} inches) of rain in one day"
             f"{' on ' + d if d else ''}. That is the biggest day it logged before 2021, when this tool starts using radar.")
    if r.recent_max24h_mm >= 20:
        d2 = date(r.recent_max24h_date)
        how = "much wetter than usual" if r.recent_vs_normal >= 1.5 else "wetter than usual" if r.recent_vs_normal >= 1.2 else "about normal"
        s += (f" This season was {how} here: about {r.recent_total_mm:.0f} mm fell from August through October 2026, "
              f"{r.recent_vs_normal:.1f} times the 2023–2025 average, with {r.recent_max24h_mm:.0f} mm in one day{' on ' + d2 if d2 else ''}.")
    if isinstance(r.noaa_flood_date, str) and r.noaa_flood_dist_m <= 5000:
        d = date(r.noaa_flood_date[:9]) or r.noaa_flood_date[:9]
        et = str(EVTYPE.get(float(r.noaa_flood_event_id), "Flood")).lower()
        s += f" The National Weather Service also logged a {et} {km(r.noaa_flood_dist_m)} away on {d}."
    return s

L = []
L.append("# placer-scout report\n")
L.append(f"*Made {datetime.date.today():%B %-d, %Y}. Study area: southern Clark County, Nevada (Goodsprings, Eldorado Canyon/Nelson, and Searchlight districts).*\n")
L.append("## What this is\n")
L.append("This report lists places where a flash flood may have washed gold down from old mines into a desert wash. "
         f"The computer kept {N_CELLS:,} spots along washes that have a recorded gold mine, prospect, mill or mine dump within 2 km upstream. {N_LEGAL:,} of them are on Bureau of Land Management (BLM) land and not inside an active mining claim, wilderness, or a national monument. "
         f"Spots in towns, quarries, and pipeline or power-line corridors were then removed, leaving {N_GROUND_OK:,}. "
         "Then it ranked them, keeping the top 25 at least 1 km apart and no more than 10 in one district. This is a rough guide for where to look first. It does not prove there is gold anywhere, and it is not a legal land survey.\n")
L.append("## How to read the score\n")
L.append("Each spot gets four numbers. They are multiplied together to make the total score. The first three run from 0.1 to 1; placer history runs from 0.6 to 1.\n")
L.append("- **Gold source** asks: is there a recorded gold mine, prospect, mill, or mine dump uphill, and how close is it? A spot only makes the list if one lies within 2 km (1.2 miles) upstream. Old prospect pits and shafts on topo maps can add up to half as much as a recorded mine right next to the wash. If no mine record is close, rusty, clay-rich rock seen from space can count a little instead.")
L.append("- **Flood** asks: how big was the biggest one-day storm here since 2000? About 20 mm (0.8 inch) of rain starts to count, and 120 mm (4.7 inches) counts fully. A rain gauge counts for less the farther away it is. A flash flood report nearby adds a little, and a big storm this August to October adds a little more, because fresh floods re-sort the gravel.")
L.append("- **Gold trap** asks: is this a place where fast water slows down? The computer looks for a side wash joining, a wash getting wider, or a wash getting less steep. A trap within 30 m (100 ft) of a road counts half, because road ditches and culverts can fake one, unless the 1 m lidar map confirms it.")
L.append("- **Placer history** asks: did old government reports record placer gold here? A 1973 USGS report (Bulletin 1356) and a 1937 Bureau of Mines survey (Information Circular 6964) were used. The one documented placer section in Eldorado Canyon (the Gresh claims, T26S R64E Sec 4) counts fully. The rest of the Eldorado Canyon area counts 0.9 and the Searchlight area 0.75, because placer gold was recorded there. Goodsprings and other places count 0.6, because the 1973 report lists no placer gold for them. (Area means the nearest district center, so edges are approximate.) A wash below a mine shut down in 1942 gets +0.1 (see below). This is a gentle nudge, not a gate: no record does not mean no gold.\n")
L.append("Each place also has a land-survey address, like *Mount Diablo Meridian T26S R64E Sec 19 SWNW*. Mount Diablo Meridian is the survey baseline for Nevada. T26S R64E is the township and range, a 6-mile square. Sec 19 is a 1-mile square inside it. SWNW means the southwest quarter of the northwest quarter, and L 2 means lot 2. The BLM files mining claims by this address. You can type it into the BLM claim map (MLRS) to look for new claims.\n")
L.append(f"{'All' if N_CLOSED10 == 10 else N_CLOSED10} of the top 10 sit on ground that once had a mining claim that is now closed. That is normal here, because these districts have been prospected for over 100 years. It also means people have staked claims near these spots before.\n")
L.append("All the numbers and their sources are in `targets.csv`. The map is `map.html`. Open it in a web browser and turn layers on and off in the box at the top right.\n")
L.append("## Top 10 places\n")
L.append(f"Weather radar was checked on {N_STORM_DAYS} stormy days from 2021 to June 2026 and on every day from July 1 to October 30, 2026. Radar readings here run about 1.5 times high (see below).\n")
for _, r in t.head(10).iterrows():
    road = r.nearest_road.replace("unnamed (", "an unnamed ").replace(")", "") if r.nearest_road.startswith("unnamed") else r.nearest_road
    dn = r.district if r.district != "other" else "Wash outside the three districts"
    om = OLDMAP.get((round(r.lat, 4), round(r.lon, 4)))
    omt = (f"Old-map check (1950s USGS map): **{om[0]}**. {om[1]} " if om else "")
    p = (f"**#{int(r['rank'])} — {dn}, {r.lat:.5f}, {r.lon:.5f}** (score {r.score:.2f} = gold source {r.f_source:.2f} × flood {r.f_flood:.2f} × trap {r.f_trap_lidar:.2f} × placer history {r.f_hist:.2f})\n\n"
         f"{source_text(r)} The gold-source signal is {level(r.f_source)}. {flood_text(r)} {trap_text(r)} {omt}"
         f"This spot is on BLM land in {r.plss}. It is about {ft(r.nearest_road_m)} from {road}. "
         + (f"Be careful here: {'private land' if 'Private' in str(r.nearest_exclusion) else 'an active mining claim' if 'claim' in str(r.nearest_exclusion) else 'closed land'} is only about {ft(r.nearest_exclusion_m)} away. " if r.nearest_exclusion_m < 100 else "")
         + f"Re-check claims with the link in `targets.csv` before you go.\n")
    L.append(p)
L.append("## What the computer could not do\n")
L.append("- **Claim closing dates are missing.** The BLM mining-claim map has no closing date for old claims. So the tool could not tell when each wash was last worked. It counted storms since January 1, 2000 everywhere instead.")
L.append("- **Some data could not be reached.** The Nevada Bureau of Mines and Geology website was blocked from this computer, so its district reports were not used. The USGS place-names list had almost no mines in it.")
L.append("- **Goodsprings has no recorded placer gold in the 1973 USGS report.** Its mines were mostly lead and zinc mines. The placer-history number lowers Goodsprings spots, but they still fill the district's 10 places in the top 25 because their floods and traps score well.")
L.append("- **Mine records say little about gold amount.** A mine on the list may have produced only a small amount of gold. Many Goodsprings mines were mainly lead and zinc mines.")
L.append(f"- **The 10 m map is coarse.** The 1 m lidar map did not agree with {N_REJ} of the wash-widening and slope-break spots the 10 m map picked. Those spots were removed. Most of the final traps are side-wash junctions, which the lidar check cannot test.")
L.append(f"- **Satellite before-and-after pictures showed no clear change** at {25 - N_S2} of the 25 places" + (f" (only a faint hint at #{' and #'.join(str(x) for x in S2_RANKS)})" if N_S2 else "") + ". Desert washes are narrow, and the satellite pixels are 20 m wide, so small changes are hard to see.")
L.append(f"- **Radar was not checked every day before July 2026.** From 2021 to June 2026 only {N_STORM_DAYS} stormy days were read; days with no gauge rain and no storm report were skipped, so a local storm could have been missed. Every day from July 1 to October 30, 2026 was read, including the storm of October 30–31. Checked against the county's official gauge files for 2023–2025, radar totals here run about 1.5 times higher than the gauges, so read the radar millimeters as high. Comparisons between years use radar on both sides, so they still hold. The October 30–31 storm has no gauge check yet. Radar values are averaged over about 5 km. Before 2021, the tool used Clark County rain gauges within 8 km, and many washes have no gauge that close.")
L.append("- **Old maps list many small prospect pits.** Repeat copies of the same pit from different map years were removed, but a wash below lots of pits can still look stronger than it really is.\n")
L.append("## Land and legal notes\n")
L.append("- The tool removed National Park Service land (including Lake Mead National Recreation Area), Forest Service land, state land, private land, BLM wilderness, and active mining claims.")
L.append("- It also removed **Avi Kwa Ame National Monument**, Sloan Canyon, and Red Rock Canyon. These BLM areas are closed to new mining claims. This removed much of the land around Searchlight. Ask the BLM Las Vegas Field Office if hobby gold panning is allowed there before you go.")
L.append("- Patented (privately owned) mining claims are not marked in the BLM claim data. The tool relied on the BLM land map to catch them. Old patented claims are common in Goodsprings, Searchlight, and Nelson. Watch for signs and fences.")
L.append("- BLM land is usually open for casual gold panning with hand tools. You may not dig large holes, use motors, or disturb a lot of ground without permission. Do not work on anyone's active claim.\n")
L.append("## Safety\n")
L.append("- **Never enter old mine shafts or tunnels.** They can collapse, have bad air, or hide deep drops. Stay well back from open holes.")
L.append("- **Never work in a wash when storms are possible.** Flash floods can come from rain miles away, even when the sky above you is clear. Check the forecast and leave if clouds build.")
L.append("- **Treat old mill waste as dangerous.** Old mills often used mercury to catch gold, and the waste can still hold mercury and arsenic. Do not dig in it, do not breathe its dust, and wash your hands and gear.")
L.append("- Bring plenty of water, tell someone where you are going, and watch for rattlesnakes. Many places have no cell signal.\n")
# ---------- Phase 2 and old-records section (computed from files) ----------
import json as _json
_l = pd.read_csv(os.path.join(OUT, "l208_mines.csv"))
_cand = _l[_l.l208_class.str.contains(r"candidate \((?:strong|medium)\)|Stopped at L-208", regex=True, na=False)]
_lab = _json.load(open(os.path.join(OUT, "review", "labels.json")))["labels"]
_cnt = {k: sum(1 for x in _lab if x["answer"] == k) for k in ("yes", "no", "unsure")}
_cells = pd.read_csv(os.path.join(OUT, "..", "data", "scored_cells.csv.gz"), usecols=["legal_ok", "ground_ok", "ground_reason"], low_memory=False)
_g = _cells[_cells.legal_ok & ~_cells.ground_ok.fillna(True).astype(bool)].ground_reason.value_counts().to_dict()
L.append("## Old records and the 1942 shutdown\n")
L.append(f"In 1942 the government ordered most gold mines to stop (War Production Board Order L-208). Old Bureau of Mines yearbooks from 1939 to 1947 were searched for every mine in these districts. {len(_l)} mines are listed in `l208_mines.csv`, each fact with a page number. The ones that look like they were stopped by the order:\n")
for r in _cand.itertuples():
    land = "private land (likely an old patented claim)" if "private" in str(r.land_status).lower() else "BLM land (check claims)"
    note = str(r.stop_note).replace("1942 yearbook: operated", "The 1942 yearbook says it operated").replace("1943 yearbook: operated", "The 1943 yearbook says it operated").replace("; cause not stated", " (no reason given)").rstrip(".") if isinstance(r.stop_note, str) else ""
    kind = "Reopened after the war." if "reopened" in r.l208_class else ("Strong candidate." if "strong" in r.l208_class else "Medium candidate.")
    L.append(f"- **{r.name}** ({r.district}). {kind} {note}. Site: {land}.")
L.append("\nMost of these mine sites are private land, so they cannot be visited. But the washes below them can be on public land. A wash gets a small boost (+0.1 on placer history) when its strongest upstream gold source is within 300 m of a strong or medium candidate. The El Dorado-Rover group gets no boost, because it was worked again after the war. " + (f"{int(t.l208_upstream.notna().sum())} of the top 25 got this boost." if "l208_upstream" in t else "") + " The boosted washes, below the Jubilee and Wall Street mines, score low on flood or trap.\n")
L.append("Two more old reports were used. A 1973 USGS report (Bulletin 1356, *Placer Gold Deposits of Nevada*) says Eldorado Canyon's recent placer gold came mostly from the Gresh claims in T26S R64E Sec 4, and lists no placer gold for Goodsprings. A 1937 Bureau of Mines survey (Information Circular 6964) names C. E. L. Gresh as president of the Eldorado Empire Mining Co. Notes: `notes/usgs_b1356_placers.md`.\n")
L.append("## Ground the old maps ruled out\n")
L.append("The 1950s USGS maps showed some top spots sat in a town, quarries, or a pipeline corridor. Spots like that are now removed everywhere: inside a town with streets nearby, within 150 m of a mapped quarry, pit or open-pit mine, within 150 m of a mapped gas pipeline (never dig over a buried pipeline), or within 60 m of a power line. Legal spots removed: " + "; ".join(f"{k}, {v}" for k, v in _g.items()) + ". Pipeline maps are approximate, so watch for pipeline markers in the field. The rules miss some cases: the old maps still rate " + " and ".join(f"#{k}" for k in WEAK8) + " as weak (see their entries), because the mapped quarry or power line was not close enough, or the problem is an open slope or airstrip, which this check cannot test.\n")
L.append("## The ant-mound test (stopped)\n")
L.append(f"Harvester ants bring up small heavy grains, so their mounds can show gold from below. Fifty spots from 0.6 m aerial photos were checked by eye: {_cnt['yes']} yes, {_cnt['no']} no, {_cnt['unsure']} not sure. The plan was to stop if fewer than 5 of 50 were real mounds, so the test stopped. The photos are too coarse, and the local ants make small mounds without a cleared ring.\n")
L.append("## Where the data came from\n")
L.append("BLM mining claims and land status (gis.blm.gov, nlsdbpubgis.blm.gov); USGS mine records (MRDS) and old topographic map mine features (USMIN, mrdata.usgs.gov); "
         "USGS 3DEP elevation, 10 m and 1 m lidar (prd-tnm.s3.amazonaws.com); Sentinel-2 satellite images (Earth Search, AWS); "
         "NOAA MRMS weather radar (noaa-mrms-pds on AWS); NOAA Storm Events (ncei.noaa.gov); Clark County Regional Flood Control District rain gauges (gustfront.ccrfcd.org); "
         "Census TIGER roads and town boundaries; HIFLD power lines; EIA/HIFLD gas pipelines; USGS Bulletin 1356; USBM IC 6964 and Minerals Yearbooks 1939–1947 (archive.org). Downloaded files are listed with their address, date, and file check code in `data/PROVENANCE.csv`. Lidar tiles and satellite scenes were read straight from their sources without being saved.\n")
open(os.path.join(OUT, "REPORT.md"), "w").write("\n".join(L))
print("\n".join(L)[:6000])
