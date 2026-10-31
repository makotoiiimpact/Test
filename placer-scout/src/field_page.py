"""Build out/field/field_plan.html: phone-friendly field guide (drive, launch, drone shot list, walk, on-foot checks, hazards)
from out/field/field_plan.json (src/field_plan.py). Static page: no runtime capabilities."""
import os, json, html, urllib.parse
ROOT = os.path.join(os.path.dirname(__file__), ".."); OUT = os.path.join(ROOT, "out", "field")
R = json.load(open(os.path.join(OUT, "field_plan.json")))
E = html.escape
ft = lambda m: f"{m * 3.281:,.0f} ft"
nav = lambda la, lo: "https://www.google.com/maps/dir/?api=1&" + urllib.parse.urlencode({"destination": f"{la},{lo}", "travelmode": "driving"})
pin = lambda la, lo: "https://www.google.com/maps/search/?api=1&" + urllib.parse.urlencode({"query": f"{la},{lo}"})
ll = lambda la, lo: f"{la:.5f}, {lo:.5f}"

TRIPS = {
 "A · Nelson / Eldorado": ("Start here. Closest to Las Vegas, all stops are short walks, and it settles the ant-mound question while checking the #1 target.",
   "From Henderson, take US-95 south toward Searchlight, then turn east on NV-165 (Nelson Road) toward Nelson. The stops sit along NV-165 and the dirt roads north and south of it, before the road drops into Eldorado Canyon. Lower Eldorado Canyon and the river are Lake Mead NRA: no drones there."),
 "B · Searchlight": ("Most targets in one place, nearly all easy walks. Several sit right against private land and old shafts, so read each card's warnings.",
   "Take US-95 south from Henderson to Searchlight. The targets are on the edge of town and along Cottonwood Cove Road east of US-95. Avi Kwa Ame National Monument surrounds this area: stay on the targets listed, which are outside it."),
 "C · Goodsprings": ("Longer walks and rougher ground. Do it after A and B, early in the day, with plenty of water.",
   "Take I-15 south to Jean, then NV-161 west to Goodsprings. Most targets are on dirt roads in the hills west and north of town. Some need a high-clearance vehicle; #16 and #18 are long hikes."),
 "D · Other": ("One target at the south edge of the Las Vegas valley, near Blue Diamond.", "Off S Fort Apache Rd at the south edge of the valley."),
}

def flags(r):
    f = []
    if r.get("private_m", 9e9) < 100: f.append(("warn", f"Private land {r['private_m']} m away: stay on the BLM side"))
    if r.get("active_claim_m", 9e9) < 150: f.append(("warn", f"Active mining claim {r['active_claim_m']} m away: don't pan or dig on it"))
    if r.get("shafts_adits_300m", 0) > 0: f.append(("danger", f"{r['shafts_adits_300m']} mapped shafts/adits within 300 m (nearest {r['nearest_shaft_m']} m)"))
    if r.get("nps_m", 9e9) < 2000: f.append(("warn", f"Lake Mead NRA {r['nps_m']:,} m away: no drone flights inside it"))
    if r.get("wilderness_m", 9e9) < 800: f.append(("warn", f"Wilderness {r['wilderness_m']} m away: don't launch or land inside it"))
    if r.get("monument_m", 9e9) < 300: f.append(("warn", f"Avi Kwa Ame monument {r['monument_m']} m away: confirm its rules first"))
    if r.get("launch_road_type") == "4WD / dirt track": f.append(("info", "Last stretch is a 4WD / dirt track"))
    return f

