"""Punto 2.4.b: mapa de calor del tiempo medio t90 (o t100) en el plano (x0, N).

Combina corridas de varias carpetas (cada una con <root>/*/seed_*/ : contacts.txt, metadata.txt, summary.txt):
  - 2.2  (N = 100 y N = 20, 12 valores de x0)           -> output/sys2_exp2, output/sys2_exp2_N20
  - 2.4  (x0 = r, N = 25..600)                           -> output/sys2_exp4
  - 2.4.b (N = 50..500 x 9 valores de x0)                -> output/sys2_exp4b
Las celdas (N, x0) se arman con las corridas de todas las carpetas que las contengan; cada corrida trae su t_max.
Definiciones (iguales a las de 2.2 y 2.4): t90 = instante del ceil(0.9 N)-esimo primer contacto con un obstaculo;
t100 = instante del N-esimo. Media sobre las corridas que alcanzan el umbral antes de su t_max; las celdas donde
no todas lo alcanzan se rayan, y donde ninguna lo alcanza quedan en gris.

Uso: python3 viz/system2/plot_heatmap_t90.py output/sys2_exp2 output/sys2_exp2_N20 output/sys2_exp4 output/sys2_exp4b
        --out-dir output/figures/sys2_exp4b [--metric t90|t100] [--n-values 20 50 100 200 300 400 500] [--annotate]
"""
import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from matplotlib.colors import LogNorm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.billiard_io import read_contacts, read_meta  # noqa: E402
from common.style import apply_style, plt  # noqa: E402


def load(roots):
    cells = defaultdict(list)
    for root in roots:
        for contacts in sorted(Path(root).glob("*/seed_*/contacts.txt")):
            d = contacts.parent
            if not (d / "summary.txt").exists():
                continue
            meta = read_meta(d)
            if not meta["obstacles"]:
                continue
            _, times = read_contacts(d)
            times = np.sort(times)
            n = meta["n"]
            k = {"t90": math.ceil(0.9 * n - 1e-9), "t100": n}
            cells[(n, round(meta["x0"], 10))].append({
                "t90": times[k["t90"] - 1] if len(times) >= k["t90"] else np.nan,
                "t100": times[n - 1] if len(times) >= n else np.nan,
                "tf": meta["tf"], "root": str(root),
            })
    if not cells:
        sys.exit("No se encontraron corridas con obstaculos")
    return cells


def main():
    p = argparse.ArgumentParser()
    p.add_argument("roots", nargs="+")
    p.add_argument("--out-dir", default="output/figures/sys2_exp4b")
    p.add_argument("--metric", choices=["t90", "t100"], default="t90")
    p.add_argument("--n-values", type=int, nargs="*")
    p.add_argument("--x0-values", type=float, nargs="*", help="x0 (m) a incluir; por defecto todos")
    p.add_argument("--annotate", action="store_true", help="escribir el valor medio en cada celda")
    args = p.parse_args()

    apply_style()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cells = load(args.roots)
    ns = sorted({n for n, _ in cells})
    if args.n_values:
        ns = [n for n in ns if n in args.n_values]
    x0s = sorted({x for n, x in cells if n in ns})
    if args.x0_values:
        x0s = [x for x in x0s if any(abs(x - v) < 1e-9 for v in args.x0_values)]

    mean = np.full((len(ns), len(x0s)), np.nan)
    reached = np.zeros((len(ns), len(x0s)), int)
    total = np.zeros((len(ns), len(x0s)), int)
    for i, n in enumerate(ns):
        for j, x in enumerate(x0s):
            runs = cells.get((n, x), [])
            vals = np.array([r[args.metric] for r in runs], float)
            ok = np.isfinite(vals)
            total[i, j], reached[i, j] = len(runs), int(ok.sum())
            if ok.any():
                mean[i, j] = vals[ok].mean()

    print(f"\nMetrica: <{args.metric}> (s). Celda = media sobre corridas que alcanzan el umbral; 'k/n' = alcanzan/total\n")
    header = "N \\ x0"
    print(f"{header:>8} " + " ".join(f"{x:>11.4f}" for x in x0s))
    for i, n in enumerate(ns):
        cellstr = []
        for j in range(len(x0s)):
            if total[i, j] == 0:
                cellstr.append(f"{'--':>11}")
            else:
                cellstr.append(f"{mean[i, j]:6.1f} {reached[i, j]:>2d}/{total[i, j]:<2d}".rjust(11) if reached[i, j] else f"{'nan':>6} {0:>2d}/{total[i, j]:<2d}".rjust(11))
        print(f"{n:8d} " + " ".join(cellstr))
    missing = [(n, x) for i, n in enumerate(ns) for j, x in enumerate(x0s) if total[i, j] == 0]
    if missing:
        print(f"\nCeldas sin corridas (en blanco): {len(missing)}")

    fig, ax = plt.subplots(figsize=(13, 8))
    masked = np.ma.masked_invalid(mean)
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad("#d0d0d0")
    vmin, vmax = np.nanmin(mean), np.nanmax(mean)
    im = ax.pcolormesh(np.arange(len(x0s) + 1), np.arange(len(ns) + 1), masked, cmap=cmap,
                       norm=LogNorm(vmin=vmin, vmax=vmax), edgecolors="white", linewidth=1)
    for i in range(len(ns)):
        for j in range(len(x0s)):
            if total[i, j] == 0:
                ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor="white", edgecolor="white"))
            elif 0 < reached[i, j] < total[i, j] or reached[i, j] == 0:
                ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False, hatch="//", edgecolor="white", linewidth=0))
            if args.annotate and reached[i, j]:
                ax.text(j + 0.5, i + 0.5, f"{mean[i, j]:.0f}", ha="center", va="center", fontsize=14, color="white")
    ax.set_xticks(np.arange(len(x0s)) + 0.5)
    ax.set_xticklabels([f"{x:.4g}" for x in x0s], rotation=45)
    ax.set_yticks(np.arange(len(ns)) + 0.5)
    ax.set_yticklabels([str(n) for n in ns])
    ax.set_xlabel("$x_0$ (m)")
    ax.set_ylabel("Cantidad de partículas")
    cb = fig.colorbar(im, ax=ax)
    ticks = [t for t in (10, 20, 50, 100, 200, 500, 1000) if vmin <= t <= vmax]
    if ticks:
        cb.set_ticks(ticks)
        cb.set_ticklabels([str(t) for t in ticks])
        cb.ax.minorticks_off()
    cb.set_label(f"Tiempo ${args.metric[0]}_{{{args.metric[1:]}}}$ medio (s)")
    fig.savefig(out / f"heatmap_{args.metric}.png")
    plt.close(fig)
    print(f"\nFigura en {out}/heatmap_{args.metric}.png  (rayado: no todas las corridas alcanzan el umbral; gris: ninguna)")


if __name__ == "__main__":
    main()
