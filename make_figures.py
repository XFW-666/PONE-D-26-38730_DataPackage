# -*- coding: utf-8 -*-
"""Final figures: fig1 rectangular boxes; fig2 advanced bar panels; fig4 classic integrated CFA
path diagram (ovals+boxes+curved correlations) with clean spacing; fig9 orthogonal arrows.
Other figures unchanged."""
import sys, io, json, warnings, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, Rectangle, FancyBboxPatch
from textwrap import wrap

plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
import os
BASE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(f"{BASE}/results.json", encoding="utf-8"))
MAP = {"非常不同意": 1, "有点不同意": 2, "不同意": 3, "一般": 4, "有点同意": 5, "同意": 6, "非常同意": 7}
df = pd.read_csv(f"{BASE}/public_data.csv")
cols = list(df.columns)
def qcol(n):
    for c in cols:
        if c.startswith(f"{n}\u3001"):
            return c
    raise KeyError(n)
items = pd.DataFrame({
    **{f"A{i}": df[qcol(i)].map(MAP) for i in range(1, 7)},
    **{f"U{i}": df[qcol(i + 6)].map(MAP) for i in range(1, 7)},
    **{f"P{i}": df[qcol(i + 12)].map(MAP) for i in range(1, 7)},
    **{f"V{i}": df[qcol(i + 18)].map(MAP) for i in range(1, 7)},
})
N = len(df)
comp = pd.DataFrame({"ANTH": items[[f"A{i}" for i in range(1, 7)]].mean(axis=1),
                     "UV": items[[f"U{i}" for i in range(1, 7)]].mean(axis=1),
                     "PR": items[[f"P{i}" for i in range(1, 7)]].mean(axis=1),
                     "AV": items[[f"V{i}" for i in range(1, 7)]].mean(axis=1)})
LBL = {"ANTH": "Anthropomorphism", "UV": "Uncanny-valley perception",
       "PR": "Psychological reactance", "AV": "Avoidance intention"}
COL = {"ANTH": "#2c7fb8", "UV": "#4dab5f", "PR": "#8b7ec8", "AV": "#f0954f"}
IND = {"ANTH": "A", "UV": "U", "PR": "P", "AV": "V"}

