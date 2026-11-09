"""Shared paths, constants and helpers for the wiki-vs-hansard study ("Who gets talked about?").

Inputs (read in place, never modified):
  RAW/uk_settlements_enwiki.tsv.gz  Wikidata UK human settlements (QLever export, CC0): item, English Wikipedia title,
                                    population (P1082, mixed vintages) and point. Includes some non-UK territories
                                    (Gibraltar and others) and a few areas that are not settlements: see 01_data.py.
  RAW/pageviews_2024.json           English Wikipedia user (non-bot) pageviews for each title, summed over 2024
                                    (Wikimedia REST pageviews API, agent=user). Only titles of settlements with a
                                    Wikidata population of at least 1,500 were fetched (5,191 titles); 0 = no views or
                                    no article under that exact title; -1 = fetch error.
  HP/places.csv, place_years.csv,   Mentioned in the House (Hotham 2026, Zenodo 10.5281/zenodo.23761431): Commons
  constituencies.csv                Hansard counts of contributions containing "in <place>" by year (1900 to 2026) and
                                    any mention (2005 to 2026), ambiguity flags and precision factors; seat names in use
                                    2005 to 2026 (Open Parliament Licence v3.0).
  ELEC (contests.csv)               Who Won Here? (Hotham 2026, Zenodo 10.5281/zenodo.23761425), data/contests.csv:
                                    every constituency contested at each general election; the 2005, 2010 and 2024
                                    lists give the seat names of each boundary period (646, 650, 650).
  RAW/census_11.csv, wpc2010_gb.json  2011 Census by Westminster constituency (2010 boundaries, GB) and the boundaries
                                    (ONS, Open Government Licence v3.0): region and deprivation proxies.
  GEO/lad23_bsc.geojson             Local authority districts, December 2023, incl. Northern Ireland (ONS/OSNI, OGL v3):
                                    clustering unit and the UK land mask.
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("WH_RAW", "/home/claude/newdata/raw_new11")
HP = os.environ.get("WH_HP", "/home/claude/src6/hansard-places/data")
GEO = os.environ.get("WH_GEO", "/home/claude/newdata/raw/geo")
ELEC = os.environ.get("WH_ELEC", "/home/claude/ref/elections-since-1832/data/contests.csv")
FONTS = os.environ.get("WH_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("WH_SCRATCH", "/home/claude/scratch/wiki-vs-hansard")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "wiki-vs-hansard"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
LONDON = (51.5074, -0.1278)          # Charing Cross, near enough
Y0, Y1 = 2005, 2025                  # parliamentary window (full calendar years)
SPLIT = 2015                          # first period 2005 to 2014, second 2015 to 2025
MATCH_KM = 20.0                      # Hansard point to Wikidata point


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\bsaint\b", "st", s)
    return s


def base_title(t):
    """the place-name part of a Wikipedia title: 'Reading, Berkshire' -> 'reading'; 'Cowbridge (Roman town)' -> 'cowbridge'"""
    return norm(re.sub(r"\s*\(.*\)$", "", t.split(",")[0]))


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None, keepdash=False):
    obj = nonan(obj) if keepdash else dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    raise ValueError(f)
