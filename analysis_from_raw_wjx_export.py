"""
Full re-analysis for PLOS ONE revision PONE-D-26-38730.
Input : raw Wenjuanxing export (407 rows)
Cleaning: exclude 9 self-reported under-18 respondents -> N=398
Outputs: results.json + cleaned_data.csv + public_data.csv
"""
import sys, io, json, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, openpyxl
import semopy
from semopy.stats import calc_stats
from scipy import stats

RAW = r"C:\Users\admin\Downloads\365578249_按文本_AI客服拟人化与消费者行为研究调查问卷_407_407.xlsx"
OUT = r"C:\Users\admin\.zcode\workspace\draft-e1afe658-697c-443e-a08a-4b5f7ebc1a44\revision"

MAP = {"非常不同意": 1, "有点不同意": 2, "不同意": 3, "一般": 4, "有点同意": 5, "同意": 6, "非常同意": 7}

wb = openpyxl.load_workbook(RAW, read_only=True)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))
hdr, data = [str(h) if h is not None else "" for h in rows[0]], rows[1:]
idx = {}
for i, h in enumerate(hdr):
    q = h.split("、")[0]
    if q.isdigit():
        idx[int(q)] = i
    elif "性别" in h: idx[29] = i
    elif "年龄" in h: idx[30] = i
    elif "最高学历" in h: idx[31] = i
    elif "支配收入" in h: idx[32] = i
    elif "在线客服的频率" in h: idx[33] = i
    elif "AI客服打交道的经历" in h: idx[34] = i
    elif "恐怖谷效应" in h and "了解" in h: idx[35] = i
    elif "最常使用在线客服" in h: idx[36] = i
    elif "提交答卷时间" in h: tcol = i
    elif "所用时间" in h: dcol = i
    elif "来自IP" in h: ipcol = i
    elif h.strip() == "序号": idcol = i

def itemcol(n):
    return idx[n]

recs = []
for r in data:
    rec = {"_ip": str(r[ipcol]), "_t": str(r[tcol]), "_dur": str(r[dcol]), "case": int(str(r[idcol]))}
    for it in range(1, 29):
        rec[f"x{it}"] = MAP.get(str(r[itemcol(it)]).strip(), np.nan)
    rec["gender"] = str(r[itemcol(29)])
    rec["age"] = str(r[itemcol(30)])
    rec["edu"] = str(r[itemcol(31)])
    rec["income"] = str(r[itemcol(32)])
    rec["freq"] = str(r[itemcol(33)])
    rec["exp"] = str(r[itemcol(34)])
    rec["aware"] = str(r[itemcol(35)])
    recs.append(rec)
df = pd.DataFrame(recs)
df = df.astype({f"x{i}": float for i in range(1, 29)})

R = {"raw_n": int(len(df))}
# attention checks
R["att25_pass"] = int((df["x25"] == 7).sum())
# recompute item26 from raw
i26 = [str(r[itemcol(26)]) for r in data]
R["att26_pass"] = int(sum(1 for x in i26 if "商品质量问题" in x and "价格争议" in x))
R["minors"] = int((df["age"].str.startswith("A")).sum())

# duplicate detection: identical responses across all 37 items -> drop later submission
import hashlib
qcols = [f"x{i}" for i in range(1, 29)] + ["gender", "age", "edu", "income", "freq", "exp", "aware"]
sig = df[qcols].astype(str).agg("|".join, axis=1).map(lambda s: hashlib.md5(s.encode()).hexdigest())
dup_mask = sig.duplicated(keep="first")
R["duplicate_removed"] = int(dup_mask.sum())
R["duplicate_cases"] = sorted(int(c) for c in df.loc[dup_mask, "case"])

# CLEAN: exclude under-18 records and duplicate double-submissions
df = df[~df["age"].str.startswith("A") & ~dup_mask].reset_index(drop=True)
df = df.dropna(subset=[f"x{i}" for i in range(1, 25)]).reset_index(drop=True)
N = len(df)
R["final_n"] = N