def save(fig, name):
    fig.savefig(f"{BASE}/figures/{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)

os.makedirs(f"{BASE}/figures", exist_ok=True)

# ================= Fig 1: rectangular, text fitted =================
fig, ax = plt.subplots(figsize=(8.6, 3.1))
boxes = {"X": (0.010, "Anthropomorphism\nof AI agent (X)"),
         "M1": (0.270, "Uncanny-valley\nperception (M1)"),
         "M2": (0.530, "Psychological\nreactance (M2)"),
         "Y": (0.790, "Avoidance\nintention (Y)")}
BW, BH = 0.175, 0.34
for k, (x, t) in boxes.items():
    ax.add_patch(Rectangle((x, 0.33), BW, BH, fc="white", ec="black", lw=1.5, zorder=4))
    ax.text(x + BW / 2, 0.50, t, ha="center", va="center", fontsize=8.0, zorder=5)
for a, b, lbl in [("X", "M1", "a (H1)"), ("M1", "M2", "d21 (H2)"), ("M2", "Y", "b2 (H3)")]:
    x1 = boxes[a][0] + BW + 0.008; x2 = boxes[b][0] - 0.008
    ax.add_patch(FancyArrowPatch((x1, 0.50), (x2, 0.50), arrowstyle="-|>", mutation_scale=14, lw=1.5, zorder=3))
    ax.text((x1 + x2) / 2, 0.585, lbl, ha="center", va="center", fontsize=7.6, zorder=6,
            bbox=dict(fc="white", ec="none", pad=0.8))
xa, xb = boxes["X"][0] + BW / 2, boxes["M2"][0] + BW / 2
ax.plot([xa, xa, xb, xb], [0.69, 0.84, 0.84, 0.72], lw=1.3, color="black", zorder=2)
ax.add_patch(FancyArrowPatch((xb, 0.78), (xb, 0.695), arrowstyle="-|>", mutation_scale=14, lw=1.3, zorder=3))
ax.text((xa + xb) / 2, 0.88, "parallel path (anthropomorphism → reactance)", ha="center", fontsize=7.8)
xay, xby = boxes["X"][0] + BW / 2, boxes["Y"][0] + BW / 2
ax.plot([xay, xay, xby, xby], [0.31, 0.15, 0.15, 0.28], lw=1.3, color="black", zorder=2)
ax.add_patch(FancyArrowPatch((xby, 0.22), (xby, 0.315), arrowstyle="-|>", mutation_scale=14, lw=1.3, zorder=3))
ax.text((xay + xby) / 2, 0.07, "c′ (direct effect)", ha="center", fontsize=7.8)
ax.set_xlim(-0.005, 0.985); ax.set_ylim(0.02, 0.95); ax.axis("off")
save(fig, "fig1_conceptual")

# ================= Fig 2: horizontal bar panels (no pies) =================
demo = R["demo"]
EN = {
    "gender": {"A. 男": "Male", "B. 女": "Female", "C. 不愿透露": "Undisclosed"},
    "age": {"B. 18-25岁": "18–25", "C. 26-30岁": "26–30", "D. 31-40岁": "31–40", "E. 41-50岁": "41–50", "F. 50岁以上": "Over 50"},
    "edu": {"A. 高中及以下": "High school or below", "B. 大专": "Junior college", "C. 本科": "Bachelor", "D. 硕士": "Master", "E. 博士": "PhD"},
    "income": {"A. 2000以下": "< 2,000", "B. 2000-5000": "2,000–5,000", "C. 5001-10000": "5,001–10,000", "D. 10011-20000": "10,011–20,000", "D. 10001-20000": "10,001–20,000", "E. 20000以上": "> 20,000"},
}
TIT = {"gender": "(a) Gender", "age": "(b) Age group (years)", "edu": "(c) Education", "income": "(d) Monthly disposable income (CNY)"}
fig, axes = plt.subplots(2, 2, figsize=(8.6, 5.4))
for ax, key in zip(axes.ravel(), ["gender", "age", "edu", "income"]):
    d = demo[key]
    labels = [EN[key].get(k, k.split(". ", 1)[-1]) for k in d]
    pcts = [v[1] for v in d.values()]
    ns = [v[0] for v in d.values()]
    y = np.arange(len(labels))[::-1]
    ax.barh(y, pcts, height=0.62, color="#5b8db8", alpha=0.9, zorder=3)
    for yi, pc, n_ in zip(y, pcts, ns):
        ax.text(pc + 1.2, yi, f"{pc:.1f}%  (n = {n_})", va="center", fontsize=8.2, color="#333333")
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlim(0, max(pcts) * 1.45)
    ax.set_xlabel("% of respondents", fontsize=8)
    ax.set_title(TIT[key], fontsize=9.5, loc="left", weight="bold")
    ax.grid(axis="x", ls=":", lw=0.6, color="#cccccc", zorder=0)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
fig.suptitle(f"Sample composition (N = {N})", fontsize=10.5, y=1.005, x=0.02, ha="left", weight="bold")
fig.tight_layout()
save(fig, "fig2_sample")

# ================= Fig 3 unchanged logic (kept identical to previous) =================
fig, ax = plt.subplots(figsize=(7.2, 7.5))
cats = items.columns.tolist()
neg = np.zeros(24)
pos = np.zeros(24)
palette = {1: "#b2182b", 2: "#d6604d", 3: "#f4a582", 4: "#bdbdbd", 5: "#92c5de", 6: "#4393c3", 7: "#2166ac"}
for pt in range(1, 8):
    counts = items[cats].apply(lambda s: (s == pt).sum(axis=0)).values / N * 100
    if pt < 4:
        ax.barh(range(24), -counts, left=-neg, color=palette[pt], height=0.7)
        neg += counts
    elif pt == 4:
        ax.barh(range(24), -counts / 2, left=-neg, color=palette[4], height=0.7)
        ax.barh(range(24), counts / 2, left=pos, color=palette[4], height=0.7)
        neg += counts / 2
        pos += counts / 2
    else:
        ax.barh(range(24), counts, left=pos, color=palette[pt], height=0.7)
        pos += counts
ax.set_yticks(range(24)); ax.set_yticklabels(cats, fontsize=7.5)
ax.invert_yaxis(); ax.axvline(0, color="black", lw=0.8)
ax.set_xlim(-50, 100)
ax.set_xticks([-50, -25, 0, 25, 50, 75, 100])
ax.set_xlabel("% of respondents (disagreement ← neutral → agreement)")
ax.set_title("Response distributions for all 24 measurement items (N=%d)" % N, fontsize=9)
save(fig, "fig3_items")

# ================= Fig 4: classic integrated CFA path diagram =================
lds = R["loadings"]
LC = R["latent_corr_CFA"]
def lcorr(a, b):
    for k, v in LC.items():
        if set(k.split("~")) == {a, b} or set(k.split("-")) == {a, b}:
            return v
    return None
fig, ax = plt.subplots(figsize=(12.5, 7.4))
xs = {"ANTH": 1.7, "UV": 4.8, "PR": 7.9, "AV": 11.0}
OY, OW, OH = 8.7, 2.7, 1.5
for g in ["ANTH", "UV", "PR", "AV"]:
    ax.add_patch(Ellipse((xs[g], OY), OW, OH, fc="white", ec=COL[g], lw=2.0, zorder=4))
    ax.text(xs[g], OY + 0.22, "\n".join(wrap(LBL[g], 18)), ha="center", va="center", fontsize=8.5, zorder=5)
    ax.text(xs[g], OY - 0.42, f"α = {R['desc'][g]['alpha']:.2f}, AVE = {R['desc'][g]['AVE']:.2f}",
            ha="center", va="center", fontsize=7.5, color="#444444", zorder=5)
    for i, l in enumerate(lds[g]):
        bx = xs[g] - 0.85 + (i % 3) * 0.85
        by = 5.3 - (i // 3) * 2.0
        ax.plot([xs[g], bx], [OY - OH / 2, by + 0.30], color=COL[g], lw=1.0, zorder=2)
        ax.add_patch(Rectangle((bx - 0.32, by - 0.30), 0.64, 0.60, fc="white", ec="black", lw=1.0, zorder=4))
        ax.text(bx, by, f"{IND[g]}{i+1}", ha="center", va="center", fontsize=8, zorder=5)
        ax.text(bx, by + 0.42, f"{l:.2f}", ha="center", va="center", fontsize=7.2, color=COL[g], zorder=6,
                bbox=dict(fc="white", ec="none", pad=0.6))
# adjacent inter-construct correlations (curved double-headed, no crossings)
for a, b in [("ANTH", "UV"), ("UV", "PR"), ("PR", "AV")]:
    x1, x2 = xs[a] + OW / 2 * 0.55, xs[b] - OW / 2 * 0.55
    r = FancyArrowPatch((x1, OY + 0.15), (x2, OY + 0.15), arrowstyle="<|-|>", mutation_scale=11,
                        lw=1.1, color="#555555", connectionstyle="arc3,rad=0.30", zorder=3)
    ax.add_patch(r)
    ax.text((x1 + x2) / 2, OY + 1.30, f"r = {lcorr(a,b):.2f}", ha="center", fontsize=8, color="#333333")
cf = R["CFA"]
ax.text(6.35, 1.45, f"Four-factor CFA: χ²({cf['df']}) = {cf['chi2']:.2f}, p = {cf['p']:.3f}, CFI = {cf['CFI']:.3f}, "
                    f"TLI = {cf['TLI']:.3f}, RMSEA = {cf['RMSEA']:.3f}, SRMR = {cf['SRMR']:.3f}  (N = {N}; all loadings p < 0.001)",
        ha="center", fontsize=9)
ax.text(6.35, 0.75, f"Remaining latent correlations: ANTH–PR = {lcorr('ANTH','PR'):.2f}, ANTH–AV = {lcorr('ANTH','AV'):.2f}, "
                    f"UV–AV = {lcorr('UV','AV'):.2f} (all p < 0.001)", ha="center", fontsize=8.5, color="#333333")
ax.set_xlim(0, 12.7); ax.set_ylim(0.2, 10.6); ax.axis("off")
save(fig, "fig4_cfa")

# ================= Fig 5-8, 10-12 unchanged =================
cc = R["corr_composite"]
pairs = list(cc.items())
fig, ax = plt.subplots(figsize=(5.6, 3.4))
for i, (k, v) in enumerate(pairs):
    ax.plot([0, v], [i, i], color="#bdbdbd", lw=1)
    ax.plot(v, i, "o", color="#2c7fb8")
    ax.text(v + 0.01, i, f"r = {v:.3f}***", va="center", fontsize=8)
ax.set_yticks(range(len(pairs))); ax.set_yticklabels([k.replace("-", " – ") for k, _ in pairs], fontsize=8)
ax.invert_yaxis(); ax.set_xlim(-0.02, 0.85); ax.set_xlabel("Pearson correlation (composite scores)")
ax.set_title("Inter-construct correlations (N=%d, ***p<.001)" % N, fontsize=9)
save(fig, "fig5_corr")

fig, ax = plt.subplots(figsize=(5.6, 3.2))
for i, g in enumerate(["ANTH", "UV", "PR", "AV"]):
    sq = np.sqrt(R["desc"][g]["AVE"])
    mx = max([v for k, v in cc.items() if g in k.split("-")])
    ax.plot([mx, sq], [i, i], color="#999", lw=2)
    ax.plot(mx, i, "s", color="#7f7f7f", label="largest r" if i == 0 else None)
    ax.plot(sq, i, "o", color="#2c7fb8", label="√AVE" if i == 0 else None)
ax.set_yticks(range(4)); ax.set_yticklabels(["ANTH", "UV", "PR", "AV"])
ax.invert_yaxis(); ax.legend(fontsize=8); ax.set_xlabel("Fornell–Larcker: √AVE exceeds all inter-construct correlations")
save(fig, "fig6_fl")

fig, ax = plt.subplots(figsize=(6.2, 3.6))
rng = np.random.default_rng(3)
for i, g in enumerate(["ANTH", "UV", "PR", "AV"]):
    v = comp[g].values
    parts = ax.violinplot([v], positions=[i], showmeans=False, showmedians=False, showextrema=False)
    for pc in parts["bodies"]:
        pc.set_facecolor(COL[g]); pc.set_alpha(0.5)
    ax.boxplot([v], positions=[i], widths=0.12, showfliers=False, patch_artist=True, boxprops={"facecolor": "white"})
    ax.scatter(i + rng.uniform(-0.06, 0.06, len(v)), v, s=2, alpha=0.25, color="black")
ax.set_xticks(range(4)); ax.set_xticklabels(["ANTH", "UV", "PR", "AV"])
ax.set_ylabel("Composite score (1–7)")
ax.set_title("Distributions of composite scores (N=%d)" % N, fontsize=9)
save(fig, "fig7_dist")

fig, axes = plt.subplots(2, 3, figsize=(8.5, 5.6))
comb = [("ANTH", "UV"), ("UV", "PR"), ("PR", "AV"), ("ANTH", "PR"), ("ANTH", "AV"), ("UV", "AV")]
for ax, (a, b) in zip(axes.ravel(), comb):
    x = comp[a]; y = comp[b]
    ax.scatter(x, y, s=4, alpha=0.35, color="#555")
    m_, b_ = np.polyfit(x, y, 1)
    xx = np.linspace(x.min(), x.max(), 50)
    ax.plot(xx, m_ * xx + b_, "--", color="black", lw=1)
    order_ = np.argsort(x.values)
    xs_, ys_ = x.values[order_], y.values[order_]
    frac = 0.6; win = int(frac * N)
    lx, ly = [], []
    for i in range(0, N, max(1, N // 40)):
        j0 = max(0, i - win // 2); j1 = min(N, j0 + win)
        d = np.abs(np.arange(j0, j1) - i) / (win / 2)
        w = (1 - np.clip(d, 0, 1)) ** 3
        lx.append(xs_[i]); ly.append(np.sum(w * ys_[j0:j1]) / np.sum(w))
    ax.plot(lx, ly, "-", color="#d62728", lw=1.4)
    r = np.corrcoef(x, y)[0, 1]
    ax.set_title(f"{a} vs {b}: r = {r:.2f}***", fontsize=8)
fig.suptitle("Pairwise associations (red: LOESS; black dashed: OLS)", fontsize=9)
fig.tight_layout(rect=[0, 0, 1, 0.96])
save(fig, "fig8_pairs")

# ================= Fig 9: orthogonal arrows =================
fig, ax = plt.subplots(figsize=(10.8, 4.8))
cx = {"ANTH": 1.3, "UV": 4.7, "PR": 8.1, "AV": 11.5}
EW, EH, CY = 2.6, 1.35, 4.0
for k, x in cx.items():
    ax.add_patch(Ellipse((x, CY), EW, EH, fc="white", ec=COL[k], lw=2.0, zorder=4))
    ax.text(x, CY, "\n".join(wrap(LBL[k], 16)), ha="center", va="center", fontsize=8.4, zorder=5)
pl = R["paths_latent"]
def h_arrow(a, b):
    x1 = cx[a] + EW / 2 + 0.06; x2 = cx[b] - EW / 2 - 0.06
    ax.add_patch(FancyArrowPatch((x1, CY), (x2, CY), arrowstyle="-|>", mutation_scale=15, lw=1.8, zorder=3))
    ax.text((x1 + x2) / 2, CY + 0.42, f"β = {pl[f'{a}->{b}']['std']:.3f}***", ha="center", fontsize=8.6, zorder=6,
            bbox=dict(fc="white", ec="none", pad=1.0))
h_arrow("ANTH", "UV"); h_arrow("UV", "PR"); h_arrow("PR", "AV")
def elbow(a, b, y_level, label, label_x=None):
    x_from, x_to = cx[a], cx[b]
    y_from = CY + EH / 2 + 0.06
    y_to = CY + EH / 2 + 0.06
    ax.plot([x_from, x_from, x_to], [y_from, y_level, y_level], color="black", lw=1.5, zorder=2)
    ax.add_patch(FancyArrowPatch((x_to, y_level), (x_to, y_to), arrowstyle="-|>", mutation_scale=15, lw=1.5, zorder=3))
    lx = label_x if label_x is not None else (x_from + x_to) / 2
    ax.text(lx, y_level + 0.28, label, ha="center", fontsize=8.4, zorder=6,
            bbox=dict(fc="white", ec="none", pad=1.0))
elbow("ANTH", "PR", 6.1, f"ANTH→PR: β = {pl['ANTH->PR']['std']:.3f} (n.s.)", label_x=3.0)
elbow("UV", "AV", 7.1, f"UV→AV: β = {pl['UV->AV']['std']:.3f}**", label_x=9.8)
x1, x2 = cx["ANTH"], cx["AV"]
y1 = CY - EH / 2 - 0.06
ax.plot([x1, x1, x2], [y1, 1.8, 1.8], color="black", lw=1.5, zorder=2)
ax.add_patch(FancyArrowPatch((x2, 1.8), (x2, y1), arrowstyle="-|>", mutation_scale=15, lw=1.5, zorder=3))
ax.text((x1 + x2) / 2, 1.35, f"c′ (ANTH→AV direct): β = {pl['ANTH->AV']['std']:.3f} (n.s.)", ha="center", fontsize=8.4)
s = R["SEM"]
ax.text(6.4, 0.35, f"Latent SEM: χ²({s['df']}) = {s['chi2']:.2f}, p = {s['p']:.3f}, CFI = {s['CFI']:.3f}, "
                   f"TLI = {s['TLI']:.3f}, RMSEA = {s['RMSEA']:.3f}, SRMR = {s['SRMR']:.3f}  (N = {N})",
        ha="center", fontsize=8.4)
ax.set_xlim(0, 12.8); ax.set_ylim(0, 8.0); ax.axis("off")
save(fig, "fig9_sem")

med = R["mediation_composite"]
rows = [("Total effect", "total_effect"), ("Direct effect (c′)", "cprime_ANTH_AV"),
        ("Indirect: ANTH→UV→AV", "ind_ANTH_UV_AV"), ("Indirect: ANTH→UV→PR→AV (serial)", "chain_ANTH_UV_PR_AV"),
        ("Indirect: ANTH→PR→AV", "ind_ANTH_PR_AV"), ("Total indirect", "total_indirect")]
fig, ax = plt.subplots(figsize=(6.4, 3.4))
for i, (lab, k) in enumerate(rows):
    e = med[k]["est"]; lo, hi = med[k]["ci"]
    ax.plot([lo, hi], [i, i], lw=1.6, color="#2c7fb8")
    ax.plot(e, i, "D", color="#d62728", ms=6)
    ax.text(hi + 0.008, i, f"{e:.3f} [{lo:.3f}, {hi:.3f}]", va="center", fontsize=7.5)
ax.axvline(0, color="grey", ls="--", lw=0.8)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=8)
ax.invert_yaxis(); ax.set_xlim(-0.05, 0.5); ax.set_xlabel("Standardized effect (5,000-resample bootstrap 95% CI)")
ax.set_title("Direct and indirect effects of anthropomorphism on avoidance", fontsize=9)
save(fig, "fig10_forest")

def z(v): return (v - v.mean()) / v.std(ddof=1)
Zc = comp.apply(z)
def betas(d):
    x = d["ANTH"].values; y = d["UV"].values
    a = np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)
    X = np.column_stack([d["UV"].values, d["ANTH"].values]); Y = d["PR"].values
    b1, b2 = np.linalg.lstsq(X, Y, rcond=None)[0]
    X = np.column_stack([d["PR"].values, d["UV"].values, d["ANTH"].values]); Y = d["AV"].values
    b3, _, _ = np.linalg.lstsq(X, Y, rcond=None)[0]
    return a * b1 * b3
rng = np.random.default_rng(11)
vals = [betas(Zc.iloc[rng.integers(0, N, N)].reset_index(drop=True)) for _ in range(2000)]
fig, ax = plt.subplots(figsize=(5.6, 3.2))
ax.hist(vals, bins=50, color="#2c7fb8", alpha=0.75)
ax.axvline(np.mean(vals), color="black", lw=1.5)
lo, hi = np.percentile(vals, [2.5, 97.5])
ax.axvline(lo, color="red", ls="--"); ax.axvline(hi, color="red", ls="--")
ax.axvline(0, color="grey", ls=":")
ax.set_xlabel("Serial indirect effect (ANTH→UV→PR→AV)")
ax.set_ylabel("Frequency")
ax.set_title(f"Bootstrap distribution (2,000 resamples): mean={np.mean(vals):.3f}, 95% CI [{lo:.3f}, {hi:.3f}]", fontsize=8.5)
save(fig, "fig11_boot")

fig, axes = plt.subplots(1, 3, figsize=(8.5, 3.0))
c4 = R["CFA"]["CFI"]; c1 = R["OneFactor"]["CFI"]
axes[0].bar([0, 1], [c4, c1], color=["#2c7fb8", "#d6604d"])
axes[0].axhline(0.95, ls="--", color="grey", lw=0.8)
axes[0].set_xticks([0, 1]); axes[0].set_xticklabels([f"4-factor\n(CFI={c4:.3f})", f"1-factor\n(CFI={c1:.3f})"], fontsize=8)
axes[0].set_ylim(0, 1.05); axes[0].set_ylabel("CFI")
axes[0].set_title(f"(a) CMB: Harman {R['Harman']['first_factor_pct']:.1f}% < 50%;\n1-factor model rejected", fontsize=8)
sg = R["subgroups"]
gk = [k for k in sg if k.startswith("gender")]
vals = [sg[k]["est"] for k in gk]
los = [sg[k]["est"] - sg[k]["ci"][0] for k in gk]
his = [sg[k]["ci"][1] - sg[k]["est"] for k in gk]
axes[1].errorbar(range(len(gk)), vals, yerr=[los, his], fmt="o", capsize=4, color="#2c7fb8")
axes[1].set_xticks(range(len(gk))); axes[1].set_xticklabels(["Male", "Female"], fontsize=8)
axes[1].set_title("(b) By gender", fontsize=8.5)
ak = [k for k in sg if k.startswith("aware")]
vals = [sg[k]["est"] for k in ak]
los = [sg[k]["est"] - sg[k]["ci"][0] for k in ak]
his = [sg[k]["ci"][1] - sg[k]["est"] for k in ak]
axes[2].errorbar(range(len(ak)), vals, yerr=[los, his], fmt="s", capsize=4, color="#d94801")
axes[2].set_xticks(range(len(ak))); axes[2].set_xticklabels(["very", "some", "not very", "not at all"], fontsize=8)
axes[2].set_title("(c) By prior UV awareness", fontsize=8.5)
for ax in axes:
    ax.axhline(0, color="grey", lw=0.8)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
fig.suptitle("Robustness of the serial indirect effect (95% bootstrap CI)", fontsize=9)
fig.tight_layout(rect=[0, 0, 1, 0.93])
save(fig, "fig12_robust")
print("ALL FIGURES DONE")
