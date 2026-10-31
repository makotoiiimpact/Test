"""Phase 2 Step A1c: cut the CLARK COUNTY section of each yearbook's Nevada metals chapter, keeping printed-page markers.
Also record the data year each volume reports (most frequent 'in 19NN' in the Nevada chapter)."""
import os, re, json, collections
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "l208")
NEXT = re.compile(r"\b(DOUGLAS|ELKO|ESMERALDA|EUREKA|HUMBOLDT|LANDER|LINCOLN|LYON|MINERAL|NYE|ORMSBY|PERSHING|STOREY|WASHOE|WHITE\s+PINE)\s+COUNTY", re.I)
meta = {}
for y in range(1939, 1948):
    d = json.load(open(os.path.join(DATA, f"myb_{y}.json")))
    pages = d["pages"]
    # Nevada chapter = pages whose running head mentions NEVADA and gold/silver
    nv = [i for i, p in enumerate(pages) if re.search(r"(GOLD|SILVER).{0,60}NEVADA|NEVADA.{0,60}(GOLD|SILVER)", p["text"][:400], re.I | re.S)]
    years = collections.Counter(re.findall(r"\bin (19[34]\d)\b", " ".join(pages[i]["text"] for i in nv)))
    start = None
    for i in nv:
        m = re.search(r"CLARK\s+COUNTY", pages[i]["text"])
        if m: start = (i, m.start()); break
    sec = ""
    if start:
        i, off = start; buf = []
        for j in range(i, min(i + 6, len(pages))):
            t = pages[j]["text"][off if j == i else 0:]
            n = NEXT.search(t, 20 if j == i else 0)
            buf.append(f"\n<<p.{pages[j]['printed_page']} leaf {pages[j]['leaf']}>>\n" + (t[:n.start()] if n else t))
            if n: break
        sec = re.sub(r"[ \t]+", " ", "".join(buf))
    meta[y] = {"data_year_guess": years.most_common(3), "nevada_chapter_pages": [pages[i]["printed_page"] for i in nv][:1] + [pages[i]["printed_page"] for i in nv][-1:],
               "clark_section_chars": len(sec)}
    open(os.path.join(DATA, f"clark_{y}.txt"), "w").write(sec)
    print(y, meta[y])
json.dump(meta, open(os.path.join(DATA, "volumes.json"), "w"), indent=1)
