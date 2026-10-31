"""Phase 2 Step A2-A6: build out/l208_mines.csv from hand-read Minerals Yearbook passages.
Every production record carries (volume, printed page, scan leaf, verbatim OCR quote); the script refuses to run if a quote
is not found on that page. Classification follows the Phase 2 spec fix (see IMPLEMENTATION_PLAN.md)."""
import os, re, json
import pandas as pd, geopandas as gpd
from shapely.ops import transform

ROOT = os.path.join(os.path.dirname(__file__), ".."); DATA = os.path.join(ROOT, "data"); L = os.path.join(DATA, "l208"); OUT = os.path.join(ROOT, "out")
norm = lambda s: re.sub(r"\s+", " ", s)
# volume key -> (archive.org identifier, data year it reports)
VOL = {"myb1939": ("pub_usgov-minerals-yearbook_1939", 1938), "myb1940": ("pub_usgov-minerals-yearbook_1940", 1939),
       "rev1940": ("dli.ernet.205783", 1940), "myb1941": ("pub_usgov-minerals-yearbook_1941", 1941), "myb1942": ("pub_usgov-minerals-yearbook_1942", 1942),
       "myb1943": ("pub_usgov-minerals-yearbook_1943", 1943), "myb1945": ("pub_usgov-minerals-yearbook_1945", 1945),
       "myb1946": ("pub_usgov-minerals-yearbook_1946", 1946), "myb1947": ("pub_usgov-minerals-yearbook_1947", 1947)}