names = {}
for it in range(1, 7): names[f"x{it}"] = f"A{it}"
for it in range(7, 13): names[f"x{it}"] = f"U{it-6}"
for it in range(13, 19): names[f"x{it}"] = f"P{it-12}"
for it in range(19, 25): names[f"x{it}"] = f"V{it-18}"
items = df[[f"x{i}" for i in range(1, 25)]].rename(columns=names)
LAT = ["ANTH", "UV", "PR", "AV"]
comp = pd.DataFrame({
    "ANTH": items[[f"A{i}" for i in range(1, 7)]].mean(axis=1),
    "UV": items[[f"U{i}" for i in range(1, 7)]].mean(axis=1),
    "PR": items[[f"P{i}" for i in range(1, 7)]].mean(axis=1),
    "AV": items[[f"V{i}" for i in range(1, 7)]].mean(axis=1),
})

def pvar(v): return float(np.var(v, ddof=1))
def cronbach(mat):
    k = mat.shape[1]
    vi = mat.var(axis=0, ddof=1).sum()
    vt = mat.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - vi / vt)
def pearson(a, b):
    return float(np.corrcoef(a, b)[0, 1])

# ---- Table 1 demographics ----
def dist(col):
    vc = df[col].value_counts()
    return {k: [int(v), round(v / N * 100, 1)] for k, v in sorted(vc.items())}
R["demo"] = {k: dist(k) for k in ["gender", "age", "edu", "income", "freq", "exp", "aware"]}

# ---- descriptives + reliability ----
desc = {}
for c, its in [("ANTH", [f"A{i}" for i in range(1, 7)]), ("UV", [f"U{i}" for i in range(1, 7)]),
               ("PR", [f"P{i}" for i in range(1, 7)]), ("AV", [f"V{i}" for i in range(1, 7)])]:
    m = items[its]
    tot = m.mean(axis=1)
    a = cronbach(m)
    msum = m.sum(axis=1)
    desc[c] = {"M": round(float(tot.mean()), 2), "SD": round(float(tot.std(ddof=1)), 2),
               "skew": round(float(stats.skew(tot)), 2), "kurt": round(float(stats.kurtosis(tot)), 2),
               "alpha": round(a, 3),
               "itc": [round(float(pearson(m[c_], msum - m[c_])), 3) for c_ in its]}
# item-level descriptives
desc["items"] = {c_: [round(float(items[c_].mean()), 2), round(float(items[c_].std(ddof=1)), 2)] for c_ in items.columns}
R["desc"] = desc

# ---- correlations ----
corr = {}
for i, a in enumerate(LAT):
    for b in LAT[i + 1:]:
        corr[f"{a}-{b}"] = round(pearson(comp[a], comp[b]), 3)
R["corr_composite"] = corr

