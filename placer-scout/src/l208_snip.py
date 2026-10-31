"""Print merged snippets (+-N chars) around Clark County district keywords, tagged with printed page, for one year."""
import os, re, sys, json
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "l208")
KEY = re.compile(r"clark\s+county|searchlight|goodsprings|yellow\s+pine|eldorado|el\s+dorado|nelson|crescent|newberry|potosi", re.I)
y, W = int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 700
d = json.load(open(os.path.join(DATA, f"myb_{y}.json")))
for p in d["pages"]:
    t = re.sub(r"\s+", " ", p["text"])
    if not re.search(r"nevada", t, re.I) or len(KEY.findall(t)) < 2 or re.search(r"\bindex\b", t[:300], re.I): continue
    spans = []
    for m in KEY.finditer(t):
        a, b = max(0, m.start() - W), min(len(t), m.end() + W)
        if spans and a <= spans[-1][1]: spans[-1][1] = b
        else: spans.append([a, b])
    for a, b in spans:
        print(f"\n[{y} p.{p['printed_page']} leaf {p['leaf']}] ...{t[a:b]}...")
