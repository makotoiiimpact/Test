# placer-scout report

*Made November 1, 2026. Study area: southern Clark County, Nevada (Goodsprings, Eldorado Canyon/Nelson, and Searchlight districts).*

## What this is

This report lists places where a flash flood may have washed gold down from old mines into a desert wash. The computer kept 4,124 spots along washes that have a recorded gold mine, prospect, mill or mine dump within 2 km upstream. 1,106 of them are on Bureau of Land Management (BLM) land and not inside an active mining claim, wilderness, or a national monument. Spots in towns, quarries, and pipeline or power-line corridors were then removed, leaving 981. Then it ranked them, keeping the top 25 at least 1 km apart and no more than 10 in one district. This is a rough guide for where to look first. It does not prove there is gold anywhere, and it is not a legal land survey.

## How to read the score

Each spot gets four numbers. They are multiplied together to make the total score. The first three run from 0.1 to 1; placer history runs from 0.6 to 1.

- **Gold source** asks: is there a recorded gold mine, prospect, mill, or mine dump uphill, and how close is it? A spot only makes the list if one lies within 2 km (1.2 miles) upstream. Old prospect pits and shafts on topo maps can add up to half as much as a recorded mine right next to the wash. If no mine record is close, rusty, clay-rich rock seen from space can count a little instead.
- **Flood** asks: how big was the biggest one-day storm here since 2000? About 20 mm (0.8 inch) of rain starts to count, and 120 mm (4.7 inches) counts fully. A rain gauge counts for less the farther away it is. A flash flood report nearby adds a little, and a big storm this August to October adds a little more, because fresh floods re-sort the gravel.
- **Gold trap** asks: is this a place where fast water slows down? The computer looks for a side wash joining, a wash getting wider, or a wash getting less steep. A trap within 30 m (100 ft) of a road counts half, because road ditches and culverts can fake one, unless the 1 m lidar map confirms it.
- **Placer history** asks: did old government reports record placer gold here? A 1973 USGS report (Bulletin 1356) and a 1937 Bureau of Mines survey (Information Circular 6964) were used. The one documented placer section in Eldorado Canyon (the Gresh claims, T26S R64E Sec 4) counts fully. The rest of the Eldorado Canyon area counts 0.9 and the Searchlight area 0.75, because placer gold was recorded there. Goodsprings and other places count 0.6, because the 1973 report lists no placer gold for them. (Area means the nearest district center, so edges are approximate.) A wash below a mine shut down in 1942 gets +0.1 (see below). This is a gentle nudge, not a gate: no record does not mean no gold.

Each place also has a land-survey address, like *Mount Diablo Meridian T26S R64E Sec 19 SWNW*. Mount Diablo Meridian is the survey baseline for Nevada. T26S R64E is the township and range, a 6-mile square. Sec 19 is a 1-mile square inside it. SWNW means the southwest quarter of the northwest quarter, and L 2 means lot 2. The BLM files mining claims by this address. You can type it into the BLM claim map (MLRS) to look for new claims.

All of the top 10 sit on ground that once had a mining claim that is now closed. That is normal here, because these districts have been prospected for over 100 years. It also means people have staked claims near these spots before.

All the numbers and their sources are in `targets.csv`. The map is `map.html`. Open it in a web browser and turn layers on and off in the box at the top right.

## Top 10 places

Weather radar was checked on 126 stormy days from 2021 to June 2026 and on every day from July 1 to October 30, 2026. Radar readings here run about 1.5 times high (see below).

**#1 — Goodsprings, 35.80764, -115.57338** (score 0.19 = gold source 0.42 × flood 0.75 × trap 1.00 × placer history 0.60)

The strongest gold source upstream is the Boss Mine, about 5,227 feet uphill along the wash. The gold-source signal is weak. The biggest one-day rain weather radar measured near here was about 65 mm (2.6 inches), on October 10, 2025. This season was much wetter than usual here: about 170 mm fell from August through October 2026, 2.2 times the 2023–2025 average, with 64 mm in one day on August 15, 2026. The National Weather Service also logged a flood 2.4 km (1.5 miles) away on August 4, 2016. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. Old-map check (1950s USGS map): **fair**. Open fan about 1.5 km below the Boss Mine, between small washes. The Shenandoah Mill is about 600 m downstream. This spot is on BLM land in Mount Diablo Meridian T25S R57E Sec 03 L 2. It is about 1,545 feet from an unnamed local road. Re-check claims with the link in `targets.csv` before you go.

