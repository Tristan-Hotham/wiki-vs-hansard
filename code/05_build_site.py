"""Step 5: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet.
10.5281/zenodo.24092583, https://doi.org/10.5281/zenodo.24092583 and https://blog.tristanhotham.com/2026/10/31/wiki-vs-hansard/ stay as placeholders for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "20261109")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
S = jload(f"{DATA}/site.json")
names = {p["n"] for p in S["places"]}
for g in re.findall(r'data-go="([^"]+)"', t):
    assert g in names, g
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
