"""Build out/project_pack/: files to upload into a Claude Project ("Hunting Gold with AI").
Re-run after any re-rank: python3 src/project_pack.py"""
import os, shutil, datetime, pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), ".."); OUT = os.path.join(ROOT, "out"); P = os.path.join(OUT, "project_pack"); os.makedirs(P, exist_ok=True)
FIELD = "https://claude.ai/artifact/WQUAb3UvWcTo15K2tFZh9o"; SERIES = "https://claude.ai/artifact/VTejW2kmEvmtjejExpQqMx"
t = pd.read_csv(os.path.join(OUT, "targets.csv")); rv = pd.read_csv(os.path.join(OUT, "oldmap_review.csv"))
om = {(round(a, 4), round(b, 4)): (v, n) for a, b, v, n in zip(rv.lat, rv.lon, rv.map_verdict, rv.map_note)}
def verdict(r): return om.get((round(r.lat, 4), round(r.lon, 4)), ("not checked", ""))
today = datetime.date.today().strftime("%B %-d, %Y")

instructions = f"""# Project instructions (paste into the Claude Project's "Instructions" box)

You are helping Makoto with two linked things:
1. **placer-scout**: an AI-built tool that ranks desert washes in southern Clark County, Nevada (Goodsprings, Eldorado Canyon/Nelson, Searchlight) where flash floods may have moved placer gold below old mines. The code, data and full history live in a GitHub repo (branch `placer-scout-plan`), worked on in Claude Code. This project holds summaries only.
2. **"Hunting Gold with AI"**: a podcast and video series on the Dopest AI channel that documents the build and the field hunt, to show how Makoto works with AI and to sell his product and design services.

Rules:
- **Never put exact locations in anything public** (scripts, show notes, thumbnails, captions). District-level only. Coordinates in these files are for private field use.
- **Use Google only through links.** Never copy Google imagery into project files or videos made from project data.
- **Be honest about the odds.** The tool is "a rough guide, not a gold prediction." Show failures (0 of 50 ant mounds, the radar running 1.5x high) as well as wins.
- **Get the facts right.** October 2026 was Las Vegas's *second-wettest October on record* (1.31 in; record 1.45 in, 2005), not "record rain." Earthquakes: over 300 in Nevada this year, the biggest swarm near Reno, a cluster near Area 51, almost none in the gold districts.
- **Respect land and people.** Check BLM land status and claims before any visit. Spirit Mountain / Avi Kwa Ame is sacred and a national monument: no treasure-hunt framing there. Keep clear of old cemeteries. Never show anyone picking up artifacts.
- **Safety lines stay in:** never enter old mine shafts; never work a wash when storms are possible; treat old mill waste as possibly holding mercury; never dig over a buried pipeline.
- **Data or model changes** (re-ranking, new layers, map updates) go back to Claude Code on the repo. Here, say what to ask for there.
- Write in plain English, about 9th-grade level. Short sentences.

Key links: field plan {FIELD} · series plan and episode 1 script {SERIES}
"""
open(os.path.join(P, "00_INSTRUCTIONS.md"), "w").write(instructions)

rows = []
for _, r in t.head(8).iterrows():
    v, n = verdict(r)
    rows.append(f"| {int(r['rank'])} | {r.district} | {str(r.top_source_name).replace("|", "on")} | {r.score:.3f} | {v} | {r.lat:.5f}, {r.lon:.5f} | {r.plss.replace('Mount Diablo Meridian ', '')} |")
