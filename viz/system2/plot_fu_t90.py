"""Punto 2.2: fraccion de particulas usadas F_u(t) y tiempo de 90 % t90 vs x0.

Lee <root>/*/seed_*/ : contacts.txt (evento fresca->usada, "id t_s") y metadata.txt (N, x0, totalTime).
Definiciones (se calculan aca; el motor solo registra el evento):
  N_u(t)  = cantidad de particulas con primer contacto en un obstaculo en un tiempo <= t
  F_u(t)  = N_u(t) / N
  t90     = menor t con F_u(t) >= 0.9, es decir el instante del ceil(0.9 N)-esimo primer contacto.
            Si la corrida no llega a F_u = 0.9 antes de t_max, t90 no esta definido ("no alcanzado").
Para cada x0: media y desvio muestral (ddof = 1) de F_u(t) sobre todas las realizaciones, y de t90 sobre las
realizaciones que lo alcanzan; se informa cuantas lo alcanzan y F_u(t_max).

Uso: python3 viz/system2/plot_fu_t90.py output/sys2_exp2 --out-dir output/figures/sys2_exp2
        [--show-x0 0.0175 0.1 0.25 0.4925] [--compare-root output/sys2_exp2_N20 --label N=100 --compare-label N=20]
"""
import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.billiard_io import read_contacts, read_meta  # noqa: E402
from common.style import apply_style, plt  # noqa: E402

THRESHOLD = 0.9


def load(root):
    by_x0 = defaultdict(list)
    for contacts in sorted(Path(root).glob("*/seed_*/contacts.txt")):
        d = contacts.parent
        if not (d / "summary.txt").exists():
            continue
        meta = read_meta(d)
        _, times = read_contacts(d)
        by_x0[round(meta["x0"], 10)].append({"n": meta["n"], "tf": meta["tf"], "times": np.sort(times)})
    if not by_x0:
        sys.exit(f"No hay corridas completas en {root}")
    return by_x0


def t90_of(run):
    k = math.ceil(THRESHOLD * run["n"] - 1e-9)
    return run["times"][k - 1] if len(run["times"]) >= k else np.nan


def fu_curve(run, grid):
    return np.searchsorted(run["times"], grid, side="right") / run["n"]


def summarize(by_x0):
    rows = []
    for x0 in sorted(by_x0):
        runs = by_x0[x0]
        t90 = np.array([t90_of(r) for r in runs])
        ok = np.isfinite(t90)
        fu_end = np.array([len(r["times"]) / r["n"] for r in runs])
        rows.append({
            "x0": x0, "runs": len(runs), "reached": int(ok.sum()),
            "t90_mean": t90[ok].mean() if ok.any() else np.nan,
            "t90_std": t90[ok].std(ddof=1) if ok.sum() > 1 else (0.0 if ok.any() else np.nan),
            "fu_end_mean": fu_end.mean(), "fu_end_std": fu_end.std(ddof=1) if len(fu_end) > 1 else 0.0,
        })
    return rows


def print_table(name, rows, tf):
    print(f"\n{name}  (t_max = {tf:g} s)")
    print(f"{'x0 (m)':>9} {'alcanzan':>9} {'t90 media (s)':>14} {'sigma (s)':>10} {'Fu(tmax) media':>15} {'sigma':>7}")
    for r in rows:
        print(f"{r['x0']:9.4f} {r['reached']:4d}/{r['runs']:<4d} {r['t90_mean']:14.2f} {r['t90_std']:10.2f} "
              f"{r['fu_end_mean']:15.3f} {r['fu_end_std']:7.3f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("--out-dir", default="output/figures/sys2_exp2")
    p.add_argument("--show-x0", type=float, nargs="*", help="x0 cuyas curvas F_u(t) se grafican")
    p.add_argument("--label", default="N = 100")
    p.add_argument("--compare-root")
    p.add_argument("--compare-label", default="N = 20")
    p.add_argument("--dt-grid", type=float, default=0.1, help="paso de la grilla temporal de F_u(t) (s)")
    args = p.parse_args()

    apply_style()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    datasets = {args.label: load(args.root)}
    if args.compare_root:
        datasets[args.compare_label] = load(args.compare_root)

    summaries = {}
    for name, by_x0 in datasets.items():
        tf = next(iter(by_x0.values()))[0]["tf"]
        summaries[name] = summarize(by_x0)
        print_table(name, summaries[name], tf)

    # --- F_u(t) media +- sigma, un panel por dataset ---
    for k, (name, by_x0) in enumerate(datasets.items()):
        tf = next(iter(by_x0.values()))[0]["tf"]
        grid = np.arange(0.0, tf + 1e-9, args.dt_grid)
        show = sorted(args.show_x0) if args.show_x0 else sorted(by_x0)
        fig, ax = plt.subplots()
        for x0 in show:
            key = min(by_x0, key=lambda v: abs(v - x0))
            curves = np.array([fu_curve(r, grid) for r in by_x0[key]])
            mean = curves.mean(axis=0)
            std = curves.std(axis=0, ddof=1) if len(curves) > 1 else np.zeros_like(mean)
            line, = ax.plot(grid, mean, linewidth=2, label=f"$x_0$ = {key:.4g} m")
            ax.fill_between(grid, np.clip(mean - std, 0, 1), np.clip(mean + std, 0, 1), alpha=0.2, color=line.get_color())
        ax.axhline(THRESHOLD, color="k", linestyle="--", linewidth=1)
        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Fracción de partículas usadas")
        ax.set_ylim(0, 1.02)
        ax.legend(loc="lower right")
        fig.savefig(out / f"fu_vs_time_{k}.png")
        plt.close(fig)

    # --- t90 vs x0 ---
    fig, ax = plt.subplots()
    for (name, rows), mk in zip(summaries.items(), ["o", "s"]):
        full = [r for r in rows if r["reached"] == r["runs"]]
        part = [r for r in rows if 0 < r["reached"] < r["runs"]]
        line = ax.errorbar([r["x0"] for r in full], [r["t90_mean"] for r in full], yerr=[r["t90_std"] for r in full],
                           marker=mk, markersize=8, capsize=4, linestyle="-", linewidth=1, label=name)
        if part:
            ax.errorbar([r["x0"] for r in part], [r["t90_mean"] for r in part], yerr=[r["t90_std"] for r in part],
                        marker=mk, markersize=8, capsize=4, linestyle="none", markerfacecolor="white",
                        color=line[0].get_color(), label=f"{name} (no todas alcanzan)")
    ax.set_xlabel("$x_0$ (m)")
    ax.set_ylabel("Tiempo $t_{90}$ (s)")
    ax.legend()
    fig.savefig(out / "t90_vs_x0.png")
    plt.close(fig)
    print(f"\nFiguras en {out}/")


if __name__ == "__main__":
    main()