def card(r):
    code = r["trip"][0] + str(int(r["stop_no"]))
    dz = r["elev_target_m"] - r["elev_launch_m"]
    alt_note = (f"The target is {abs(dz)} m ({ft(abs(dz))}) {'above' if dz > 0 else 'below'} the launch point. The drone's altitude reads from launch, so "
                f"{'add' if dz > 0 else 'subtract'} that to get height above the wash.") if abs(dz) >= 8 else "The target is about level with the launch point."
    vs, ve = r["video_start"], r["video_end"]
    fl = "".join(f'<span class="flag {k}">{E(t)}</span>' for k, t in flags(r))
    if r["kind"] == "clips":
        body = f"""
<div class="block"><h4>Drone: one photo per spot</h4><ol>
<li>Load <b>clip_spots.gpx</b> (50 waypoints) into your phone or flight app.</li>
<li>At each spot, hover about <b>35 m</b> up and take one <b>straight-down</b> photo. Name or note it by clip number.</li>
<li>For any spot that shows a round bare patch, drop to <b>15 m</b> and take two more straight-down photos.</li></ol>
<p class="small">The spots spread over about 1.2 × 1.5 km, so work them in a loop and expect 2–3 batteries.</p></div>
<div class="block"><h4>On foot</h4><p>Walk to any spot that looks like a clearing. A harvester-ant nest has a bare disc, a central hole and ant traffic. Look, don't dig: these ants sting. Run a magnet or detector over the cleared surface and the tailings ring around the hole.</p></div>"""
    else:
        body = f"""
<div class="block"><h4>Drone shot list</h4><ol>
<li><b>Overview.</b> Climb to about <b>60 m</b> over the target. Take one straight-down photo and one angled shot looking upstream.</li>
<li><b>Wash video.</b> Start upstream at <a href="{pin(vs[0], vs[1])}" target="_blank" rel="noopener noreferrer">{ll(*vs)}</a> and fly down the wash to <a href="{pin(ve[0], ve[1])}" target="_blank" rel="noopener noreferrer">{ll(*ve)}</a> (about 350 m). Stay about <b>25 m</b> over the wash, camera 45–60° down, 2–3 m/s. Then fly the same line back at 40 m, camera straight down, a photo every 2 seconds.</li>
<li><b>Close-ups.</b> Hover <b>12–15 m</b> over the target ({E(r.get('trap') or '')}) and take straight-down photos of the junction or bar, plus any rock ribs crossing the channel and dark black-sand streaks.</li></ol>
<p class="small">{E(alt_note)}</p></div>
<div class="block"><h4>On foot</h4><p>Walk to the target only after the flight, and stay on BLM ground. Look for:</p><ul>
<li>bedrock showing in the channel floor;</li>
<li>coarse gravel on the inside of the bend just below the junction;</li>
<li>a debris line from the last flood.</li></ul>
<p>Take <b>3 test pans</b>: just below the junction, at the head of the gravel bar, and from a bedrock crack if you find one. Count the gold colors in each pan and note the black sand.</p></div>"""
    walk = ("right at the road" if r["walk_m"] < 60 else f"{r['walk_m']:,} m ({ft(r['walk_m'])}) walk, {r['climb_m']} m climb")
    score = f'<span class="score">score {r["score"]:.2f}</span>' if r["kind"] == "target" else ""
    return f"""<article class="stop" id="{code}">
<header><span class="code">{code}</span><h3>{E(r['name'])}</h3>{score}</header>
<div class="facts"><div><span class="k">Launch</span><span>{E(r['launch_road'])} ({E(r['launch_road_type'])}) · <span class="mono">{ll(r['launch_lat'], r['launch_lon'])}</span></span></div>
<div><span class="k">Walk</span><span>{walk} · <b class="rate {r['walk_rating']}">{r['walk_rating']}</b></span></div>
<div><span class="k">Target</span><span class="mono">{ll(r['lat'], r['lon'])}</span></div></div>
<div class="links"><a class="btn" href="{nav(r['launch_lat'], r['launch_lon'])}" target="_blank" rel="noopener noreferrer">Navigate to launch</a><a class="btn ghost" href="{pin(r['lat'], r['lon'])}" target="_blank" rel="noopener noreferrer">Target on map</a></div>
{f'<div class="flags">{fl}</div>' if fl else ''}{body}</article>"""

trips = []
for name in TRIPS:
    rs = [r for r in R if r["trip"] == name]
    if not rs: continue
    why, how = TRIPS[name]
    toc = " · ".join(f'<a href="#{r["trip"][0]}{int(r["stop_no"])}">{r["trip"][0]}{int(r["stop_no"])} {E(r["name"].replace("Ant mound clip area (50 spots)", "Clip area"))}</a>' for r in rs)
    trips.append(f"""<section class="trip" id="trip-{name[0]}"><h2>Trip {E(name)}</h2><p class="why">{E(why)}</p><p>{E(how)}</p><p class="toc">{toc}</p>{''.join(card(r) for r in rs)}</section>""")

