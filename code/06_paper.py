"""Step 6: the paper. Fills code/paper_template.tex from data/results.json and data/models.csv, adds the tables, compiles
with xelatex. Output: release/paper/Hotham_Who_Gets_Talked_About.pdf and .tex beside the f_*.pdf figures.
The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24092583 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/06_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Who_Gets_Talked_About"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    for k in ("f0", "f1", "f2", "f3"):
        if f == k: return f"{float(v):.{k[1]}f}".replace("-", "$-$")
    return tex(str(v))


M = pd.read_csv(f"{DATA}/models.csv")
D = pd.read_csv(f"{DATA}/places.csv")
I = pd.read_csv(f"{DATA}/index.csv")
sf = R["sample_flow"]; d = R["data"]
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{From Hansard place terms to the analysis sample.}\\label{tab:flow}\\begin{tabular}{lr}\\toprule Step & Places\\\\\\midrule\n"
      f"Hansard place terms (Mentioned in the House) & {d['n_terms']:,}\\\\\n"
      f"\\quad matched to a Wikidata settlement article & {d['n_matched']:,}\\\\\n"
      f"\\quad with 2024 pageviews collected & {d['n_matched_views']:,}\\\\\n"
      f"\\quad less: flagged in Hansard (shared, namesake, word) or merged duplicate & $-${sf['hansard_flag_removed']}\\\\\n"
      f"\\quad less: name collision with an equally viewed namesake & $-${sf['collide_removed']}\\\\\n"
      f"\\quad less: suspect (probably renamed) article & $-${sf['suspect_removed']}\\\\\n"
      f"\\quad less: zero pageviews & $-${sf['zero_views_removed']}\\\\\\midrule\n"
      f"Main sample & {R['n']['main']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
B = I.copy()
rows = ""
for nat in ("England", "Scotland", "Wales", "Northern Ireland", "All"):
    g = B if nat == "All" else B[B.nation == nat]
    rows += (f"{nat} & {len(g):,} & {int(g.pop_main.median()):,} & {int(g.views.median()):,} & {g.in_05_25.median():.0f} & {int(g.in_05_25.sum()):,} & "
             f"{100 * (g.seat_share > 0).mean():.0f}\\\\\n") + ("\\midrule\n" if nat == "Northern Ireland" else "")
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{The main sample by nation: medians of population, 2024 pageviews and ``in'' mentions 2005 to 2025, total mentions, and the share of places that were part of a seat name.}\\label{tab:desc}"
      "\\begin{tabular}{lrrrrrr}\\toprule Nation & $N$ & Population & Views & Mentions & Total mentions & Seat name (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
LAB = {"lv": "log pageviews 2024", "lp": "log population", "seat_share": "Seat-name share", "ldist": "log(1 + km to London)", "depr": "Deprivation (SD)", "disamb": "Qualified title",
       "seat_exact_share": "Exact seat name share"}
def coef_col(model, keys):
    g = M[M.model == model].set_index("term")
    out = {}
    for k in keys:
        if k in g.index:
            r = g.loc[k]; st = "^{***}" if r.p < .001 else "^{**}" if r.p < .01 else "^{*}" if r.p < .05 else ""
            out[k] = (f"${r.b:.3f}{st}$".replace("-", "-"), f"({r.se:.3f})")
        else:
            out[k] = ("", "")
    return out, int(g.n.iloc[0])
mods = [("M0 no views", "M0"), ("M1 main", "M1"), ("M1 without distance", "M1 no distance"), ("R1 OLS log(1+Y)", "OLS log(1+Y)")]
keys = ["lv", "lp", "seat_share", "ldist", "depr", "disamb"]
cols = [coef_col(m, keys) for m, _ in mods]
body = ""
for k in keys:
    body += LAB[k] + " & " + " & ".join(c[0][k][0] for c in cols) + "\\\\\n & " + " & ".join(c[0][k][1] for c in cols) + "\\\\\n"
body += "\\midrule Region fixed effects & yes & yes & yes & yes\\\\\n$N$ & " + " & ".join(f"{c[1]:,}" for c in cols) + "\\\\\n"
body += f"Clusters (local authorities) & \\multicolumn{{4}}{{c}}{{{R['n']['lad_clusters']}}}\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Main models of ``in'' mentions, 2005 to 2025. Columns 1 to 3: Poisson pseudo-maximum likelihood; column 4: OLS of $\\log(1+Y)$. Standard errors clustered by local authority in parentheses. $^{*}p<.05$, $^{**}p<.01$, $^{***}p<.001$. Region coefficients in Appendix Table~\\ref{tab:full}.}\\label{tab:main}"
      "\\begin{tabular}{lcccc}\\toprule & M0 & M1 (main) & M1, no distance & OLS\\\\\\midrule\n" + body + "\\bottomrule\\end{tabular}\\end{table}")
pc = lambda v: f"{v['b']:.0f} [{v['lo']:.0f}, {v['hi']:.0f}]".replace("-", "$-$")
TW = ("\\begin{table}[tbp]\\centering\\small\\caption{Within-place models of yearly ``in'' mentions (PPML, place and year fixed effects, standard errors clustered by local authority). Percentage differences with 95\\% intervals.}\\label{tab:within}"
      "\\begin{tabular}{lrrr}\\toprule Model & Seat name now & Seat name in two years & Place-years\\\\\\midrule\n"
      f"M2, 2005 to 2025 & {pc(R['M2']['seat'])} & & {R['M2']['n_obs']:,}\\\\\n"
      f"M2 with lead (placebo) & {pc(R['M2_lead']['seat'])} & {pc(R['M2_lead']['lead2'])} & {R['M2_lead']['n_obs']:,}\\\\\n"
      f"Fake timing (lead only) & & {pc(R['M2_fake']['lead2'])} & \\\\\n"
      f"2005 to 2023 (2010 change only) & {pc(R['M2_to2023']['seat'])} & & {R['M2_to2023']['n_obs']:,}\\\\\n"
      f"2005 to 2023 with lead & {pc(R['M2_to2023_lead']['seat'])} & {pc(R['M2_to2023_lead']['lead2'])} & \\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for j, (a, b) in enumerate(zip(R["rank"]["over"], R["rank"]["under"])):
    rows += (f"{tex(a['term'])}{'$^\\dagger$' if a['seat'] else ''} & {a['views']:,} & {a['mentions']:,} & {a['expected']:.0f} & {a['oe']:.2f} & "
             f"{tex(b['term'])}{'$^\\dagger$' if b['seat'] else ''} & {b['views']:,} & {b['mentions']:,} & {b['expected']:.0f} & {b['oe']:.2f}\\\\\n")
TR = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The 15 places with the most and fewest ``in'' mentions relative to expectation from 2024 pageviews and population (places expected to receive at least 20 mentions, name-form flagged places excluded). $^\\dagger$ part of a seat name in 2005 to 2025.}\\label{tab:rank}"
      "\\setlength{\\tabcolsep}{3.5pt}\\begin{tabular}{lrrrr@{\\hskip 14pt}lrrrr}\\toprule \\multicolumn{5}{c}{More than expected} & \\multicolumn{5}{c}{Less than expected}\\\\\\cmidrule(r){1-5}\\cmidrule(l){6-10}"
      "Place & Views & Obs. & Exp. & Ratio & Place & Views & Obs. & Exp. & Ratio\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
grp = None
for x in R["robust"]:
    if x["group"] != grp:
        rows += f"\\multicolumn{{7}}{{l}}{{\\textit{{{tex(x['group'])}}}}}\\\\\n"; grp = x["group"]
    f = lambda k: pc(x[k]) if x.get(k) else ""
    v = x["views"]
    rows += (f"\\quad {tex(x['label'])} & {x['n']:,} & {v['b']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}] & {f('seat')} & {f('wales')} & {f('dev')} & {f('ns')}\\\\\n")
TB = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Robustness checks. Elasticity with respect to pageviews; seat-name, Wales, devolved-nation and north versus south contrasts as percentage differences, 95\\% intervals in brackets. The OLS row reports $\\exp(b)-1$ of the log-scale coefficients.}\\label{tab:robust}"
      "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{p{5.3cm}rlllll}\\toprule Check & $N$ & Views & Seat name & Wales & Devolved & North/South\\\\\\midrule\n" + rows +
      f"\\midrule\\multicolumn{{7}}{{l}}{{Main model M1: $N$ = {R['M1']['n']:,}, views {R['M1']['views']['b']:.2f}, seat {pc(R['M1']['seat'])}, Wales {pc(R['M1']['Wales_vs_england'])}}}\\\\\n"
      f"\\multicolumn{{7}}{{l}}{{Permutation of seat names (1,000 draws): observed {R['perm']['obs']:.3f}, permutation mean {R['perm']['mean']:.3f}, sd {R['perm']['sd']:.3f}, $p$ = {R['perm']['p']:.3f}}}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
g = M[M.model == "M1 main"]
def tl(term):
    term = term.replace("C(region, contr.treatment('South East'))[T.", "Region: ").rstrip("]")
    return tex(LAB.get(term, "Constant" if term == "Intercept" else term))
rows = "".join(f"{tl(r.term)} & {r.b:.3f} & {r.se:.3f} & {r.p:.3f}\\\\\n" for r in g.itertuples())
TFULL = ("\\begin{table}[tbp]\\centering\\small\\caption{M1 in full (PPML; reference region South East; standard errors clustered by local authority).}\\label{tab:full}"
         "\\begin{tabular}{lrrr}\\toprule Term & $b$ & SE & $p$\\\\\\midrule\n" + rows + f"\\midrule $N$ & {R['M1']['n']:,} & & \\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{tex(x['left_out'])} & {x['n']:,} & {x['views']['b']:.2f} [{x['views']['lo']:.2f}, {x['views']['hi']:.2f}] & {pc(x['seat'])} & {pc(x['dev'])}\\\\\n" for x in R["loro"])
TL = ("\\begin{table}[tbp]\\centering\\small\\caption{Leave one region out: M1 re-estimated without each region.}\\label{tab:loro}"
      "\\begin{tabular}{lrlll}\\toprule Region left out & $N$ & Views & Seat name (\\%) & Devolved vs England (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_FLOW", TF), ("TABLE_DESC", TD), ("TABLE_MAIN", TM), ("TABLE_WITHIN", TW), ("TABLE_RANK", TR), ("TABLE_ROBUST", TB), ("TABLE_FULL", TFULL), ("TABLE_LORO", TL)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24092583", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("References")[0] if "References" in txt else txt
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