best = [f"#{int(r['rank'])} ({r.district}, below {str(r.top_source_name).replace("|", "on")})" for _, r in t.head(8).iterrows() if verdict(r)[0] == "strong"]
weak = [f"#{int(r['rank'])}" for _, r in t.head(8).iterrows() if verdict(r)[0] == "weak"]
brief = f"""# Project brief: placer-scout and "Hunting Gold with AI"

*Generated {today} from the repo (`src/project_pack.py`). Private: contains coordinates.*

## What it is
An AI agent (Claude Code) built a tool that scores every desert wash cell in southern Clark County, Nevada. It looks for spots where a flash flood could have dropped gold below an old mine. Score = **gold source** (a recorded gold mine, prospect, mill or dump within 2 km upstream) × **flood** (biggest one-day storm since 2000, radar and gauges, plus this fall's storms) × **gold trap** (side-wash junction, widening or slope break, checked with 1 m lidar) × **placer history** (old government reports). The legal gate drops private land, active claims, wilderness, national monuments and Park Service land. A ground check drops towns, quarries and pits, pipeline corridors and power lines.

## Current top 8
| # | District | Strongest gold source upstream | Score | 1950s map check | Lat, lon (private) | Land-survey address |
|---|---|---|---|---|---|---|
{chr(10).join(rows)}

**Best bets (real washes below named gold mines on the 1950s maps):** {", ".join(best)}.
**Look from the road or skip:** {", ".join(weak)} (the old maps show an airstrip, quarries, or an open slope).
Re-check the BLM claim map (MLRS) for any spot the week before going. #2 has an active claim about 5 m away and an old cemetery on the bank.

## Key findings so far
- **1942 shutdown:** War Production Board Order L-208 stopped gold mines in Dec 1942. Yearbooks show Techatticup and Jubilee stopped Dec 1, 1942; Wall Street June 18, 1943; El Dorado-Rover Dec 8, 1942 (reopened after the war). Most of these mine sites are private now.
- **Old reports:** USGS Bulletin 1356 (1973) says Eldorado Canyon's recent placer gold came mostly from the "Gresh Group" claims (T26S R64E Sec 4), and lists no placer gold for Goodsprings. A 1937 Bureau of Mines survey (IC 6964) names C. E. L. Gresh as president of the Eldorado Empire Mining Co. The Gresh section itself now falls inside the Nelson town grid; target #2 is the main canyon wash just downstream.
- **Goodsprings caution:** 10 of the top 25 are in Goodsprings, which has no recorded placer gold. Treat them as lower confidence.
- **Rain:** Las Vegas October 2026 = 1.31 in, 2nd wettest of 90 Octobers since 1937. Aug–Oct as a whole ranked about 15th of 78. Radar reads about 1.5x high against the county gauges.
- **Earthquakes:** 341 Nevada quakes M2.5+ in the past year; 42% near Silver Springs (Reno); a cluster of 37 within 100 km of Area 51; none of that size in the gold districts. Quakes are not opening new ground here.
- **Ant-mound test:** stopped by its own rule (0 yes, 24 no, 26 unsure of 50 clips). The 0.6 m photos are too coarse.
- **Roadside hunch (I-15, mile 122.5):** the pale chute in the Soda Mountains was matched by computer to 35.1196, -116.3020: wind-blown sand in a wilderness area, no gold source. Good "hunch checker" short.

## Podcast status
- Series plan, 8-episode lineup, episode 1 script with the origin story (*The Weight*, *Landman*), fact-check box, and animation list: {SERIES}
- Animation prototypes (vertical MP4s in the repo, `out/animations/`): storm replay (Oct 2026) and hunch checker (I-15 chute).
- Editing plan: record, then AI Producer by OpusClip for transcript, rough cut, captions; vidIQ for titles and thumbnails. Ask before spending credits.

## Open items
- Field day once the washes dry: drone and walk-in at the best bets; Gresh-section scout from public ground only.
- Pull final October storm totals for the top 8.
- Record episode 1; build animation #9 (earthquake year) and #5 (1942 lights out).
- Optional: UNLV Special Collections search for "Gresh", Eldorado Canyon placer photos and claim maps.
- Parked: 3D map view with Google links only.

## Where things live
- Field plan (private page): {FIELD}
- Repo outputs: `out/targets.csv`, `out/map.html`, `out/REPORT.md`, `out/l208_mines.csv`, `out/notes/`, `out/animations/`.
"""
open(os.path.join(P, "01_PROJECT_BRIEF.md"), "w").write(brief)
for src, dst in (("REPORT.md", "02_REPORT.md"), ("notes/usgs_b1356_placers.md", "03_old_records_notes.md"), ("notes/rain_record_check.md", "04_rain_record_check.md")):
    shutil.copy(os.path.join(OUT, src), os.path.join(P, dst))
t.head(25)[["rank", "district", "lat", "lon", "score", "f_source", "f_flood", "f_trap_lidar", "f_hist", "top_source_name", "plss", "nearest_exclusion", "nearest_exclusion_m", "boundary_risk"]].to_csv(os.path.join(P, "05_top25_private.csv"), index=False)
open(os.path.join(P, "README.md"), "w").write(f"""# Claude Project pack

1. In Claude, create a Project named **Hunting Gold with AI**.
2. Paste the text of `00_INSTRUCTIONS.md` into the project's **Instructions**.
3. Upload `01_PROJECT_BRIEF.md` through `05_top25_private.csv` as **project knowledge**.
4. After a re-rank in Claude Code, run `python3 src/project_pack.py`, then replace the knowledge files.

Built {today}. Files 01 and 05 contain coordinates; keep the project private.
""")
print(sorted(os.listdir(P)))
