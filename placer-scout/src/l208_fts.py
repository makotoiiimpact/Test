"""Phase 2 Step A1d: Minerals Yearbook 'Review of 1940' (dli.ernet.205783) has no page index, so use archive.org's in-book
full-text search, which returns the leaf of each hit; leaf -> printed page via page_numbers.json."""
import json, os, re, requests
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "l208")
ID = "dli.ernet.205783"; DOC = "205783-Minerals Yearbook Review Of 1940"
m = requests.get(f"https://archive.org/metadata/{ID}", timeout=120).json()
pn = requests.get(f"https://archive.org/download/{ID}/{DOC.replace(' ', '%20')}_page_numbers.json", timeout=120).json()
leaf2page = {p["leafNum"]: p.get("pageNumber", "") for p in pn["pages"]}
hits = {}
for q in ("Eldorado Canyon district", "Searchlight district", "Yellow Pine district", "Crescent district", "Goodsprings", "El Dorado-Rover", "Techatticup", "Chiquita"):
    r = requests.get(f"https://{m['d1']}/fulltext/inside.php", params={"item_id": ID, "doc": DOC, "path": m["dir"], "q": q}, timeout=120).json()
    for h in r.get("matches", []):
        leaf = h["par"][0].get("page") if h.get("par") else None
        key = (leaf, h["text"][:60])
        if key in hits: continue
        hits[key] = {"query": q, "leaf": leaf, "printed_page": leaf2page.get(leaf, ""), "text": re.sub(r"</?IA_FTS_MATCH>", "", h["text"])}
out = sorted(hits.values(), key=lambda h: (h["leaf"] or 0))
json.dump({"identifier": ID, "url": f"https://archive.org/details/{ID}", "hits": out}, open(os.path.join(DATA, "myb_review1940_hits.json"), "w"), indent=1)
for h in out: print(f"[leaf {h['leaf']} p.{h['printed_page']} q={h['query']}] {h['text'][:700]}\n")
