# -*- coding: utf-8 -*-
"""Combine figures into multi-panel composites (no content removed).
New set: fig1, fig2, fig3, fig4, fig5(a=old5 b=old6), fig6(a=old7 b=old8),
fig7(old9), fig8(a=old10 b=old11), fig9(old12)."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FIG = Path(r"C:\Users\admin\.zcode\workspace\draft-e1afe658-697c-443e-a08a-4b5f7ebc1a44\revision\figures")

def combine(hname, panels, out, gap=24, label_size=30):
    imgs = [Image.open(FIG / f"{p}.png").convert("RGB") for p in panels]
    H = max(i.height for i in imgs)
    imgs = [i.resize((int(i.width * H / i.height), H)) if i.height != H else i for i in imgs]
    W = sum(i.width for i in imgs) + gap * (len(imgs) - 1) + 20
    canvas = Image.new("RGB", (W, H + 50), "white")
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", label_size)
    except Exception:
        font = ImageFont.load_default()
    x = 10
    for k, i in enumerate(imgs):
        canvas.paste(i, (x, 50))
        d.text((x + 6, 8), "(" + "abcdefgh"[k] + ")", fill="black", font=font)
        x += i.width + gap
    canvas.save(FIG / out)
    print("combined ->", out, canvas.size)

# keep originals as *_src backup then write final numbered files
import shutil
for f in list(FIG.glob("*.png")):
    (FIG / "_backup").mkdir(exist_ok=True)
    shutil.copy(f, FIG / "_backup" / f.name)

combine(None, ["fig5_corr", "fig6_fl"], "fig5_panels.png")
combine(None, ["fig7_dist", "fig8_pairs"], "fig6_panels.png")
shutil.copy(FIG / "fig9_sem.png", FIG / "fig7_sem.png")
combine(None, ["fig10_forest", "fig11_boot"], "fig8_panels.png")
shutil.copy(FIG / "fig12_robust.png", FIG / "fig9_robust.png")
print("done")
