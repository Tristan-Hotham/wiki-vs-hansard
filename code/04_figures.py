"""Step 4: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf, vector)
and header.png (1200 x 630). Light paper background; diverging red (Parliament talks more than attention predicts) to
blue (less), grey midpoint; validated with the dataviz palette checker (#B4442E / #2F6A9E, CVD dE 16.9)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np, pandas as pd
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as stransform, unary_union
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
RED, BLUE, GREY = "#B4442E", "#2F6A9E", "#C9C2B4"
CMAP = LinearSegmentedColormap.from_list("d", [BLUE, "#8FB0CF", GREY, "#E3A58F", RED])
NORM = TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3)
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
I = pd.read_csv(f"{DATA}/index.csv")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD):
    os.makedirs(d_, exist_ok=True)


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.055, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s="Data: Hansard (Open Parliament Licence v3.0); Wikipedia pageviews 2024; Wikidata (CC0). maps.tristanhotham.com/wiki-vs-hansard"):
    fig.text(0.04, 0.015, s, fontsize=8.5, family=MONO, color=MUT)


# ---------- 1. scatter: public attention against parliamentary attention
fig = plt.figure(figsize=(11, 8.2))
title(fig, "What the public looks up, and what Parliament talks about",
      f"{R['n']['main']:,} UK places: English Wikipedia views in 2024 against Commons contributions saying \"in <place>\", 2005 to 2025")
ax = fig.add_axes([0.09, 0.1, 0.66, 0.76])
x, y = I.views, I.in_05_25 + 1
sc = ax.scatter(x, y, c=I.log2oe.clip(-3, 3), cmap=CMAP, norm=NORM, s=14 + 3 * np.log10(I.pop_main), lw=0.4, edgecolor=PAPER, alpha=0.9, zorder=3)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Wikipedia pageviews, 2024 (log scale)"); ax.set_ylabel("Commons contributions with \"in <place>\", 2005 to 2025, plus one (log scale)")
ax.grid(True, which="major", color=RULE, lw=0.6, zorder=0)
lab = {"London": (8, -12), "Kettering": (-10, 8), "Redcar": (8, 4), "Newtownards": (-12, 8), "Saltburn-by-the-Sea": (6, -4), "City of London": (6, 3),
       "Glasgow": (8, 4), "Cardiff": (8, -6), "Birmingham": (8, -10), "Newcastle upon Tyne": (6, -2), "Bath": (6, -8), "Port Talbot": (6, 2),
       "Thirsk": (6, 3), "Broughty Ferry": (6, 0), "Stoke-on-Trent": (6, 3), "Southport": (6, -9)}
for t, (dx, dy) in lab.items():
    r = I[I.term == t]
    if len(r):
        r = r.iloc[0]
        ax.annotate(t, (r.views, r.in_05_25 + 1), xytext=(dx, dy), textcoords="offset points", fontsize=9.5, color=INK,
                    ha="left" if dx > 0 else "right", path_effects=HALO, zorder=5)
cax = fig.add_axes([0.8, 0.35, 0.025, 0.4])
cb = fig.colorbar(sc, cax=cax, ticks=[-3, -2, -1, 0, 1, 2, 3])
cb.ax.set_yticklabels(["1/8", "1/4", "1/2", "as expected", "2x", "4x", "8x"], fontsize=9)
cb.outline.set_visible(False)
fig.text(0.79, 0.78, "Mentions against what\nviews and population\npredict", fontsize=10, color=INK, va="bottom")
fig.text(0.79, 0.3, f"Rank correlation {R['desc']['spearman_views_mentions']:.2f}\nDot size: population\n"
         "Long formal names (Saltburn-\nby-the-Sea, City of London)\nare said in short forms in\ndebate: measurement artefacts", fontsize=9, color=MUT, va="top")
foot(fig); out(fig, "scatter")

# ---------- 2. map of the index
tr = Transformer.from_crs(4326, 27700, always_xy=True)
C = jload(f"{GEO}/counties_uk.geojson")["features"]
uk = unary_union([shape(f["geometry"]).buffer(0.002) for f in C]).buffer(-0.002).simplify(0.003)
ukp = stransform(lambda a, b, z=None: tr.transform(a, b), uk)
NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]
irl = stransform(lambda a, b, z=None: tr.transform(a, b), next(shape(f["geometry"]) for f in NE if f["properties"]["ADM0_A3"] == "IRL"))
from matplotlib.patches import PathPatch
from matplotlib.path import Path


def patch(ax, g, **kw):
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.geom_type != "Polygon": continue
        v, c = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = np.asarray(ring.coords); v += cs.tolist(); c += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(v, c), **kw))


def basemap(ax, ext=(-30000, 690000, -10000, 1080000)):
    ax.set_facecolor("#EAF0F2")
    patch(ax, irl, fc="#F2EEE6", ec="#BDB6A8", lw=0.4)
    patch(ax, ukp, fc="#FBF7EE", ec="#8E8576", lw=0.6)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)


px, py = tr.transform(I.lon.values, I.lat.values)
I["x"], I["y"] = px, py
fig = plt.figure(figsize=(11, 12.5))
title(fig, "Talked about more, or less, than the public's interest predicts",
      "Commons \"in <place>\" mentions 2005 to 2025 against the number expected from 2024 Wikipedia views and population", y=0.975)
ax = fig.add_axes([0.02, 0.05, 0.62, 0.85]); basemap(ax)
o = I.sort_values("expected")
ax.scatter(o.x, o.y, c=o.log2oe.clip(-3, 3), cmap=CMAP, norm=NORM, s=6 + 9 * np.sqrt(o.expected.clip(0, 400)) / 3, lw=0.35, edgecolor="white", zorder=3)
for t in ("Newtownards", "Redcar", "Kettering", "Dudley", "Stroud", "Port Talbot", "Peterhead", "Broughty Ferry", "Bideford", "Whitley Bay", "Prescot", "Oxted"):
    r = I[I.term == t].iloc[0]
    ax.annotate(t, (r.x, r.y), xytext=(5, 3), textcoords="offset points", fontsize=9, color=INK, path_effects=HALO, zorder=5)
ax2 = fig.add_axes([0.64, 0.5, 0.34, 0.36]); basemap(ax2, (500000, 570000, 150000, 210000))
L_ = I[(I.x > 500000) & (I.x < 570000) & (I.y > 150000) & (I.y < 210000)].sort_values("expected")
ax2.scatter(L_.x, L_.y, c=L_.log2oe.clip(-3, 3), cmap=CMAP, norm=NORM, s=10 + 9 * np.sqrt(L_.expected.clip(0, 400)) / 3, lw=0.4, edgecolor="white", zorder=3)
ax2.set_title("London", fontsize=12, color=INK, loc="left")
for s in ax2.spines.values(): s.set_visible(True); s.set_color(MUT)
cax = fig.add_axes([0.68, 0.3, 0.26, 0.022])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=NORM, cmap=CMAP), cax=cax, orientation="horizontal", ticks=[-3, -2, -1, 0, 1, 2, 3])
cb.ax.set_xticklabels(["1/8", "1/4", "1/2", "1", "2x", "4x", "8x"], fontsize=9); cb.outline.set_visible(False)
fig.text(0.68, 0.34, "Observed / expected mentions\nred: Parliament talks more\nblue: Parliament talks less", fontsize=10.5, color=INK)
fig.text(0.68, 0.24, f"{R['n']['main']:,} places; dot size grows with\nthe expected number of mentions", fontsize=9.5, color=MUT, va="top")
foot(fig); out(fig, "map")

# ---------- 3. coefficients: what predicts parliamentary attention (M1), with 95% CIs
M = R["M1"]
rows = [("Seat named after the place", M["seat"]), ("Wales vs England", M["Wales_vs_england"]), ("Scotland vs England", M["Scotland_vs_england"]),
        ("Northern Ireland vs England", M["Northern Ireland_vs_england"]), ("North vs South of England", M["north_vs_south"]),
        ("London region vs rest of England", M["london_vs_rest_england"]), ("Deprivation, +1 SD", M["depr"]),
        ("Wikipedia views doubled", {k: 100 * (2 ** M["views"][k] - 1) for k in ("b", "lo", "hi")}),
        ("Population doubled", {k: 100 * (2 ** M["pop"][k] - 1) for k in ("b", "lo", "hi")})]
DL = R["robust_drop_london"]
alt = {"Wales vs England": DL["wales"], "North vs South of England": DL["ns"], "London region vs rest of England": DL["london"]}
fig = plt.figure(figsize=(11, 7.4))
title(fig, "What goes with more mentions in the Commons", f"Change in \"in <place>\" mentions, %, holding the other factors fixed (Poisson model, N = {M['n']:,}; 95% intervals clustered by council)")
ax = fig.add_axes([0.33, 0.14, 0.62, 0.7])
for i, (lab_, v) in enumerate(rows[::-1]):
    col = RED if v["lo"] > 0 else BLUE if v["hi"] < 0 else MUT
    ax.plot([v["lo"], v["hi"]], [i, i], color=col, lw=2.2, solid_capstyle="round")
    ax.plot(v["b"], i, "o", color=col, ms=8, mec=PAPER, mew=1.5, zorder=4)
    ax.text(-0.02, i, lab_, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=11.5, color=INK)
    if lab_ in alt:
        a = alt[lab_]
        ax.plot(a["b"], i - 0.28, "D", color="none", mec=INK, ms=6, mew=1.1, zorder=4)
ax.axvline(0, color=INK, lw=0.8); ax.set_yticks([]); ax.set_ylim(-0.7, len(rows) - 0.4)
ax.grid(True, axis="x", color=RULE, lw=0.6); ax.spines["left"].set_visible(False)
ax.set_xlabel("% change in mentions")
ax.text(0.99, 0.02, "open diamond: same model without the single\nobservation for London itself", transform=ax.transAxes, ha="right", fontsize=9.5, color=MUT)
foot(fig); out(fig, "effects")

# ---------- 4. event study, places named in a new seat in 2024
ev = R["event"]["2024"]["coef"]
ks = sorted(int(k) for k in ev) + [-1]; ks.sort()
b = [0 if k == -1 else ev[str(k)]["b"] for k in ks]; lo = [0 if k == -1 else ev[str(k)]["lo"] for k in ks]; hi = [0 if k == -1 else ev[str(k)]["hi"] for k in ks]
fig = plt.figure(figsize=(11, 6.6))
title(fig, "When a town gets a seat named after it", f"{R['event']['2024']['n_treated']} places first named in a Commons seat at the 2024 election, against {R['event']['2024']['n_control']:,} places whose status never changed:\n\"in <place>\" mentions relative to 2023, %, with 95% intervals (place and year fixed effects)")
ax = fig.add_axes([0.09, 0.12, 0.86, 0.66])
yrs = [2024 + k for k in ks]
ax.fill_between(yrs, lo, hi, color="#E3A58F", alpha=0.35, lw=0)
ax.plot(yrs, b, "-o", color=RED, lw=2, ms=6, mec=PAPER)
ax.axhline(0, color=INK, lw=0.8); ax.axvline(2023.5, color=MUT, lw=1, ls=(0, (3, 3)))
ax.text(2023.6, max(hi) * 0.92, "2024 election:\nnew seat names", fontsize=10, color=INK)
ax.set_xticks(yrs); ax.set_ylabel("% difference from 2023"); ax.grid(True, axis="y", color=RULE, lw=0.6)
ax.text(2015, max(hi) * 0.92, "Mentions were already rising before the change,\nso part of the jump is a trend, not the name", fontsize=10, color=MUT, va="top")
foot(fig); out(fig, "event")

# ---------- 5. robustness: views elasticity and seat effect across checks
rb = [x for x in R["robust"] if x.get("views") and x.get("seat") and "OLS" not in x["label"]]
fig = plt.figure(figsize=(11, 9.4))
title(fig, "Do the two main results survive other choices?", "Each row re-runs the main model with one change; dashed lines show the main estimate")
for j, (key, nm, tf) in enumerate((("views", "Elasticity of mentions with respect to views", lambda v: v), ("seat", "Seat named after the place, % more mentions", lambda v: v))):
    ax = fig.add_axes([0.4 + j * 0.3, 0.08, 0.26, 0.77])
    for i, x in enumerate(rb[::-1]):
        v = x[key]
        ax.plot([v["lo"], v["hi"]], [i, i], color=INK, lw=1.6); ax.plot(v["b"], i, "o", color=RED if key == "seat" else BLUE, ms=6, mec=PAPER)
        if j == 0:
            ax.text(-0.04, i, x["label"].replace(" (added after reading the rankings)", " *"), transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=9.5, color=INK)
    m = R["M1"][key]["b"]; ax.axvline(m, color=MUT, lw=1, ls=(0, (4, 3)))
    ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.set_title(nm, fontsize=10.5, color=INK, loc="left", wrap=True)
    ax.grid(True, axis="x", color=RULE, lw=0.6); ax.set_ylim(-0.7, len(rb) - 0.3)
    if key == "seat": ax.axvline(0, color=INK, lw=0.8)
fig.text(0.04, 0.045, "* added after reading the rankings", fontsize=9, color=MUT)
foot(fig); out(fig, "robust")

# ---------- 6. ranked places: over and under
ov, un = R["rank"]["over"][:12], R["rank"]["under"][:12]
fig = plt.figure(figsize=(11, 8.4))
title(fig, "Talked about most and least, for their profile", f"Observed against expected \"in <place>\" mentions, 2005 to 2025, among {R['rank']['n']} places expected to get at least 20")
for j, (lst, col, nm) in enumerate(((ov, RED, "More than expected"), (un, BLUE, "Less than expected"))):
    ax = fig.add_axes([0.2 + j * 0.48, 0.15, 0.28, 0.69])
    for i, r in enumerate(lst[::-1]):
        ax.plot([r["expected"], r["mentions"] + 0.5], [i, i], color=col, lw=1.8, alpha=0.7)
        ax.plot(r["expected"], i, "o", mfc=PAPER, mec=INK, ms=6); ax.plot(r["mentions"] + 0.5, i, "o", color=col, ms=7, mec=PAPER)
        ax.text(-0.03, i, r["term"] + (" •" if r["seat"] else ""), transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=10.5, color=INK)
    ax.set_xscale("log"); ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.grid(True, axis="x", color=RULE, lw=0.6)
    tk = [1, 3, 10, 30, 100, 300, 1000]
    ax.set_xticks(tk); ax.set_xticklabels([str(t) for t in tk]); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_title(nm, fontsize=12.5, color=col, loc="left"); ax.set_xlabel("mentions (log scale)")
fig.text(0.04, 0.05, "open circle: expected from views and population; filled: observed;  • name is part of a Commons seat name", fontsize=9.5, color=MUT)
foot(fig); out(fig, "ranks")

# ---------- 7. the link over time (exploratory gradient and the two periods)
G = R["exploratory_gradient"]
fig = plt.figure(figsize=(11, 6.2))
title(fig, "Wikipedia attention tracks Parliament's past better than its present", "Elasticity of \"in <place>\" mentions in each period with respect to 2024 Wikipedia views, same controls, 95% intervals (exploratory)")
ax = fig.add_axes([0.1, 0.13, 0.85, 0.65])
labs = list(G)
for i, k in enumerate(labs):
    v = G[k]; ax.plot([i, i], [v["lo"], v["hi"]], color=INK, lw=2); ax.plot(i, v["b"], "o", color=BLUE, ms=10, mec=PAPER)
    ax.text(i + 0.08, v["b"], f"{v['b']:.2f}", va="center", fontsize=11, color=INK)
ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs); ax.set_ylabel("elasticity"); ax.grid(True, axis="y", color=RULE, lw=0.6)
ax.set_xlim(-0.5, len(labs) - 0.5)
foot(fig); out(fig, "time")

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.patch.set_facecolor(PAPER)
ax = fig.add_axes([0.6, 0.02, 0.38, 0.96]); basemap(ax, (-30000, 690000, -10000, 1080000))
o = I.sort_values("expected")
ax.scatter(o.x, o.y, c=o.log2oe.clip(-3, 3), cmap=CMAP, norm=NORM, s=4 + 5 * np.sqrt(o.expected.clip(0, 400)) / 3, lw=0.25, edgecolor="white", zorder=3)
fig.text(0.05, 0.84, "DATA STUDY · 2026", family=MONO, fontsize=12, color=MUT)
fig.text(0.05, 0.62, "Who gets\ntalked about?", family=DISP, fontsize=46, fontweight="bold", color=INK, va="bottom", linespacing=0.95)
fig.text(0.05, 0.47, "What the public looks up on Wikipedia\nagainst what MPs talk about in the Commons", fontsize=16, color=INK, va="top")
fig.text(0.05, 0.27, f"A seat named after a town:\n{R['prose']['seat_x']:.1f} times the mentions", fontsize=17, color=RED, fontweight="bold", va="top")
fig.text(0.05, 0.06, "Dr Tristan Hotham · maps.tristanhotham.com/wiki-vs-hansard", family=MONO, fontsize=10.5, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER)
plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