# ---- KMO & Bartlett (on 24 items) ----
Xc = items.values
C = np.corrcoef(Xc, rowvar=False)
Rinv = np.linalg.inv(C)
p = Xc.shape[1]
num = sum(C[i, j] ** 2 for i in range(p) for j in range(p) if i != j)
den = sum(Rinv[i, j] ** 2 for i in range(p) for j in range(p) if i != j)
R["KMO"] = round(num / (num + den), 3)
bart = -(N - 1 - (2 * p + 5) / 6) * np.log(np.linalg.det(C))
R["Bartlett"] = {"chi2": round(float(bart), 1), "df": p * (p - 1) // 2, "p": float(stats.chi2.sf(bart, p * (p - 1) // 2))}

# ---- CFA ----
def srmr(model, data):
    S = np.cov(data.values, rowvar=False, ddof=1)
    sig = model.calc_sigma()[0]
    D = np.diag(1 / np.sqrt(np.diag(S)))
    Rs = D @ S @ D
    Rm = D @ sig @ D
    p = S.shape[0]
    iu = np.triu_indices(p, 1)
    return float(np.sqrt(((Rs[iu] - Rm[iu]) ** 2).sum() / (p * (p + 1) / 2)))

MEAS = """
ANTH =~ A1+A2+A3+A4+A5+A6
UV =~ U1+U2+U3+U4+U5+U6
PR =~ P1+P2+P3+P4+P5+P6
AV =~ V1+V2+V3+V4+V5+V6
"""
m = semopy.Model(MEAS)
m.fit(items)
s = calc_stats(m).iloc[0]
sp = m.inspect(std_est=True)
lds = {}
for g in LAT:
    v = sp[(sp["op"] == "~") & (sp["rval"] == g) & (~sp["lval"].isin(LAT))]["Est. Std"].values
    lds[g] = [round(float(x), 2) for x in v]
    ave = float(np.mean(v ** 2))
    cr = float(v.sum() ** 2 / (v.sum() ** 2 + np.sum(1 - v ** 2)))
    desc[g]["AVE"] = round(ave, 3)
    desc[g]["CR"] = round(cr, 3)
R["CFA"] = {"chi2": round(float(s["chi2"]), 2), "df": int(s["DoF"]), "p": round(float(s["chi2 p-value"]), 4),
            "CFI": round(float(s["CFI"]), 3), "TLI": round(float(s["TLI"]), 3),
            "RMSEA": round(float(s["RMSEA"]), 3), "SRMR": round(srmr(m, items), 3)}
R["loadings"] = lds
latcfa = sp[(sp["op"] == "~~") & (sp["lval"].isin(LAT)) & (sp["rval"].isin(LAT)) & (sp["lval"] != sp["rval"])]
R["latent_corr_CFA"] = {f"{r['lval']}-{r['rval']}": round(float(r["Est. Std"]), 3) for _, r in latcfa.iterrows()}

# ---- Structural model (saturated, latent) ----
SPEC = MEAS + """
UV ~ ANTH
PR ~ UV + ANTH
AV ~ PR + UV + ANTH
"""
m2 = semopy.Model(SPEC)
m2.fit(items)
s2 = calc_stats(m2).iloc[0]
sp2 = m2.inspect(std_est=True)
paths = {}
for _, r in sp2[(sp2["op"] == "~") & (sp2["lval"].isin(LAT)) & (sp2["rval"].isin(LAT))].iterrows():
    paths[f"{r['rval']}->{r['lval']}"] = {"std": round(float(r["Est. Std"]), 3), "unstd": round(float(r["Estimate"]), 3),
                                          "SE": round(float(r["Std. Err"]), 3), "z": round(float(r["z-value"]), 2),
                                          "p": round(float(r["p-value"]), 4)}
R["SEM"] = {"chi2": round(float(s2["chi2"]), 2), "df": int(s2["DoF"]), "p": round(float(s2["chi2 p-value"]), 4),
            "CFI": round(float(s2["CFI"]), 3), "TLI": round(float(s2["TLI"]), 3),
            "RMSEA": round(float(s2["RMSEA"]), 3), "SRMR": round(srmr(m2, items), 3)}
R["paths_latent"] = paths

# ---- composite-score serial mediation, 5000 bootstrap ----
def z(v): return (v - v.mean()) / v.std(ddof=1)
Zc = comp.apply(z)
def betas(d):
    x = d["ANTH"].values; y = d["UV"].values
    a = np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)
    X = np.column_stack([d["UV"].values, d["ANTH"].values]); Y = d["PR"].values
    b_uv_pr, b_ant_pr = np.linalg.lstsq(X, Y, rcond=None)[0]
    X = np.column_stack([d["PR"].values, d["UV"].values, d["ANTH"].values]); Y = d["AV"].values
    b_pr_av, b_uv_av, b_ant_av = np.linalg.lstsq(X, Y, rcond=None)[0]
    chain = a * b_uv_pr * b_pr_av
    ind1 = a * b_uv_av
    ind2 = a * b_ant_pr * b_pr_av
    ind3 = b_ant_pr * b_pr_av
    ind4 = b_uv_av
    total = np.cov(x, d["AV"].values, ddof=1)[0, 1] / np.var(x, ddof=1)
    return [a, b_uv_pr, b_pr_av, b_ant_pr, b_uv_av, b_ant_av, chain, ind1, ind3, chain + ind1 + ind3, total]
labels = ["a_ANTH_UV", "d21_UV_PR", "b2_PR_AV", "d21a_ANTH_PR", "b12_UV_AV", "cprime_ANTH_AV",
          "chain_ANTH_UV_PR_AV", "ind_ANTH_UV_AV", "ind_ANTH_PR_AV", "total_indirect", "total_effect"]
rng = np.random.default_rng(2026)
B = 5000
boot = np.array([betas(Zc.iloc[rng.integers(0, N, N)].reset_index(drop=True)) for _ in range(B)])
obs = betas(Zc)
med = {}
for j, l in enumerate(labels):
    lo, hi = np.percentile(boot[:, j], [2.5, 97.5])
    med[l] = {"est": round(float(obs[j]), 3), "ci": [round(float(lo), 3), round(float(hi), 3)]}