**#2 — Eldorado Canyon/Nelson, 35.70097, -114.82949** (score 0.13 = gold source 0.51 × flood 0.42 × trap 0.69 × placer history 0.90)

The strongest gold source upstream is the Copper Canyon Mine, about 3,895 feet uphill along the wash. The gold-source signal is medium. The biggest one-day rain weather radar measured near here was about 44 mm (1.7 inches), on March 15, 2024. This season was much wetter than usual here: about 89 mm fell from August through October 2026, 2.0 times the 2023–2025 average, with 30 mm in one day on August 14, 2026. The National Weather Service also logged a flash flood 1.1 km (0.7 miles) away on August 7, 2015. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. Old-map check (1950s USGS map): **strong**. In the main Eldorado Canyon wash channel just below Nelson, downstream of the Black Hawk mine and the Gresh placer section (Sec 4). Bulletin 1356 says the canyon gravels held placer gold. A small cemetery sits on the south bank: keep well clear of it. An active claim is about 5 m away. This spot is on BLM land in Mount Diablo Meridian T26S R64E Sec 10 SWNW. It is about 1,985 feet from an unnamed local road. Be careful here: an active mining claim is only about 16 feet away. Re-check claims with the link in `targets.csv` before you go.

**#3 — Searchlight, 35.45579, -114.89042** (score 0.12 = gold source 0.41 × flood 0.41 × trap 0.99 × placer history 0.75)

The strongest gold source upstream is the Geneva Mill, about 3,391 feet uphill along the wash. The gold-source signal is weak. The biggest one-day rain weather radar measured near here was about 40 mm (1.6 inches), on August 12, 2026. This season was much wetter than usual here: about 103 mm fell from August through October 2026, 3.0 times the 2023–2025 average, with 40 mm in one day on August 12, 2026. The National Weather Service also logged a flash flood 2.9 km (1.8 miles) away on July 19, 2017. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. Old-map check (1950s USGS map): **strong**. In a real wash where it leaves a canyon onto the fan, about 700 m below the Pittsburg Mine. Classic drop-out spot. This spot is on BLM land in Mount Diablo Meridian T29S R63E Sec 01 L 1. It is about 741 feet from an unnamed local road. Re-check claims with the link in `targets.csv` before you go.

**#4 — Wash outside the three districts, 36.04440, -115.29995** (score 0.12 = gold source 0.48 × flood 0.42 × trap 1.00 × placer history 0.60)

The strongest gold source upstream is an old mine dump shown on the Blue Diamond SE 1972 USGS topographic map, about 6,788 feet uphill along the wash. The gold-source signal is medium. The biggest one-day rain weather radar measured near here was about 46 mm (1.8 inches), on September 1, 2023. This season was about normal here: about 56 mm fell from August through October 2026, 1.1 times the 2023–2025 average, with 25 mm in one day on October 10, 2026. The National Weather Service also logged a flash flood 3.3 km (2.0 miles) away on July 7, 2014. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. Old-map check (1950s USGS map): **weak**. Upstream workings are quarries (gypsum and limestone country), not gold. Spot is under a power line at a road crossing. This spot is on BLM land in Mount Diablo Meridian T22S R60E Sec 07 SESE. It is about 820 feet from S Fort Apache Rd (local road). Re-check claims with the link in `targets.csv` before you go.

**#5 — Eldorado Canyon/Nelson, 35.71088, -114.82764** (score 0.12 = gold source 0.41 × flood 0.42 × trap 0.75 × placer history 0.90)

