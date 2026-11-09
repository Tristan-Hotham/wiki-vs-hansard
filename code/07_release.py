"""Step 7: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24092583, https://doi.org/10.5281/zenodo.24092583 and https://blog.tristanhotham.com/2026/10/31/wiki-vs-hansard/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Who_Gets_Talked_About"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Who gets talked about? What the public looks up on Wikipedia, and what Parliament talks about",
        "slug": "wiki-vs-hansard",
        "excerpt": f"I set a year of Wikipedia reading against twenty-one years of Commons debate for {R['n']['main']:,} UK towns and cities. The two mostly agree, but a town with a seat named after it gets {R['prose']['seat_x']:.1f} times the mentions, and Welsh places are talked about more, not less.",
        "seo_description": f"Which UK places does the public look up on Wikipedia, and which does Parliament talk about? {R['n']['main']:,} towns compared, 2005 to 2025.",
        "tags": ["maps", "data visualisation", "Parliament", "Hansard", "Wikipedia", "representation", "UK politics", "towns"],
        "header_alt": "Title card on cream paper reading 'Who gets talked about?' beside a map of UK places coloured from blue to red by how often the Commons mentions them against their Wikipedia views."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("places.csv", "index.csv", "match_log.csv", "place_years.csv", "models.csv", "results.json"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$\\rho$", "rho").replace("$", "").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "Who Gets Talked About? Public Attention on Wikipedia and Parliamentary Attention in the House of Commons to UK Places, 2005 to 2025",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/wiki-vs-hansard/}}.</p><p>Sources: Hansard via the UK Parliament Hansard API (Open Parliament Licence v3.0), counted in Mentioned in the House (doi:10.5281/zenodo.23761431); seat names from Who Won Here? (doi:10.5281/zenodo.23761425); English Wikipedia pageviews (Wikimedia, CC0); Wikidata (CC0); ONS 2011 Census and boundaries (OGL v3.0). Text, figures and data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["political attention", "parliamentary debate", "Hansard", "Wikipedia pageviews", "constituency representation", "United Kingdom", "places"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23761431", "relation": "isDerivedFrom", "resource_type": "publication"},
                                 {"identifier": "10.5281/zenodo.23761425", "relation": "isDerivedFrom", "resource_type": "publication"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2, keepdash=True)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
