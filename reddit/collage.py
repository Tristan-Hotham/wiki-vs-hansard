"""Reddit collage (r/dataisbeautiful style), light background, 2700 x 2025 px: a map of Commons mentions against what
Wikipedia views and population predict, the seat-name effect, the most and least mentioned places, and a full legend.
Run after code/03_results.py:  python3 reddit/collage.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as stransform, unary_union
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
plt.rcParams.update({"font.family": "Source Serif 4", "axes.unicode_minus": False})
PAPER, INK, MUT, SEA = "#FAF6EC", "#2B2119", "#6E604E", "#E6EEF1"
RED, BLUE = "#B4442E", "#2F6A9E"
CMAP = LinearSegmentedColormap.from_list("d", [BLUE, "#8FB0CF", "#C9C2B4", "#E3A58F", RED])
NORM = TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3)
HALO = [pe.withStroke(linewidth=4, foreground=SEA)]
R = jload(f"{DATA}/results.json")
I = pd.read_csv(f"{DATA}/index.csv")
tr = Transformer.from_crs(4326, 27700, always_xy=True)
C = jload(f"{GEO}/counties_uk.geojson")["features"]
uk = stransform(lambda a, b, z=None: tr.transform(a, b), unary_union([shape(f["geometry"]).buffer(0.002) for f in C]).buffer(-0.002).simplify(0.003))
NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]
irl = stransform(lambda a, b, z=None: tr.transform(a, b), next(shape(f["geometry"]) for f in NE if f["properties"]["ADM0_A3"] == "IRL"))


def patch(ax, g, **kw):
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.geom_type != "Polygon": continue
        v, c = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = np.asarray(ring.coords); v += cs.tolist(); c += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(v, c), **kw))


fig = plt.figure(figsize=(13.5, 10.125), dpi=200)
fig.patch.set_facecolor(PAPER)
fig.text(0.035, 0.955, "Who gets talked about in Parliament?", family=DISP, fontsize=31, fontweight="bold", color=INK, va="top")
fig.text(0.035, 0.895, f"{R['n']['main']:,} UK towns and cities: House of Commons mentions (\"in <place>\", 2005 to 2025) against what each place's\nEnglish Wikipedia views in 2024 and its population predict", fontsize=13.5, color=MUT, va="top")
# map
ax = fig.add_axes([0.01, 0.15, 0.5, 0.69]); ax.set_facecolor(SEA)
patch(ax, irl, fc="#F1EDE4", ec="#BDB6A8", lw=0.4)
patch(ax, uk, fc="#FFFDF8", ec="#8E8576", lw=0.6)
x, y = tr.transform(I.lon.values, I.lat.values)
o = np.argsort(I.expected.values)
ax.scatter(x[o], y[o], c=I.log2oe.clip(-3, 3).values[o], cmap=CMAP, norm=NORM, s=(5 + 8 * np.sqrt(I.expected.clip(0, 400)) / 3).values[o],
           lw=0.35, edgecolor="white", zorder=3)
ax.set_xlim(-60000, 690000); ax.set_ylim(-10000, 1000000); ax.set_aspect("equal"); ax.axis("off")
# labels on sea, with short leader lines that do not cross (positions checked by a search for boxes clear of land and dots)
lab = [("Newtownards", (220000, 500000)), ("Redcar", (560000, 560000)), ("Kettering", (600000, 375000)), ("Port Talbot", (150000, 150000)),
       ("Peterhead", (520000, 880000))]
for t, (tx, ty) in lab:
    r = I[I.term == t].iloc[0]; px, py = tr.transform(r.lon, r.lat)
    ax.annotate(f"{t}\n{r.oe:.1f}x" if r.oe >= 1 else f"{t}\n1/{1 / r.oe:.0f}", (px, py), (tx, ty), fontsize=11, color=INK, ha="center", va="center",
                path_effects=HALO, arrowprops=dict(arrowstyle="-", color=MUT, lw=0.7, shrinkA=10, shrinkB=3), zorder=6)
# legend
cax = fig.add_axes([0.30, 0.085, 0.17, 0.016])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=NORM, cmap=CMAP), cax=cax, orientation="horizontal", ticks=[-3, -1.5, 0, 1.5, 3])
cb.ax.set_xticklabels(["1/8", "", "1", "", "8x"], fontsize=9.5); cb.outline.set_visible(False)
fig.text(0.04, 0.115, "Commons mentions against expectation\nblue: talked about less, red: more", fontsize=10.5, color=INK, va="top")
fig.text(0.04, 0.06, "Dot size: expected mentions", fontsize=9.5, color=MUT)
# right: stat cards
def card(x0, y0, big, txt, col):
    fig.text(x0, y0, big, family=DISP, fontsize=40, fontweight="bold", color=col, va="top")
    fig.text(x0, y0 - 0.075, txt, fontsize=12.5, color=INK, va="top", linespacing=1.3)
card(0.54, 0.83, f"{R['prose']['seat_x']:.2f}x", "the mentions for a town with\na Commons seat named after it\n(same views and population;\n95% interval "
     f"{1 + R['M1']['seat']['lo'] / 100:.2f}x to {1 + R['M1']['seat']['hi'] / 100:.2f}x)", RED)
card(0.79, 0.83, f"{R['desc']['spearman_views_mentions']:.2f}", "rank correlation between\nWikipedia views and\nCommons mentions", INK)
card(0.54, 0.6, f"+{R['prose']['views_double']}%", "more mentions when a place gets\ntwice the Wikipedia views\n(not +100%)", BLUE)
card(0.79, 0.6, f"+{R['M1']['Wales_vs_england']['b']:.0f}%", "for Welsh places against\nEnglish ones with the same\nviews and population", RED)
# right bottom: top and bottom lists
fig.text(0.54, 0.37, "Talked about most for their profile", fontsize=13, fontweight="bold", color=RED)
fig.text(0.79, 0.37, "Talked about least", fontsize=13, fontweight="bold", color=BLUE)
for j, r in enumerate(R["rank"]["over"][:8]):
    fig.text(0.54, 0.335 - j * 0.03, f"{r['term']}{' *' if r['seat'] else ''}", fontsize=11.5, color=INK)
    fig.text(0.74, 0.335 - j * 0.03, f"{r['oe']:.1f}x", fontsize=11.5, color=INK, ha="right", family="IBM Plex Mono")
for j, r in enumerate(R["rank"]["under"][:8]):
    fig.text(0.79, 0.335 - j * 0.03, f"{r['term']}{' *' if r['seat'] else ''}", fontsize=11.5, color=INK)
    fig.text(0.975, 0.335 - j * 0.03, f"1/{1 / max(r['oe'], 0.01):.0f}", fontsize=11.5, color=INK, ha="right", family="IBM Plex Mono")
fig.text(0.54, 0.075, "* part of a Commons seat name.  Expected: from 2024 Wikipedia views and population (places expected\nto get 20+ mentions). Long formal names often shortened in speech are left out of the lists.", fontsize=9.5, color=MUT)
fig.text(0.035, 0.018, "Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0), Wikipedia pageviews 2024; Wikidata (CC0); ONS.  "
         "Dr Tristan Hotham  ·  maps.tristanhotham.com/wiki-vs-hansard", fontsize=8.8, color=MUT, family="IBM Plex Mono")
out = os.path.join(HERE, "wiki_vs_hansard_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER)
print(out)