# (volume, printed page, mine key, gold: yes / not stated / uncertain, quotes that must appear on that page)
E = [
 ("myb1939", "403", "paden", "yes", ["Paden mine", "189 tons of smelting ore which contained 2 ounces of gold"]),
 ("myb1939", "403", "rover", "yes", ["The El Dorado Rover Mining Co. worked the Flagstaff, Rover, and Skylark groups throughout 1938", "a large quantity of gold-silver ore was treated"]),
 ("myb1939", "403", "techatticup", "yes", ["The Diamond Gold Mining Co., which operated the Techatticup mine", "gold-lead concentrate"]),
 ("myb1939", "403", "wallstreet", "not stated", ["W. W. Hartman at the Wall Street mine was treated by amalgamation and flotation"]),
 ("myb1939", "403", "blossom", "yes", ["Lessees produced a substantial quantity of gold ore at the Blossom mine"]),
 ("myb1939", "403", "duplex", "uncertain", ["The Duplex mine was worked by lessees throughout 1938", "151 ounces of td 169 ounces of silver"]),
 ("myb1939", "403", "mm", "not stated", ["Lessees shipped ore from the M & M mine to custom cyanide mills"]),
 ("myb1939", "403", "quartette", "not stated", ["tette mine shipped a substantial quantity of ore to smelters and custom mills"]),
 ("myb1939", "403", "keystone", "not stated", ["treated 1 ,020 tons of ore from the Barefoot mine by amalgamation and flotation"]),
 ("myb1939", "389", "chiquita", "yes", ["Ten leading gold producers in Nevada in 1988", "Chiquita", "Yellow Pine"]),
 ("myb1940", "385", "paden", "yes", ["Lessees of the Paden mine in 1939", "129 tons of ore which contained 11 ounces of gold"]),
 ("myb1940", "385", "techatticup", "not stated", ["The Diamond Gold Mining Co. worked the Jubilee and Techatticup mines throughout 1939"]),
 ("myb1940", "385", "jubilee", "not stated", ["The Diamond Gold Mining Co. worked the Jubilee and Techatticup mines throughout 1939"]),
 ("myb1940", "385", "oroplata", "not stated", ["The Oro Plata mine was active."]),
 ("myb1940", "385", "rover", "yes", ["operated the Rand, Bell, and Rover groups", "27,375 tons of company ore yielded 4,560 ounces of gold"]),
 ("myb1940", "385", "wallstreet", "not stated", ["W. W. Hartman operated the Wall Street mine throughout the year"]),
 ("myb1940", "386", "duplex", "yes", ["A lessee on the Duplex mine in 1939", "29 tons of smelting ore which contained 147 ounces of gold"]),
 ("myb1940", "386", "quartette", "not stated", ["The Calumet Gold Mines Co. worked the Quartette mine from January 1 to November 1"]),
 ("myb1940", "386", "chiquita", "yes", ["The Chiquita Mining Co., Ltd., operated the Chiquita mine throughout 1939", "By amalgamation, 1,050 ounces of gold"]),
 ("myb1940", "386", "keystone", "yes", ["The Barefoot Lease operated the Keystone-Barefoot mine throughout the year", "1,215 ounces of gold"]),
 ("rev1940", "394", "rover", "yes", ["operated the Rand, Quaker City, Magnolia, Poppy, Crown, Nevada- Eagle, and Cross mines throughout 1940", "6,044 ounces of gold"]),
 ("rev1940", "394", "oroplata", "yes", ["The Oro Plata (Belmont Phoenix) mine", "220 ounces of gold"]),
 ("rev1940", "394", "techatticup", "not stated", ["The Diamond Gold Mining Co. operated the Techatticup, Jubilee, and Red Butte mines throughout 1940"]),
 ("rev1940", "394", "jubilee", "not stated", ["The Diamond Gold Mining Co. operated the Techatticup, Jubilee, and Red Butte mines throughout 1940"]),
 ("rev1940", "394", "redbutte", "not stated", ["The Diamond Gold Mining Co. operated the Techatticup, Jubilee, and Red Butte mines throughout 1940"]),
 ("rev1940", "394", "wallstreet", "not stated", ["W. W. Hartman worked the Wall Street mine"]),
 ("rev1940", "394", "blossom", "not stated", ["The Blossom mine was productive in 1940."]),
 ("rev1940", "394", "quartette", "yes", ["Lessees at the Quartette mine shipped 533 tons of ore", "204 ounces of gold"]),
 ("rev1940", "394", "valley", "not stated", ["F. P. Jackson worked the Valley"]),
 ("rev1940", "395", "chiquita", "not stated", ["operated the CMquita mine and the 100-ton cyanide plant"]),
 ("rev1940", "395", "keystone", "yes", ["worked the Keystone- Barefoot mine", "1,134 ounces of gold"]),
 ("myb1941", "404", "rover", "not stated", ["Magnolia, Crown, and Névada Eagle groups of claims throughout 1941"]),
 ("myb1941", "404", "occidental", "yes", ["Gold-silver ore was shipped to a smelter from the Occidental mine."]),
 ("myb1941", "404", "oroplata", "yes", ["Oro Plata (Belmont Phoenix) mine contained 66 ounces of gold"]),
 ("myb1941", "404", "techatticup", "not stated", ["The Diamond Gold Mining Co. operated the Techatticup, Jubilee, and Red Butte mines throughout 1941"]),
 ("myb1941", "404", "jubilee", "not stated", ["The Diamond Gold Mining Co. operated the Techatticup, Jubilee, and Red Butte mines throughout 1941"]),
 ("myb1941", "404", "redbutte", "not stated", ["The Diamond Gold Mining Co. operated the Techatticup, Jubilee, and Red Butte mines throughout 1941"]),
 ("myb1941", "404", "wallstreet", "not stated", ["W. W. Hartman operated the Wall Street mine."]),
 ("myb1941", "405", "blossom", "not stated", ["Lessees operated the Blossom mine during 1941."]),
 ("myb1941", "405", "goodhope", "not stated", ["H. H. Lang worked the Good Hope mine."]),
 ("myb1941", "405", "mm", "not stated", ["W. H. Kelsey operated the M & M property."]),
 ("myb1941", "405", "montecarlo", "not stated", ["The Monte Carlo group was active."]),
 ("myb1941", "405", "valley", "not stated", ["shipped ore from the Valley mine to a custom mill and a smelter"]),
 ("myb1941", "405", "chiquita", "not stated", ["The Chiquita Mining Co., Ltd., operated the Chiquita mine."]),
 ("myb1941", "405", "goldenchariot", "yes", ["operated the Golden Chariot mine", "yielded 27 ounces of gold"]),
 ("myb1941", "405", "keystone", "not stated", ["ated the Hoosier and Keystone-Barefoot mines."]),
 ("myb1942", "430", "rover", "yes", ["from January 1 to December 8, 1942", "2,641 ounces of gold"]),
 ("myb1942", "430", "techatticup", "not stated", ["chatticup and Jubilee mines from January 1 to December 1"]),
 ("myb1942", "430", "jubilee", "not stated", ["chatticup and Jubilee mines from January 1 to December 1"]),
 ("myb1942", "430", "wallstreet", "yes", ["operated the Wall Street mine throughout the year; gold ore was treated"]),
 ("myb1943", "421", "wallstreet", "yes", ["operated the Wall Street mine from January 1 to June 18, 1943", "628 ounces of gold"]),
 ("myb1943", "421", "blossom", "yes", ["containing 110 ounces of gold and 1,077 ounces of silver, produced at the Blossom mine during 1943"]),
 ("myb1945", "416", "blossom", "yes", ["shipped gold ore to a smelter from the Blossom mine during 1945"]),
 ("myb1946", "1484", "rover", "not stated", ["The Patimac Metals Co. operated the Eldorado, Rover, Crown, and Rambler groups of claims in 1946."]),
 ("myb1946", "1484", "blossom", "yes", ["Lessees shipped gold ore to smelters from the Blossom mine during 1946."]),
 ("myb1946", "1484", "quartette", "yes", ["operated the Quartette mine during July and August 1946; gold-silver ore"]),
 ("myb1946", "1484", "clementina", "yes", ["operated the Clementina mine from April 1 through December 20, 1946", "22 tons of gold ore"]),
 ("myb1947", "1467", "rover", "yes", ["operated claims in the Eldorado-Rover group during 1947, treating the gold-silver dump ore and old tailings by cyanidation"]),
 ("myb1947", "1467", "blossom", "yes", ["Blossom (Coyote) mine in 1947, treating gold ore by cyanidation"]),
]
# mine key -> (display name, district, location record (dataset, id) or None)
MINES = {
 "rover": ("El Dorado-Rover group (Rover, Rand, Quaker City, Magnolia, Crown, Nevada Eagle, et al.)", "Eldorado Canyon", ("MRDS", "10246687")),
 "techatticup": ("Techatticup mine", "Eldorado Canyon", ("MRDS", "10246422")), "jubilee": ("Jubilee mine", "Eldorado Canyon", ("MRDS", "10037162")),
 "redbutte": ("Red Butte mine", "Eldorado Canyon", None), "wallstreet": ("Wall Street mine", "Eldorado Canyon", ("MRDS", "10037164")),
 "oroplata": ("Oro Plata (Belmont-Phoenix) mine", "Eldorado Canyon", ("MRDS", "10135662")), "occidental": ("Occidental mine", "Eldorado Canyon", ("MRDS", "10270039")),
 "blossom": ("Blossom (Coyote) mine", "Searchlight", ("MRDS", "10046988")), "goodhope": ("Good Hope mine", "Searchlight", ("MRDS", "10037138")),
 "mm": ("M & M mine", "Searchlight", ("MRDS", "10109507")), "montecarlo": ("Monte Carlo group", "Searchlight", ("MRDS", "10174065")),
 "valley": ("Valley mine", "Searchlight", None), "quartette": ("Quartette mine", "Searchlight", ("MRDS", "10037033")),
 "duplex": ("Duplex mine", "Searchlight", ("MRDS", "10046990")), "chiquita": ("Chiquita mine", "Yellow Pine (Goodsprings)", ("USMIN", "Chiquita Mine")),
 "keystone": ("Keystone-Barefoot mine", "Yellow Pine (Goodsprings)", ("MRDS", "10037224")),
 "goldenchariot": ("Golden Chariot mine", "Yellow Pine (Goodsprings)", ("MRDS", "10038077")),
 "paden": ("Paden mine", "Crescent", None), "clementina": ("Clementina mine", "Yellow Pine (Goodsprings)", ("MRDS", "10037211")),
}