The strongest gold source upstream is the Eldorado Empire Mining Co., about 3,966 feet uphill along the wash. Satellite images also show rusty, clay-rich rock on about 8% of the slopes that drain here. The gold-source signal is weak. The biggest one-day rain weather radar measured near here was about 42 mm (1.6 inches), on March 15, 2024. This season was much wetter than usual here: about 92 mm fell from August through October 2026, 1.9 times the 2023–2025 average, with 35 mm in one day on August 14, 2026. The National Weather Service also logged a flash flood 0.7 km (0.4 miles) away on August 7, 2015. The wash floor gets wider here, from about 16 m to 47 m on the 10 m map. Water spreads out and slows where a wash widens. The 1 m lidar map agrees with this. Old-map check (1950s USGS map): **weak**. Beside the old Nelson landing strip and the highway at the edge of town, on a small side channel; likely road and airstrip drainage. This spot is on BLM land in Mount Diablo Meridian T26S R64E Sec 03 NWSW. It is about 26 feet from an unnamed local road. Re-check claims with the link in `targets.csv` before you go.

**#6 — Goodsprings, 35.83995, -115.46764** (score 0.10 = gold source 0.59 × flood 0.28 × trap 1.00 × placer history 0.60)

The strongest gold source upstream is the Lavina Mine, about 3,913 feet uphill along the wash. The gold-source signal is medium. The biggest one-day rain weather radar measured near here was about 47 mm (1.8 inches), on October 10, 2025. This season was about normal here: about 101 mm fell from August through October 2026, 1.1 times the 2023–2025 average, with 24 mm in one day on October 10, 2026. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. Old-map check (1950s USGS map): **strong**. In a real wash 300 to 400 m below the Iron Gold and Lavina mines, with prospect pits all around. This spot is on BLM land in Mount Diablo Meridian T24S R58E Sec 22 L 13. It is about 233 feet from an unnamed local road. Be careful here: an active mining claim is only about 121 feet away. Re-check claims with the link in `targets.csv` before you go.

**#7 — Goodsprings, 35.81727, -115.44681** (score 0.10 = gold source 0.48 × flood 0.36 × trap 0.93 × placer history 0.60)

The strongest gold source upstream is the Lookout Mine, about 6,200 feet uphill along the wash. The gold-source signal is medium. The biggest one-day rain weather radar measured near here was about 39 mm (1.5 inches), on February 13, 2025. This season was about normal here: about 92 mm fell from August through October 2026, 1.1 times the 2023–2025 average, with 24 mm in one day on October 10, 2026. The National Weather Service also logged a flash flood 4.7 km (2.9 miles) away on June 30, 2016. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. Old-map check (1950s USGS map): **weak**. Open slope, not on a mapped wash; below the Argentena (mainly lead-zinc) mine. This spot is on BLM land in Mount Diablo Meridian T24S R58E Sec 35 SWNW. It is about 302 feet from an unnamed local road. Re-check claims with the link in `targets.csv` before you go.

**#8 — Goodsprings, 35.85866, -115.47588** (score 0.09 = gold source 0.53 × flood 0.34 × trap 0.85 × placer history 0.60)

The strongest gold source upstream is the Prairie Flower Mine, about 4,862 feet uphill along the wash. The gold-source signal is medium. The biggest one-day rain weather radar measured near here was about 53 mm (2.1 inches), on October 10, 2025. This season was about normal here: about 106 mm fell from August through October 2026, 1.0 times the 2023–2025 average, with 23 mm in one day on October 10, 2026. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. Old-map check (1950s USGS map): **fair**. Wash below the district's core mines (Pilgrim, Red Cloud, Prairie Flower), but running beside the highway. This spot is on BLM land in Mount Diablo Meridian T24S R58E Sec 16 L 6. It is about 436 feet from an unnamed local road. Re-check claims with the link in `targets.csv` before you go.

**#9 — Searchlight, 35.48208, -114.92264** (score 0.09 = gold source 0.50 × flood 0.24 × trap 1.00 × placer history 0.75)

The strongest gold source upstream is the Southern Nevada Mine, about 891 feet uphill along the wash. The gold-source signal is medium. The biggest one-day rain weather radar measured near here was about 28 mm (1.1 inches), on November 15, 2025. This season was much wetter than usual here: about 98 mm fell from August through October 2026, 2.3 times the 2023–2025 average, with 23 mm in one day on August 12, 2026. The National Weather Service also logged a flash flood 0.8 km (0.5 miles) away on August 3, 2008. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. This spot is on BLM land in Mount Diablo Meridian T28S R63E Sec 27 L 8. It is about 131 feet from US Hwy 95 (secondary road). Be careful here: private land is only about 108 feet away. Re-check claims with the link in `targets.csv` before you go.

