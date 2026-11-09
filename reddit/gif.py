"""Looping GIF of the best bit: mentions of the 96 places first named in a Commons seat in 2024, drawn year by year
(relative to 2023), against places whose status never changed. Run after code/03_results.py: python3 reddit/gif.py"""
import os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "code"))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image
from common import *
for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
plt.rcParams.update({"font.family": "Source Serif 4", "axes.unicode_minus": False})
R = jload(f"{DATA}/results.json"); ev = R["event"]["2024"]
ks = sorted([int(k) for k in ev["coef"]] + [-1])
b = [0 if k == -1 else ev["coef"][str(k)]["b"] for k in ks]; yrs = [2024 + k for k in ks]
frames = []
for n in list(range(1, len(yrs) + 1)) + [len(yrs)] * 6:
    fig = plt.figure(figsize=(8, 5), dpi=100); fig.patch.set_facecolor("#FAF6EC")
    ax = fig.add_axes([0.1, 0.13, 0.85, 0.62]); ax.set_facecolor("#FAF6EC")
    ax.plot(yrs[:n], b[:n], "-o", color="#B4442E", lw=2.5, ms=7)
    ax.axhline(0, color="#2B2119", lw=0.8); ax.axvline(2023.5, color="#6E604E", ls=(0, (3, 3)))
    ax.set_xlim(2014.5, 2025.5); ax.set_ylim(-60, 110); ax.set_xticks(yrs); ax.tick_params(labelsize=9)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.set_ylabel("% vs 2023")
    ax.text(2023.6, 95, "2024 election:\nnew seat names", fontsize=9, va="top")
    fig.text(0.05, 0.93, "When a town gets a seat named after it", family=DISP, fontsize=19, fontweight="bold", color="#2B2119", va="top")
    fig.text(0.05, 0.85, f"Commons mentions of the {ev['n_treated']} places first named in a seat in 2024 (already rising before)", fontsize=10, color="#6E604E", va="top")
    fig.text(0.05, 0.02, "maps.tristanhotham.com/wiki-vs-hansard", fontsize=8, color="#6E604E")
    buf = io.BytesIO(); fig.savefig(buf, format="png", facecolor=fig.get_facecolor()); plt.close(fig)
    frames.append(Image.open(buf).convert("P", palette=Image.ADAPTIVE))
out = os.path.join(HERE, "wiki_vs_hansard.gif")
frames[0].save(out, save_all=True, append_images=frames[1:], duration=450, loop=0, optimize=True)
print(out, os.path.getsize(out) // 1024, "KB")