def page_text(vol, page):
    if vol == "rev1940":
        hits = json.load(open(os.path.join(L, "myb_review1940_hits.json")))["hits"]
        ts = [h for h in hits if h["printed_page"] == page]
        return norm(" ".join(h["text"] for h in ts)), (ts[0]["leaf"] if ts else None)
    y = int(vol[3:]); d = json.load(open(os.path.join(L, f"myb_{y}.json")))
    ps = [p for p in d["pages"] if p["printed_page"] == page]
    return (norm(ps[0]["text"]), ps[0]["leaf"]) if ps else ("", None)

rows, bad = [], []
for vol, page, key, gold, quotes in E:
    t, leaf = page_text(vol, page)
    missing = [q for q in quotes if norm(q) not in t]
    if missing: bad.append((vol, page, key, missing))
    ident, dy = VOL[vol]
    rows.append({"mine_key": key, "data_year": dy, "gold": gold, "source": f"USBM Minerals Yearbook ({'Review of 1940' if vol == 'rev1940' else vol[3:]}), p. {page}",
                 "archive_id": ident, "scan_leaf": leaf, "url": f"https://archive.org/details/{ident}/page/n{leaf}" if leaf is not None else f"https://archive.org/details/{ident}",
                 "quote": " … ".join(quotes)})
