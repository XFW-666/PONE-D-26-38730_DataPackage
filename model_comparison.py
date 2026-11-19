import sys, io, json, warnings, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, openpyxl, semopy
from semopy.stats import calc_stats

BASE = r"C:\Users\admin\.zcode\workspace\draft-e1afe658-697c-443e-a08a-4b5f7ebc1a44\revision"
df = pd.read_csv(f"{BASE}/cleaned_full.csv")
items = df[[f"x{i}" for i in range(1, 25)]].copy()
ren = {}
for it in range(1, 7): ren[f"x{it}"] = f"A{it}"
for it in range(7, 13): ren[f"x{it}"] = f"U{it-6}"
for it in range(13, 19): ren[f"x{it}"] = f"P{it-12}"
for it in range(19, 25): ren[f"x{it}"] = f"V{it-18}"
items = items.rename(columns=ren)
MEAS = """ANTH =~ A1+A2+A3+A4+A5+A6
UV =~ U1+U2+U3+U4+U5+U6
PR =~ P1+P2+P3+P4+P5+P6
AV =~ V1+V2+V3+V4+V5+V6"""

def srmr(model, data):
    S = np.cov(data.values, rowvar=False, ddof=1)
    sig = model.calc_sigma()[0]
    D = np.diag(1 / np.sqrt(np.diag(S)))
    p = S.shape[0]
    iu = np.triu_indices(p, 1)
    return float(np.sqrt(((D @ S @ D - D @ sig @ D)[iu] ** 2).sum() / (p * (p + 1) / 2)))

def rep(tag, spec):
    m = semopy.Model(spec)
    m.fit(items)
    s = calc_stats(m).iloc[0]
    r = {"chi2": round(float(s["chi2"]), 2), "df": int(s["DoF"]), "CFI": round(float(s["CFI"]), 3),
         "TLI": round(float(s["TLI"]), 3), "RMSEA": round(float(s["RMSEA"]), 3), "SRMR": round(srmr(m, items), 3),
         "AIC": round(float(s["AIC"]), 1), "BIC": round(float(s["BIC"]), 1)}
    sp = m.inspect(std_est=True)
    r["paths"] = {f"{q['rval']}->{q['lval']}": round(float(q["Est. Std"]), 3)
                  for _, q in sp[(sp["op"] == "~") & (sp["lval"].isin(["UV", "PR", "AV"])) & (sp["rval"].isin(["ANTH", "UV", "PR"]))].iterrows()}
    print(tag, json.dumps(r, ensure_ascii=False))
    return r

serial = rep("SERIAL(saturated):", MEAS + "\nUV ~ ANTH\nPR ~ UV + ANTH\nAV ~ PR + UV + ANTH")
serial_r = rep("SERIAL(restricted, no UV->AV):", MEAS + "\nUV ~ ANTH\nPR ~ UV + ANTH\nAV ~ PR + ANTH")
parallel = rep("PARALLEL(UV,PR independent):", MEAS + "\nUV ~ ANTH\nPR ~ ANTH\nAV ~ PR + UV + ANTH")
# serial without UV->PR (pure parallel) equals parallel; also fit model where PR ~ UV only (no parallel ANTH->PR)
serial2 = rep("SERIAL(no ANTH->PR, keep UV->AV):", MEAS + "\nUV ~ ANTH\nPR ~ UV\nAV ~ PR + UV + ANTH")
json.dump({"serial_saturated": serial, "serial_restricted": serial_r, "parallel": parallel, "serial2": serial2},
          open(f"{BASE}/model_comparison.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- verify suggested PLOS ONE papers ----
for q in ["anthropomorphic AI customer service social presence PLOS ONE Huang Ahmad",
          "chatbot anthropomorphism consumer PLOS ONE Tian 2025",
          "AI acceptance consumer PLOS ONE Li 2025"]:
    try:
        url = "https://api.crossref.org/works?rows=4&query.bibliographic=" + urllib.parse.quote(q)
        j = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ref-check/1.0"}), timeout=25))
        print("\nQUERY:", q)
        for it in j["message"]["items"]:
            cont = (it.get("container-title") or ["?"])
            print("  -", (it.get("title") or ["?"])[0][:90], "|", cont[0] if cont else "?", "|",
                  it.get("issued", {}).get("date-parts", [[None]])[0][0], "|",
                  ",".join(a.get("family", "") for a in it.get("author", [])[:3]))
    except Exception as e:
        print("ERR", repr(e)[:120])
