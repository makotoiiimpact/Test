# Project brief: placer-scout and "Hunting Gold with AI"

*Generated November 2, 2026 from the repo (`src/project_pack.py`). Private: contains coordinates.*

## What it is
An AI agent (Claude Code) built a tool that scores every desert wash cell in southern Clark County, Nevada. It looks for spots where a flash flood could have dropped gold below an old mine. Score = **gold source** (a recorded gold mine, prospect, mill or dump within 2 km upstream) × **flood** (biggest one-day storm since 2000, radar and gauges, plus this fall's storms) × **gold trap** (side-wash junction, widening or slope break, checked with 1 m lidar) × **placer history** (old government reports). The legal gate drops private land, active claims, wilderness, national monuments and Park Service land. A ground check drops towns, quarries and pits, pipeline corridors and power lines.

## Current top 8
| # | District | Strongest gold source upstream | Score | 1950s map check | Lat, lon (private) | Land-survey address |
|---|---|---|---|---|---|---|
| 1 | Goodsprings | Boss Mine | 0.191 | fair | 35.80764, -115.57338 | T25S R57E Sec 03 L 2 |
| 2 | Eldorado Canyon/Nelson | Copper Canyon Mine | 0.133 | strong | 35.70097, -114.82949 | T26S R64E Sec 10 SWNW |
| 3 | Searchlight | Geneva Mill | 0.124 | strong | 35.45579, -114.89042 | T29S R63E Sec 01 L 1 |
| 4 | other | Mine Dump on topo Blue Diamond SE 1972 | 0.122 | weak | 36.04440, -115.29995 | T22S R60E Sec 07 SESE |
| 5 | Eldorado Canyon/Nelson | Eldorado Empire Mining Co. | 0.117 | weak | 35.71088, -114.82764 | T26S R64E Sec 03 NWSW |
| 6 | Goodsprings | Lavina Mine | 0.099 | strong | 35.83995, -115.46764 | T24S R58E Sec 22 L 13 |
| 7 | Goodsprings | Lookout Mine | 0.096 | weak | 35.81727, -115.44681 | T24S R58E Sec 35 SWNW |
| 8 | Goodsprings | Prairie Flower Mine | 0.090 | fair | 35.85866, -115.47588 | T24S R58E Sec 16 L 6 |

**Best bets (real washes below named gold mines on the 1950s maps):** #2 (Eldorado Canyon/Nelson, below Copper Canyon Mine), #3 (Searchlight, below Geneva Mill), #6 (Goodsprings, below Lavina Mine).
**Look from the road or skip:** #4, #5, #7 (the old maps show an airstrip, quarries, or an open slope).
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
- Series plan, 8-episode lineup, episode 1 script with the origin story (*The Weight*, *Landman*), fact-check box, and animation list: https://claude.ai/artifact/VTejW2kmEvmtjejExpQqMx
- Animation prototypes (vertical MP4s in the repo, `out/animations/`): storm replay (Oct 2026) and hunch checker (I-15 chute).
- Editing plan: record, then AI Producer by OpusClip for transcript, rough cut, captions; vidIQ for titles and thumbnails. Ask before spending credits.

## Open items
- Field day once the washes dry: drone and walk-in at the best bets; Gresh-section scout from public ground only.
- Pull final October storm totals for the top 8.
- Record episode 1; build animation #9 (earthquake year) and #5 (1942 lights out).
- Optional: UNLV Special Collections search for "Gresh", Eldorado Canyon placer photos and claim maps.
- Parked: 3D map view with Google links only.

## Where things live
- Field plan (private page): https://claude.ai/artifact/WQUAb3UvWcTo15K2tFZh9o
- Repo outputs: `out/targets.csv`, `out/map.html`, `out/REPORT.md`, `out/l208_mines.csv`, `out/notes/`, `out/animations/`.
