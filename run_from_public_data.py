# -*- coding: utf-8 -*-
"""Self-contained reproduction from the deposited public_data.csv.
Run:  python -I run_from_public_data.py
Writes results_republished.json and prints a consistency check against results.json.
Requires: Python 3.12, pandas, numpy, scipy, semopy==2.3.11."""
import json, warnings
import numpy as np, pandas as pd
import semopy
from semopy.stats import calc_stats
from scipy import stats

warnings.filterwarnings("ignore")
MAP = {"非常不同意": 1, "有点不同意": 2, "不同意": 3, "一般": 4, "有点同意": 5, "同意": 6, "非常同意": 7}
df = pd.read_csv("public_data.csv")
N = len(df)  # 397 analyzed records
cols = list(df.columns)
def qcol(n):
    for c in cols:
        if c.startswith(f"{n}、"):
            return c
    raise KeyError(n)
items = pd.DataFrame({
    **{f"A{i}": df[qcol(i)].map(MAP) for i in range(1, 7)},
    **{f"U{i}" : df[qcol(i + 6)].map(MAP) for i in range(1, 7)},
    **{f"P{i}": df[qcol(i + 12)].map(MAP) for i in range(1, 7)},
    **{f"V{i}": df[qcol(i + 18)].map(MAP) for i in range(1, 7)},
})
grp = {"ANTH": [f"A{i}" for i in range(1, 7)], "UV": [f"U{i}" for i in range(1, 7)],
       "PR": [f"P{i}" for i in range(1, 7)], "AV": [f"V{i}" for i in range(1, 7)]}
comp = pd.DataFrame({g: items[c].mean(axis=1) for g, c in grp.items()})
R = {"N": N}
def cronbach(m):
    k = m.shape[1]
    return k / (k - 1) * (1 - m.var(axis=0, ddof=1).sum() / m.sum(axis=1).var(ddof=1))
R["reliability"] = {g: round(float(cronbach(items[c])), 3) for g, c in grp.items()}
R["descriptives"] = {g: {"M": round(float(comp[g].mean()), 2), "SD": round(float(comp[g].std(ddof=1)), 2),
                         "skew": round(float(stats.skew(comp[g])), 2), "kurt": round(float(stats.kurtosis(comp[g])), 2)}
                    for g in grp}
R["corr_composite"] = {}
for i, a in enumerate(grp):
    for b in list(grp)[i + 1:]:
        R["corr_composite"][f"{a}-{b}"] = round(float(np.corrcoef(comp[a], comp[b])[0, 1]), 3)
MEAS = """ANTH =~ A1+A2+A3+A4+A5+A6
UV =~ U1+U2+U3+U4+U5+U6
PR =~ P1+P2+P3+P4+P5+P6
AV =~ V1+V2+V3+V4+V5+V6"""
def srmr(model):
    S = np.cov(items.values, rowvar=False, ddof=1)
    sig = model.calc_sigma()[0]
    D = np.diag(1 / np.sqrt(np.diag(S)))
    iu = np.triu_indices(24, 1)
    return float(np.sqrt((((D @ S @ D) - (D @ sig @ D))[iu] ** 2).sum() / (24 * 25 / 2)))
m = semopy.Model(MEAS); m.fit(items)
s = calc_stats(m).iloc[0]
R["CFA"] = {"chi2": round(float(s["chi2"]), 2), "df": int(s["DoF"]), "p": round(float(s["chi2 p-value"]), 4),
            "CFI": round(float(s["CFI"]), 3), "TLI": round(float(s["TLI"]), 3),
            "RMSEA": round(float(s["RMSEA"]), 3), "SRMR": round(srmr(m), 3)}
sp = m.inspect(std_est=True)
R["loadings"] = {g: [round(float(x), 2) for x in sp[(sp["op"] == "~") & (sp["rval"] == g) & (~sp["lval"].isin(grp))]["Est. Std"]] for g in grp}
R["AVE_CR"] = {}
for g in grp:
    v = np.array(R["loadings"][g])
    R["AVE_CR"][g] = {"AVE": round(float(np.mean(v ** 2)), 3),
                     "CR": round(float(v.sum() ** 2 / (v.sum() ** 2 + np.sum(1 - v ** 2))), 3)}
latc = sp[(sp["op"] == "~~") & (sp["lval"].isin(grp)) & (sp["rval"].isin(grp)) & (sp["lval"] != sp["rval"])]
R["latent_corr"] = {f"{r['lval']}-{r['rval']}": round(float(r["Est. Std"]), 3) for _, r in latc.iterrows()}
m2 = semopy.Model(MEAS + "\nUV ~ ANTH\nPR ~ UV + ANTH\nAV ~ PR + UV + ANTH"); m2.fit(items)
s2 = calc_stats(m2).iloc[0]
R["SEM"] = {"chi2": round(float(s2["chi2"]), 2), "df": int(s2["DoF"]), "p": round(float(s2["chi2 p-value"]), 4),
            "CFI": round(float(s2["CFI"]), 3), "TLI": round(float(s2["TLI"]), 3),
            "RMSEA": round(float(s2["RMSEA"]), 3), "SRMR": round(srmr(m2), 3)}