**#10 — Searchlight, 35.43718, -114.91986** (score 0.09 = gold source 0.24 × flood 0.49 × trap 1.00 × placer history 0.75)

The strongest gold source upstream is the Rambler Mine, about 5,999 feet uphill along the wash. The gold-source signal is weak. The biggest one-day rain weather radar measured near here was about 45 mm (1.8 inches), on August 12, 2026. This season was much wetter than usual here: about 109 mm fell from August through October 2026, 3.0 times the 2023–2025 average, with 45 mm in one day on August 12, 2026. The National Weather Service also logged a flash flood 3.1 km (1.9 miles) away on August 31, 2013. A side wash joins the main wash here. Water slows down where two washes meet, so heavy gold can drop out. This spot is on BLM land in Mount Diablo Meridian T29S R63E Sec 11 SWNW. It is about 810 feet from an unnamed local road. Re-check claims with the link in `targets.csv` before you go.

## What the computer could not do

- **Claim closing dates are missing.** The BLM mining-claim map has no closing date for old claims. So the tool could not tell when each wash was last worked. It counted storms since January 1, 2000 everywhere instead.
- **Some data could not be reached.** The Nevada Bureau of Mines and Geology website was blocked from this computer, so its district reports were not used. The USGS place-names list had almost no mines in it.
- **Goodsprings has no recorded placer gold in the 1973 USGS report.** Its mines were mostly lead and zinc mines. The placer-history number lowers Goodsprings spots, but they still fill the district's 10 places in the top 25 because their floods and traps score well.
- **Mine records say little about gold amount.** A mine on the list may have produced only a small amount of gold. Many Goodsprings mines were mainly lead and zinc mines.
- **The 10 m map is coarse.** The 1 m lidar map did not agree with 11 of the wash-widening and slope-break spots the 10 m map picked. Those spots were removed. Most of the final traps are side-wash junctions, which the lidar check cannot test.
- **Satellite before-and-after pictures showed no clear change** at 23 of the 25 places (only a faint hint at #4 and #21). Desert washes are narrow, and the satellite pixels are 20 m wide, so small changes are hard to see.
- **Radar was not checked every day before July 2026.** From 2021 to June 2026 only 126 stormy days were read; days with no gauge rain and no storm report were skipped, so a local storm could have been missed. Every day from July 1 to October 30, 2026 was read, including the storm of October 30–31. Checked against the county's official gauge files for 2023–2025, radar totals here run about 1.5 times higher than the gauges, so read the radar millimeters as high. Comparisons between years use radar on both sides, so they still hold. The October 30–31 storm has no gauge check yet. Radar values are averaged over about 5 km. Before 2021, the tool used Clark County rain gauges within 8 km, and many washes have no gauge that close.
- **Old maps list many small prospect pits.** Repeat copies of the same pit from different map years were removed, but a wash below lots of pits can still look stronger than it really is.

## Land and legal notes

- The tool removed National Park Service land (including Lake Mead National Recreation Area), Forest Service land, state land, private land, BLM wilderness, and active mining claims.
- It also removed **Avi Kwa Ame National Monument**, Sloan Canyon, and Red Rock Canyon. These BLM areas are closed to new mining claims. This removed much of the land around Searchlight. Ask the BLM Las Vegas Field Office if hobby gold panning is allowed there before you go.
- Patented (privately owned) mining claims are not marked in the BLM claim data. The tool relied on the BLM land map to catch them. Old patented claims are common in Goodsprings, Searchlight, and Nelson. Watch for signs and fences.
- BLM land is usually open for casual gold panning with hand tools. You may not dig large holes, use motors, or disturb a lot of ground without permission. Do not work on anyone's active claim.

## Safety

- **Never enter old mine shafts or tunnels.** They can collapse, have bad air, or hide deep drops. Stay well back from open holes.
- **Never work in a wash when storms are possible.** Flash floods can come from rain miles away, even when the sky above you is clear. Check the forecast and leave if clouds build.
- **Treat old mill waste as dangerous.** Old mills often used mercury to catch gold, and the waste can still hold mercury and arsenic. Do not dig in it, do not breathe its dust, and wash your hands and gear.
- Bring plenty of water, tell someone where you are going, and watch for rattlesnakes. Many places have no cell signal.

## Old records and the 1942 shutdown

In 1942 the government ordered most gold mines to stop (War Production Board Order L-208). Old Bureau of Mines yearbooks from 1939 to 1947 were searched for every mine in these districts. 19 mines are listed in `l208_mines.csv`, each fact with a page number. The ones that look like they were stopped by the order:

- **Wall Street mine** (Eldorado Canyon). Medium candidate. The 1943 yearbook says it operated 'from January 1 to June 18, 1943' (no reason given). Site: private land (likely an old patented claim).
- **Jubilee mine** (Eldorado Canyon). Strong candidate. The 1942 yearbook says it operated 'from January 1 to December 1' 1942. Site: private land (likely an old patented claim).
- **Techatticup mine** (Eldorado Canyon). Strong candidate. The 1942 yearbook says it operated 'from January 1 to December 1' 1942. Site: private land (likely an old patented claim).
- **El Dorado-Rover group (Rover, Rand, Quaker City, Magnolia, Crown, Nevada Eagle, et al.)** (Eldorado Canyon). Reopened after the war. The 1942 yearbook says it operated 'from January 1 to December 8, 1942' (L-208 took effect Dec 8, 1942). Site: BLM land (check claims).

Most of these mine sites are private land, so they cannot be visited. But the washes below them can be on public land. A wash gets a small boost (+0.1 on placer history) when its strongest upstream gold source is within 300 m of a strong or medium candidate. The El Dorado-Rover group gets no boost, because it was worked again after the war. 0 of the top 25 got this boost. The boosted washes, below the Jubilee and Wall Street mines, score low on flood or trap.

Two more old reports were used. A 1973 USGS report (Bulletin 1356, *Placer Gold Deposits of Nevada*) says Eldorado Canyon's recent placer gold came mostly from the Gresh claims in T26S R64E Sec 4, and lists no placer gold for Goodsprings. A 1937 Bureau of Mines survey (Information Circular 6964) names C. E. L. Gresh as president of the Eldorado Empire Mining Co. Notes: `notes/usgs_b1356_placers.md`.

## Ground the old maps ruled out

The 1950s USGS maps showed some top spots sat in a town, quarries, or a pipeline corridor. Spots like that are now removed everywhere: inside a town with streets nearby, within 150 m of a mapped quarry, pit or open-pit mine, within 150 m of a mapped gas pipeline (never dig over a buried pipeline), or within 60 m of a power line. Legal spots removed: townsite, 46; pipeline corridor, 41; power line corridor, 33; quarry or pit, 5. Pipeline maps are approximate, so watch for pipeline markers in the field. The rules miss some cases: the old maps still rate #4 and #5 and #7 as weak (see their entries), because the mapped quarry or power line was not close enough, or the problem is an open slope or airstrip, which this check cannot test.

## The ant-mound test (stopped)

Harvester ants bring up small heavy grains, so their mounds can show gold from below. Fifty spots from 0.6 m aerial photos were checked by eye: 0 yes, 24 no, 26 not sure. The plan was to stop if fewer than 5 of 50 were real mounds, so the test stopped. The photos are too coarse, and the local ants make small mounds without a cleared ring.

## Where the data came from

BLM mining claims and land status (gis.blm.gov, nlsdbpubgis.blm.gov); USGS mine records (MRDS) and old topographic map mine features (USMIN, mrdata.usgs.gov); USGS 3DEP elevation, 10 m and 1 m lidar (prd-tnm.s3.amazonaws.com); Sentinel-2 satellite images (Earth Search, AWS); NOAA MRMS weather radar (noaa-mrms-pds on AWS); NOAA Storm Events (ncei.noaa.gov); Clark County Regional Flood Control District rain gauges (gustfront.ccrfcd.org); Census TIGER roads and town boundaries; HIFLD power lines; EIA/HIFLD gas pipelines; USGS Bulletin 1356; USBM IC 6964 and Minerals Yearbooks 1939–1947 (archive.org). Downloaded files are listed with their address, date, and file check code in `data/PROVENANCE.csv`. Lidar tiles and satellite scenes were read straight from their sources without being saved.