if bad:
    for b in bad: print("QUOTE NOT FOUND:", b)
    raise SystemExit("refusing to build: unverified quotes")
ev = pd.DataFrame(rows); ev.to_csv(os.path.join(L, "l208_evidence.csv"), index=False)
print("evidence rows", len(ev), "all quotes verified on their cited pages")

# --- locations ---
swap = lambda g: transform(lambda x, y, z=None: (y, x), g)
mrds = gpd.read_file(os.path.join(DATA, "mrds_box.gml")); mrds["geometry"] = mrds.geometry.apply(swap)
usp = gpd.read_file(os.path.join(DATA, "usmin_points.gml")); usp["geometry"] = usp.geometry.apply(swap)
def locate(rec):
    if rec is None: return None, None, "not found in MRDS/USMIN"
    ds, i = rec
    g = mrds[mrds.dep_id.astype(str) == i] if ds == "MRDS" else usp[usp.ftr_name == i]
    p = g.geometry.iloc[0]
    return p.y, p.x, (f"MRDS dep_id {i}: {g.site_name.iloc[0]} ({g.url.iloc[0]})" if ds == "MRDS" else f"USMIN topo feature '{i}' ({g.gml_id.iloc[0]})")

# --- land / claim status at the mine point ---
sma = {n: gpd.read_file(os.path.join(DATA, f"sma_{n}.geojson")) for n in ("BLM", "NPS", "USFS", "PrivateOrUnknown", "State", "Local", "USBR", "OtherFederal", "BIA")}
nca = gpd.read_file(os.path.join(DATA, "nca_blm.geojson")); wild = gpd.read_file(os.path.join(DATA, "wilderness_blm.geojson"))
act = gpd.read_file(os.path.join(DATA, "claims_active.geojson")); clo = gpd.read_file(os.path.join(DATA, "claims_closed.geojson"))
for g in list(sma.values()) + [nca, wild, act, clo]: g["geometry"] = g.geometry.make_valid()
def status(lat, lon):
    if lat is None: return "unknown (no location)", "", ""
    P = gpd.GeoDataFrame(geometry=gpd.points_from_xy([lon], [lat]), crs=4326)
    inside = lambda g: len(gpd.sjoin(P, g[["geometry"]], predicate="within")) > 0
    land = next((n for n, g in sma.items() if len(g) and inside(g)), "unmapped")
    if land == "PrivateOrUnknown": land = "EXCLUDED: private (likely patented mining claim; verify in GLO records)"
    elif land != "BLM": land = f"EXCLUDED: {land}"
    else:
        hit = gpd.sjoin(P, nca[["NCA_NAME", "geometry"]], predicate="within")
        land = f"EXCLUDED: BLM monument/NCA ({hit.NCA_NAME.iloc[0]})" if len(hit) else ("EXCLUDED: BLM wilderness" if inside(wild) else "BLM (likely open - verify)")
    a = gpd.sjoin(P, act[["CSE_NR", "BLM_PROD", "geometry"]], predicate="within"); c = gpd.sjoin(P, clo[["CSE_NR", "geometry"]], predicate="within")
    claim = ("ACTIVE claim " + ", ".join(sorted(set(a.CSE_NR)))[:120]) if len(a) else ("closed claims only" if len(c) else "no claim mapped")
    return land, claim, ", ".join(sorted(set(a.CSE_NR)))