sp2 = m2.inspect(std_est=True)
R["paths_latent"] = {f"{r['rval']}->{r['lval']}": {"std": round(float(r["Est. Std"]), 3), "SE": round(float(r["Std. Err"]), 3),
                        "z": round(float(r["z-value"]), 2), "p": round(float(r["p-value"]), 4)}
                     for _, r in sp2[(sp2["op"] == "~") & (sp2["lval"].isin(grp)) & (sp2["rval"].isin(grp))].iterrows()}
def z(v): return (v - v.mean()) / v.std(ddof=1)
Zc = comp.apply(z)
def betas(d):
    x = d["ANTH"].values; y = d["UV"].values
    a = np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)
    X = np.column_stack([d["UV"].values, d["ANTH"].values]); b = np.linalg.lstsq(X, d["PR"].values, rcond=None)[0]
    X = np.column_stack([d["PR"].values, d["UV"].values, d["ANTH"].values]); e = np.linalg.lstsq(X, d["AV"].values, rcond=None)[0]
    return [a, b[0], e[0], b[1], e[1], e[2], a * b[0] * e[0], a * e[1], b[1] * e[0], a * b[0] * e[0] + a * e[1] + b[1] * e[0],
            np.cov(x, d["AV"].values, ddof=1)[0, 1] / np.var(x, ddof=1)]
rng = np.random.default_rng(2026)
boot = np.array([betas(Zc.iloc[rng.integers(0, N, N)].reset_index(drop=True)) for _ in range(5000)])
obs = betas(Zc)
lab = ["a_ANTH_UV", "d21_UV_PR", "b2_PR_AV", "parallel_ANTH_PR", "UV_AV", "direct", "serial_indirect",
       "ind_ANTH_UV_AV", "ind_ANTH_PR_AV", "total_indirect", "total"]
R["mediation_composite"] = {l: {"est": round(float(obs[j]), 3),
                                "ci": [round(float(np.percentile(boot[:, j], 2.5)), 3),
                                       round(float(np.percentile(boot[:, j], 97.5)), 3)]}
                            for j, l in enumerate(lab)}
Xi = ((items - items.mean()) / items.std(ddof=1)).values
ev = np.linalg.eigvalsh(np.cov(Xi, rowvar=False, ddof=1))[::-1]
R["Harman_first_factor_pct"] = round(float(ev[0] / ev.sum() * 100), 1)
m4 = semopy.Model("F =~ " + "+".join(items.columns)); m4.fit(items)
s4 = calc_stats(m4).iloc[0]
R["OneFactor"] = {"chi2": round(float(s4["chi2"]), 2), "df": int(s4["DoF"]), "CFI": round(float(s4["CFI"]), 3),
                  "RMSEA": round(float(s4["RMSEA"]), 3)}
for it, nm in [(27, "stimulus_human_like"), (28, "stimulus_distinct")]:
    v = df[qcol(it)].map(MAP).dropna().values
    t, p = stats.ttest_1samp(v, 4)
    R.setdefault("stimulus", {})[nm] = {"M": round(float(v.mean()), 2), "SD": round(float(v.std(ddof=1)), 2),
                                        "t": round(float(t), 2), "p": float(p)}
json.dump(R, open("results_republished.json", "w"), indent=1, ensure_ascii=False)
print("N =", N)
print("=== consistency vs results.json (manuscript) ===")
ref = json.load(open("results.json", encoding="utf-8"))
def g(d, *ks):
    for k in ks:
        d = d[k]
    return d
checks = [
    ("N", N, ref["final_n"]),
    ("CFA chi2", R["CFA"]["chi2"], ref["CFA"]["chi2"]),
    ("CFA CFI", R["CFA"]["CFI"], ref["CFA"]["CFI"]),
    ("SEM chi2", R["SEM"]["chi2"], ref["SEM"]["chi2"]),
    ("path UV->PR", R["paths_latent"]["UV->PR"]["std"], ref["paths_latent"]["UV->PR"]["std"]),
    ("path PR->AV", R["paths_latent"]["PR->AV"]["std"], ref["paths_latent"]["PR->AV"]["std"]),
    ("serial indirect", R["mediation_composite"]["serial_indirect"]["est"], ref["mediation_composite"]["chain_ANTH_UV_PR_AV"]["est"]),
    ("serial CI", R["mediation_composite"]["serial_indirect"]["ci"], ref["mediation_composite"]["chain_ANTH_UV_PR_AV"]["ci"]),
    ("total indirect", R["mediation_composite"]["total_indirect"]["est"], ref["mediation_composite"]["total_indirect"]["est"]),
    ("Harman%", R["Harman_first_factor_pct"], ref["Harman"]["first_factor_pct"]),
    ("alpha ANTH", R["reliability"]["ANTH"], ref["desc"]["ANTH"]["alpha"]),
    ("alpha AV", R["reliability"]["AV"], ref["desc"]["AV"]["alpha"]),
]
allok = True
for nm, a, b in checks:
    ok = a == b
    allok &= ok
    print(f"  {'OK ' if ok else 'DIFF'} {nm}: deposit={a} manuscript={b}")
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print("ALL CONSISTENT" if allok else "some diffs - check bootstrap seed order")
