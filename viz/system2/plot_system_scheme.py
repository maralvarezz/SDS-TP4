import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

plt.rcParams.update({"font.size": 20})
R, r = 0.51, 0.0175

p = argparse.ArgumentParser()
p.add_argument("--x0", type=float, default=0.25)
p.add_argument("--out", default="output/figures/sys2_scheme/sistema.png")
a = p.parse_args()
x0 = a.x0

fig, ax = plt.subplots(figsize=(7.5, 7))
ax.add_patch(Circle((0, 0), R, fill=False, edgecolor="k", linewidth=2.5))
for sx in (-1, 1):
    ax.add_patch(Circle((sx * x0, 0), r, facecolor="k", edgecolor="k"))

arrow = dict(arrowstyle="<->", color="tab:blue", linewidth=2, shrinkA=0, shrinkB=0)
th = np.deg2rad(50)
ax.annotate("", xy=(R * np.cos(th), R * np.sin(th)), xytext=(0, 0), arrowprops=dict(arrow, color="tab:red"))
ax.text(0.5 * R * np.cos(th) - 0.035, 0.5 * R * np.sin(th) + 0.02, "$R$", color="tab:red", ha="center", va="bottom")
yo = -0.07
ax.annotate("", xy=(x0, yo), xytext=(0, yo), arrowprops=arrow)
ax.plot([x0, x0], [0, yo], color="tab:blue", linewidth=1, linestyle=":")
ax.plot([0, 0], [0, yo], color="tab:blue", linewidth=1, linestyle=":")
ax.text(x0 / 2, yo - 0.015, "$x_0$", color="tab:blue", ha="center", va="top")
ax.annotate("$r$", xy=(-x0 - r * np.cos(np.deg2rad(45)), r * np.sin(np.deg2rad(45))), xytext=(-x0 - 0.075, 0.095),
            ha="center", va="center", arrowprops=dict(arrowstyle="-", color="k", linewidth=1.5))

lim = R * 1.08
ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect("equal")
ax.axis("off")
fig.tight_layout()
out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.05)
print(out)