med["_shares"] = {"chain_pct_of_total": round(obs[6] / obs[10] * 100, 1),
                  "total_indirect_pct": round(obs[9] / obs[10] * 100, 1),
                  "direct_pct": round(obs[5] / obs[10] * 100, 1)}
R["mediation_composite"] = med

# ---- Harman single-factor ----
Xi = ((items - items.mean()) / items.std(ddof=1)).values
ev = np.linalg.eigvalsh(np.cov(Xi, rowvar=False, ddof=1))[::-1]
R["Harman"] = {"first_factor_pct": round(float(ev[0] / ev.sum() * 100), 1),
               "n_eigen_gt1": int((ev > 1).sum())}

# ---- single-factor CFA baseline (for CMB comparison) ----
ONE = "F =~ " + "+".join(items.columns)
try:
    m4 = semopy.Model(ONE)
    m4.fit(items)
    s4 = calc_stats(m4).iloc[0]
    R["OneFactor"] = {"chi2": round(float(s4["chi2"]), 2), "df": int(s4["DoF"]),
                      "CFI": round(float(s4["CFI"]), 3), "RMSEA": round(float(s4["RMSEA"]), 3),
                      "SRMR": round(srmr(m4, items), 3)}
except Exception as e:
    R["OneFactor"] = {"error": str(e)[:120]}

# ---- PC partialling sensitivity (as in original Fig 12a) ----
Xi2 = ((items - items.mean()) / items.std(ddof=1)).values
u, sv, vt = np.linalg.svd(Xi2, full_matrices=False)
pc1 = Xi2 @ vt[0]
resid = {}
for c in LAT:
    y = comp[c].values
    A = np.column_stack([np.ones(N), pc1])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    resid[c] = y - A @ coef
Zc2 = pd.DataFrame(resid).apply(z)
R["chain_after_PCpartial"] = round(float(betas(Zc2)[6]), 3)

# ---- subgroup chain effects ----
def chain_in(d):
    if d["gender"].nunique() < 2 or len(d) < 50:
        return None
    v = betas(d.apply(z) if False else d)
    return v[6]
sub = {}
def boot_chain(dd, Bn=2000):
    r2 = np.random.default_rng(7)
    Zn = dd.apply(z)
    vals = [betas(Zn.iloc[r2.integers(0, len(Zn), len(Zn))].reset_index(drop=True))[6] for _ in range(Bn)]
    o = betas(Zn)[6]
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return {"est": round(float(o), 3), "ci": [round(float(lo), 3), round(float(hi), 3)], "n": int(len(dd))}
for g in ["男", "女"]:
    dd = comp[df["gender"].str.contains(g)]
    sub[f"gender_{g}"] = boot_chain(dd)
for a, lab in [("A", "very_familiar"), ("B", "somewhat"), ("C", "not_very"), ("D", "not_at_all")]:
    dd = comp[df["aware"].str.startswith(a + ".")]
    if len(dd) >= 30:
        sub[f"aware_{lab}"] = boot_chain(dd)
R["subgroups"] = sub

# ---- manipulation checks + t-tests vs midpoint ----
mc = {}
for it, nm in [(27, "highly human-like"), (28, "clearly distinct from human")]:
    v = items_df = df[f"x{it}"].dropna().values
    t, p = stats.ttest_1samp(v, 4)
    mc[nm] = {"M": round(float(v.mean()), 2), "SD": round(float(v.std(ddof=1)), 2),
              "t": round(float(t), 2), "p": float(p)}
R["manipulation"] = mc

# ---- straight-lining ----
sl = int((items.nunique(axis=1) == 1).sum())
R["straightliners"] = sl
R["zero_var"] = int((items.std(axis=1) == 0).sum())

# ---- save outputs ----
df.to_csv(f"{OUT}/cleaned_full.csv", index=False, encoding="utf-8-sig")
# NOTE: the public deposit file data_package/public_data.csv is generated by qa_data.py
# (original response labels, all 407 rows, analysed flag = 0 for minors and duplicates).

with open(f"{OUT}/results.json", "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