# --- classify ---
out = []
for key, (name, dist, rec) in MINES.items():
    e = ev[ev.mine_key == key]
    active = sorted(set(e.data_year)); gold_yrs = sorted(set(e[e.gold == "yes"].data_year))
    last = max(active); a42 = 1942 in active
    stop_note = ""
    if key in ("rover",): stop_note = "1942 yearbook: operated 'from January 1 to December 8, 1942' (L-208 took effect Dec 8, 1942)"
    if key in ("techatticup", "jubilee"): stop_note = "1942 yearbook: operated 'from January 1 to December 1' 1942"
    if key == "wallstreet": stop_note = "1943 yearbook: operated 'from January 1 to June 18, 1943'; cause not stated"
    if a42 and last <= 1943 and key != "wallstreet": cls = "L-208 candidate (strong): active in 1942, stopped Dec 1942, no record through 1947"
    elif a42 and last <= 1943: cls = "L-208 candidate (medium): active 1942, stopped mid-1943, cause not stated"
    elif a42 and last >= 1945: cls = "Stopped at L-208, reopened after the war"
    elif last == 1941: cls = "Possible (uncertain): last yearbook record 1941; the 1942 yearbook is silent, which does not prove a shutdown"
    elif last >= 1945: cls = "Not a candidate: produced after 1945"
    else: cls = f"Not a candidate: last yearbook record {last}, before the war"
    lat, lon, loc_src = locate(rec); land, claim, _ = status(lat, lon)
    out.append({"name": name, "district": dist, "lat": None if lat is None else round(lat, 5), "lon": None if lon is None else round(lon, 5),
                "location_source": loc_src, "years_recorded_active": " ".join(map(str, active)), "years_gold_reported": " ".join(map(str, gold_yrs)) or "none stated",
                "last_recorded_year": last, "last_production_after_1945": "yes" if last >= 1946 else "none recorded (1946-47 yearbooks)",
                "l208_class": cls, "stop_note": stop_note, "land_status": land, "claim_status": claim,
                "source_pages": "; ".join(f"{r.data_year}: {r.source}" for r in e.itertuples()),
                "evidence_file": "data/l208/l208_evidence.csv"})
T = pd.DataFrame(out).sort_values(["l208_class", "district", "name"])
T.to_csv(os.path.join(OUT, "l208_mines.csv"), index=False)
pd.set_option("display.width", 250)
print(T[["name", "district", "years_recorded_active", "years_gold_reported", "last_recorded_year", "l208_class", "land_status", "claim_status"]].to_string())