page = r"""<title>Placer Scout Field Plan</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* layout: one column field guide; trip sections, stop cards, compact fact rows; coordinates in mono */
:root{--bg:#f1ede3;--card:#fbf9f3;--ink:#2a2822;--muted:#6c675a;--line:#d9d1bf;--accent:#8a4b12;--accent-bg:#f2dfc6;--warn:#8a5a00;--warn-bg:#f6e7bf;--danger:#9b2c1f;--danger-bg:#f6d6d0;--info:#3d5a6b;--info-bg:#dde7ec;--ok:#3f6b2f;
--display:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;--body:"Atkinson Hyperlegible",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1c1b17;--card:#25241f;--ink:#ece7da;--muted:#a8a291;--line:#3b3930;--accent:#e2a25c;--accent-bg:#3c2b16;--warn:#e7c066;--warn-bg:#3a3017;--danger:#f19a8c;--danger-bg:#3d211c;--info:#a3c3d3;--info-bg:#22313a;--ok:#9fcb86;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#1c1b17;--card:#25241f;--ink:#ece7da;--muted:#a8a291;--line:#3b3930;--accent:#e2a25c;--accent-bg:#3c2b16;--warn:#e7c066;--warn-bg:#3a3017;--danger:#f19a8c;--danger-bg:#3d211c;--info:#a3c3d3;--info-bg:#22313a;--ok:#9fcb86;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font:16px/1.55 var(--body)}
.wrap{max-width:820px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:22px 56px;display:grid;gap:22px}
h1{font:700 2rem/1.1 var(--display);margin:0;text-wrap:balance}
h2{font:700 1.45rem/1.2 var(--display);margin:0;text-wrap:balance}
h3{font:600 1.15rem/1.2 var(--display);margin:0}
h4{font:600 .82rem var(--display);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 .3rem}
p{margin:.35rem 0;max-width:68ch}ol,ul{margin:.2rem 0;padding-left:1.25rem;display:grid;gap:.3rem;max-width:68ch}
a{color:var(--accent)}
.lede{color:var(--muted);max-width:68ch}
.box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.trip{display:grid;gap:14px;padding-top:6px;border-top:2px solid var(--ink)}
.why{font-weight:700}
.toc{font-size:.9rem;color:var(--muted)}.toc a{white-space:nowrap}
.stop{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;display:grid;gap:12px;min-width:0;scroll-margin-top:12px}
.stop header{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 10px}
.code{font:700 .9rem var(--display);background:var(--ink);color:var(--card);border-radius:4px;padding:1px 7px}
.score{margin-left:auto;font:600 .85rem var(--display);color:var(--muted);font-variant-numeric:tabular-nums}
.facts{display:grid;gap:4px}.facts>div{display:grid;grid-template-columns:4.5rem minmax(0,1fr);gap:8px}
.k{font:600 .78rem var(--display);letter-spacing:.07em;text-transform:uppercase;color:var(--muted);padding-top:2px}
.mono{font:500 .88rem var(--mono);overflow-wrap:anywhere}
.rate{font:600 .78rem var(--display);letter-spacing:.06em;text-transform:uppercase;padding:0 6px;border-radius:4px}
.rate.easy{color:var(--ok);border:1px solid var(--ok)}.rate.moderate{color:var(--warn);border:1px solid var(--warn)}.rate.hard{color:var(--danger);border:1px solid var(--danger)}
.links{display:flex;flex-wrap:wrap;gap:8px}
.btn{font:700 .95rem var(--body);text-decoration:none;padding:.55rem .9rem;border-radius:6px;background:var(--accent);color:var(--card)}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.btn:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.flags{display:flex;flex-wrap:wrap;gap:6px}
.flag{font-size:.86rem;padding:3px 8px;border-radius:5px}
.flag.warn{background:var(--warn-bg);color:var(--warn)}.flag.danger{background:var(--danger-bg);color:var(--danger);font-weight:700}.flag.info{background:var(--info-bg);color:var(--info)}
.block{border-top:1px solid var(--line);padding-top:10px}
.small{font-size:.88rem;color:var(--muted)}
.sheet{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,230px),1fr));gap:8px 18px;margin-top:6px}
.sheet div{border-left:3px solid var(--accent);padding-left:8px}
</style>
<div class="wrap">
<header><h1>Placer Scout field plan</h1>
<p class="lede">Driving, drone and walking plan for the 25 wash targets and the 50 ant-mound clip spots. Each stop has a launch point on a public road, a drone shot list with exact start and stop points, what to check on foot, and warnings for private land, claims and old shafts.</p></header>

<section class="box"><h2>Where to start</h2>
<ol><li><b>Trip A (Nelson) first.</b> It is the closest, the walks are short, and it answers the two biggest open questions in one morning: are the ant "clearings" real, and is the #1 target a real gold trap?</li>
<li><b>Trip B (Searchlight) next.</b> Ten targets, mostly right off the road. Several sit tight against private land and old shafts, so watch the red and amber warnings.</li>
<li><b>Trip C (Goodsprings) last.</b> Longer, rougher walks. Skip #16 and #18 unless you're set up for a real hike.</li></ol>
<p class="small">Bring the files from the chat: <b>field_plan.kml</b> (launch points, targets and wash flight lines for Google Earth or a GPS app), <b>clip_spots.gpx</b> and <b>targets.gpx</b>.</p></section>

<section class="box"><h2>Data that raises confidence</h2>
<p>Record these at every stop. They let me check the model against what's really on the ground and re-weight it.</p>
<div class="sheet">
<div><b>Waypoint and time</b><br>Where you stood, and when.</div>
<div><b>Photo and video file names</b><br>Matched to the stop code (A1, B3…).</div>
<div><b>Trap check</b><br>Is the junction, widening or slope break real? Yes, no or partly.</div>
<div><b>Bedrock</b><br>Exposed in the channel? Depth if you probed.</div>
<div><b>Gravel</b><br>Mostly sand, pea gravel, cobbles or boulders.</div>
<div><b>Pans</b><br>Gold colors in each of 3 pans, plus black sand: none, some or lots.</div>
<div><b>Flood signs</b><br>Debris line height, fresh scour, uprooted brush.</div>
<div><b>Ant nests</b><br>Clip number or waypoint, disc size, ants active or not.</div>
<div><b>Access</b><br>Road condition, gates, signs, claim posts you saw.</div></div>
<p class="small">Zero colors is a useful result too: it tells me which signals to trust less.</p></section>

<section class="box"><h2>Rules and safety</h2><ul>
<li><b>Drone:</b> you need the FAA TRUST certificate. Stay under 400 ft and keep the drone in sight. Check B4UFLY before each trip.</li>
<li><b>No-drone zones:</b> no flights in Lake Mead NRA (Park Service). Don't launch or land inside wilderness. Keep well clear of bighorn sheep and desert tortoises.</li>
<li><b>Panning:</b> hand panning on open BLM land only. Never on an active claim or private land; claim posts and signs override this plan.</li>
<li><b>Old mines:</b> never enter old shafts or tunnels. Stay off dump edges, and walk where you can see the ground.</li>
<li><b>Mill waste:</b> old mill tailings can hold mercury and arsenic. Don't dig in them or breathe their dust, and wash your hands and gear.</li>
<li><b>Weather:</b> no wash work if storms are possible anywhere upstream. Check the NWS Las Vegas forecast that morning.</li>
<li><b>Heat:</b> go early. Bring plenty of water, and tell someone your route; many spots have no cell signal.</li></ul></section>
__TRIPS__
<p class="small">Launch points are the nearest public road to each target, chosen off Park Service land, private land and wilderness. Walks and climbs come from 10 m elevation data, and wash lines from the 10 m flow model, so expect small offsets on the ground. Land status comes from BLM maps; check the claim link in targets.csv before you go.</p>
</div>"""
open(os.path.join(OUT, "field_plan.html"), "w").write(page.replace("__TRIPS__", "".join(trips)))
print("field_plan.html KB", os.path.getsize(os.path.join(OUT, "field_plan.html")) // 1024)
