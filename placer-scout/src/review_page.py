"""Phase 2 Step B4: build out/review/review.html (published as a private Artifact; answers saved to its db, exported to labels.json)."""
import os, json
OUT = os.path.join(os.path.dirname(__file__), "..", "out", "review")
clips = json.load(open(os.path.join(OUT, "clips.json")))
data = [{"id": c["id"], "a": c["img2022"], "b": c["img2019"]} for c in clips]       # score/band hidden from the reviewer
html = r"""<title>Ant Mound Clip Review</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">
<style>
/* layout: sticky progress bar, then a field-notebook grid of clip cards (1 col phone, 2-3 wide) */
:root{--bg:#efece4;--card:#f8f6f0;--ink:#2b2a25;--muted:#6b675c;--line:#d6d0c2;--yes:#9a5b17;--yes-bg:#f3e3cc;--no:#4e5a62;--no-bg:#e1e6e8;--unsure:#7a6f2a;--unsure-bg:#ece7c9;
--display:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;--body:"Atkinson Hyperlegible",system-ui,-apple-system,"Segoe UI",sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1d1e1a;--card:#262722;--ink:#e9e6dc;--muted:#a6a293;--line:#3a3b34;--yes:#e0a35c;--yes-bg:#3d2d18;--no:#a9b8c1;--no-bg:#2a3236;--unsure:#d6c873;--unsure-bg:#37341d;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#1d1e1a;--card:#262722;--ink:#e9e6dc;--muted:#a6a293;--line:#3a3b34;--yes:#e0a35c;--yes-bg:#3d2d18;--no:#a9b8c1;--no-bg:#2a3236;--unsure:#d6c873;--unsure-bg:#37341d;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font:16px/1.5 var(--body)}
.wrap{max-width:1180px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 48px}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}
h1{font:600 1.7rem/1.15 var(--display);letter-spacing:.01em;margin:0 0 .4rem;text-wrap:balance}
.intro{max-width:68ch;color:var(--ink)}
.intro p{margin:.4rem 0}
.how{display:grid;gap:.35rem;margin:.8rem 0 0;padding:0;list-style:none;max-width:68ch}
.how li{padding-left:1.1rem;position:relative}.how li::before{content:"";position:absolute;left:0;top:.62em;width:.45rem;height:.45rem;border-radius:50%;background:var(--yes)}
.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);border-bottom:1px solid var(--line);margin:18px 0;padding-block:10px;display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center}
.count{font:600 1rem var(--display);letter-spacing:.04em;text-transform:uppercase;font-variant-numeric:tabular-nums}
.track{flex:1 1 200px;height:8px;background:var(--line);border-radius:4px;overflow:hidden}.fill{height:100%;width:0;background:var(--yes);transition:width .2s}
.status{color:var(--muted);font-size:.9rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;display:grid;gap:10px;min-width:0}
.card[data-a="yes"]{border-color:var(--yes)}.card[data-a="no"]{border-color:var(--no)}.card[data-a="unsure"]{border-color:var(--unsure)}
.head{display:flex;justify-content:space-between;align-items:baseline;font:600 .85rem var(--display);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:6px}
figure{margin:0;min-width:0}figure img{display:block;width:100%;aspect-ratio:1;image-rendering:pixelated;border-radius:4px}
figcaption{font:500 .75rem var(--display);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-top:3px}
.btns{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
button{font:700 .95rem var(--body);padding:.6rem .4rem;border-radius:6px;border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}
button:hover{border-color:var(--muted)}button:focus-visible{outline:3px solid var(--yes);outline-offset:2px}
button[aria-pressed="true"].yes{background:var(--yes-bg);border-color:var(--yes);color:var(--yes)}
button[aria-pressed="true"].no{background:var(--no-bg);border-color:var(--no);color:var(--no)}
button[aria-pressed="true"].unsure{background:var(--unsure-bg);border-color:var(--unsure);color:var(--unsure)}
.note{margin-top:28px;color:var(--muted);font-size:.9rem;max-width:68ch}
@media (prefers-reduced-motion:reduce){.fill{transition:none}}
</style>
<div class="wrap">
<h1>Ant mound clip review</h1>
<div class="intro">
<p>These are 50 spots the detector picked in open BLM desert near Nelson (Eldorado Canyon), below the Rand and Quaker City mines. Each card shows the same spot in the 2022 and 2019 NAIP aerial photos, 30 m across. The red ring is about 6.6 m wide; the spot sits in its middle. The yellow bar is 5 m.</p>
<ul class="how">
<li><b>Yes</b>: a bare, roughly round clearing about 2.5–3 m across (about half the ring), often with shrubs around its edge, and it shows in both years.</li>
<li><b>No</b>: a rock, a gap between bushes, a track, a wash bank, a dug pit, or nothing you can see.</li>
<li><b>Not sure</b>: you can't tell at this resolution. That is a fine answer.</li>
</ul>
</div>
<div class="bar" role="status"><span class="count" id="count">0 of 50 reviewed</span><div class="track" aria-hidden="true"><div class="fill" id="fill"></div></div><span class="status" id="status">Connecting to saved answers…</span></div>
<div class="grid" id="grid"></div>
<p class="note">Answers save as you click, and you can change them any time. When you're done, tell Claude in chat; it reads the answers, writes them to labels.json, and tunes the detector. If fewer than 5 of the 50 are real mounds, the scan stops there.</p>
</div>
<script>
const CLIPS = __DATA__;
const answers = {};
const grid = document.getElementById("grid");
const LABEL = {yes: "Yes", no: "No", unsure: "Not sure"};
for (const c of CLIPS) {
  const card = document.createElement("article"); card.className = "card"; card.id = "card-" + c.id;
  card.innerHTML = `<div class="head"><span>Clip ${c.id.slice(1)}</span><span id="ans-${c.id}"></span></div>
  <div class="pair"><figure><img alt="2022 aerial photo, clip ${c.id.slice(1)}" src="data:image/png;base64,${c.a}"><figcaption>NAIP 2022</figcaption></figure>
  <figure><img alt="2019 aerial photo, clip ${c.id.slice(1)}" src="data:image/png;base64,${c.b}"><figcaption>NAIP 2019</figcaption></figure></div>
  <div class="btns">${["yes","no","unsure"].map(k => `<button type="button" id="b-${c.id}-${k}" class="${k}" data-id="${c.id}" data-k="${k}" aria-pressed="false">${LABEL[k]}</button>`).join("")}</div>`;
  grid.appendChild(card);
}
function paint() {
  let n = 0;
  for (const c of CLIPS) {
    const a = answers[c.id]; if (a) n++;
    const card = document.getElementById("card-" + c.id); card.dataset.a = a || "";
    document.getElementById("ans-" + c.id).textContent = a ? LABEL[a] : "";
    for (const k of ["yes","no","unsure"]) document.getElementById(`b-${c.id}-${k}`).setAttribute("aria-pressed", a === k ? "true" : "false");
  }
  document.getElementById("count").textContent = `${n} of ${CLIPS.length} reviewed · ${Object.values(answers).filter(v => v === "yes").length} yes`;
  document.getElementById("fill").style.width = (100 * n / CLIPS.length) + "%";
}
const status = document.getElementById("status");
let col = null;
try { Object.assign(answers, JSON.parse(localStorage.getItem("mound-answers") || "{}")); } catch (e) {}
paint();
grid.addEventListener("click", async (e) => {
  const b = e.target.closest("button[data-id]"); if (!b) return;
  const id = b.dataset.id, k = b.dataset.k;
  answers[id] = k; paint();
  try { localStorage.setItem("mound-answers", JSON.stringify(answers)); } catch (e) {}
  if (!col) { status.textContent = "Saved on this device only. Open this page on claude.ai while signed in so Claude can read your answers."; return; }
  try { await col.doc(id).set({answer: k, at: new Date().toISOString()}); status.textContent = "Saved"; }
  catch (err) { status.textContent = "Couldn't save that answer (" + (err && err.code || "error") + "). Try clicking it again."; }
});
(async () => {
  const timer = setTimeout(() => { if (!col) status.textContent = "Saved answers aren't reachable here; answers will stay on this device."; }, 10000);
  const db = window.claude ? await window.claude.use("db") : null;
  if (!db) { clearTimeout(timer); status.textContent = "Saved answers aren't reachable here; answers will stay on this device."; return; }
  col = db.collection("labels");
  col.onSnapshot((snap) => {
    clearTimeout(timer);
    for (const d of snap.docs) { const v = d.data(); if (v && v.answer) answers[d.id] = v.answer; }
    paint(); status.textContent = "Answers save as you click";
  }, (err) => { clearTimeout(timer); status.textContent = "Couldn't load saved answers (" + (err && err.code || "error") + ")."; });
})();
</script>"""
open(os.path.join(OUT, "review.html"), "w").write(html.replace("__DATA__", json.dumps(data)))
print("review.html KB", os.path.getsize(os.path.join(OUT, "review.html")) // 1024)
