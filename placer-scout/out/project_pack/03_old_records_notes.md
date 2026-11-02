# USGS Bulletin 1356 (Johnson, 1973), "Placer gold deposits of Nevada": Clark County check (Nov 1, 2026)

> **Status after the ground re-rank (later on Nov 1, 2026):** target numbers below are from the earlier ranking. Since then the
> Nelson townsite cells were removed (`src/ground.py`), so old #1 and Black Hawk (#23, the Gresh section) are gone. The Eldorado
> Empire mine now feeds target #5; the new #2 is the main Eldorado Canyon wash just downstream of the Gresh section. Goodsprings
> holds 10 of the top 25. Current numbers are in `out/targets.csv`.

Source: https://pubs.usgs.gov/bul/1356/report.pdf (63 pages, scanned). Pages cited are the printed page numbers.

## What it says (quotes are from the report)
- **Eldorado Canyon (district 4, p. 6–7):** "Small amounts of placer gold have been found in the gravels of Eldorado Canyon" and in Colorado River bars. Recent production came "mostly from the Gresh Group of claims in the upper canyon near Nelson (sec. 4, T. 26 S., R. 64 E., Nelson quadrangle)." The gold is fine and scarce because "much of the gold is contained in sulfides." Table 1 (p. ~51): about 300 oz estimated before 1901, 173 oz recorded 1902–68, 470 oz estimated total.
- **Searchlight (district 7, p. 9–10):** the placers are "east of the main lode-gold mining area between the Newberry Mountains and the Colorado River (Tps. 28-31 S., Rs. 65 and 66 E.)", mostly in "ancient riverbed gravels", worked in the 1930s. 26 oz recorded, 50 oz estimated.
- **Gold Butte / Temple Bar (district 5, p. 7–8):** fine gold, at most pinhead size, in the 2–20 ft of gravel just above bedrock; Temple Bar was flooded by Lake Mead.
- **Las Vegas Wash (district 6, p. 8–9):** 43 oz in 1905; dredge plans in 1909 were never carried out; now under Lake Mead.
- **Goodsprings:** not listed as a placer district at all (no recorded placer production).

## What it means for the targets (`out/targets.csv`)
- **Independent check, Eldorado:** #23 (Black Hawk) is in T26S R64E Sec 04, the Gresh placer section; #1 (Eldorado Empire) is in Sec 03 next door. Placer records were not a model input, so the model reached the one documented placer section on its own. The Gresh claims may still be claimed or patented, so re-check BLM MLRS before going.
- **Goodsprings caution:** 11 of the top 25 are in a district with no recorded placer gold. Its mines were mainly lead and zinc. Treat Goodsprings targets as lower confidence than their scores.
- **Searchlight:** the recorded placers lie east of our targets, in old river gravels toward the Colorado. Most of that ground is now Avi Kwa Ame National Monument or Lake Mead NRA, which the model excludes.

## Follow-up: USBM Information Circular 6964 (Vanderburg, 1937), free on archive.org
Source: https://archive.org/details/pub_usgov-bmines-information-circular_6964 (OCR text; spelling below corrected from the scan).
- "The Eldorado Empire Mining Co., C. E. L. Gresh, of Nelson, Nev., president and principal owner, controls the Empire group of
  three claims (one patented) adjoining the Wall Street group on the east." Inactive in February 1937; about 50 tons of ore on
  the dumps "reported to average about $12 per ton in gold and silver."
- Eldorado Empire Mining Co. is the top gold source above target #1. The 1973 report's "Gresh Group" placer claims in
  T26S R64E Sec 04 carry the same family name. Likely connected, but the documents do not say they are the same claims.
- Wall Street, the neighbor to the west, is the L-208 "medium" candidate (stopped June 18, 1943; out/l208_mines.csv).
- Table 1 (Clark County production 1908–1935) shows placer gold only as footnotes: $98, $2,317, $1,035 and one illegible value.
  Placer gold was a very small part of county gold output.
- NBMG Bulletin 30 (Vanderburg 1936, Placer Mining in Nevada) costs $15 from NBMG and was not bought; this circular and
  Bulletin 1356 cover most of what we need.
