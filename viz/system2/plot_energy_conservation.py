import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.billiard_io import read_meta, read_runtime_ms, read_states, total_energy
from common.style import apply_style, plt


def load_runs(root):
    runs = []
    for states_file in sorted(Path(root).glob("*/seed_*/states.txt")):
        d = states_file.parent
        meta = read_meta(d)
        t, x, y, vx, vy, _ = read_states(d)
        runs.append({
            "dt": meta["dt"], "seed": meta["seed"], "n": meta["n"],
            "t": t, "e": total_energy(meta, x, y, vx, vy),
            "runtime_ms": read_runtime_ms(d),
        })
        print(f"leida {d}", file=sys.stderr)
    if not runs:
        sys.exit(f"No hay corridas con states.txt en {root}")
    return runs


def dt_label(dt):
    m, e = f"{dt:.0e}".split("e")
    mant = "" if m == "1" else f"{m}\\times "
    return rf"dt = ${mant}10^{{{int(e)}}}$ s"


def deltas(run):
    dev = run["e"] - run["e"][0]
    if not np.all(np.isfinite(dev)):
        return np.inf, np.inf, dev
    return np.max(np.abs(dev)), np.sqrt(np.mean(dev ** 2)), dev


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("--out-dir", default="output/figures/2_1a")
    p.add_argument("--show-dts", type=float, nargs="*", help="dt cuyas series temporales se grafican")
    p.add_argument("--seed", type=int, help="semilla de la corrida cuya serie temporal se grafica (por defecto, la menor de cada dt)")
    p.add_argument("--max-only", action="store_true", help="en la figura de desviacion vs dt, graficar solo la desviacion maxima")
    p.add_argument("--tolerance", type=float, help="tolerancia relativa (fraccion de E_0); se dibuja como linea horizontal tolerancia*E_0")
    args = p.parse_args()

    apply_style()
    runs = load_runs(args.root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    by_dt = defaultdict(list)
    for r in runs:
        by_dt[r["dt"]].append(r)
    dts = sorted(by_dt)
    show = sorted(args.show_dts) if args.show_dts else dts

    print(f"{'dt (s)':>10} {'runs':>4} {'delta_max':>22} {'delta_rms':>22} {'runtime (s)':>12}")
    stats = []
    for dt in dts:
        dm, dr = zip(*[deltas(r)[:2] for r in by_dt[dt]])
        dm, dr = np.array(dm), np.array(dr)
        rt = np.nanmean([r["runtime_ms"] for r in by_dt[dt]]) / 1000
        stats.append((dt, dm.mean(), dm.std(ddof=0), dr.mean(), dr.std(ddof=0)))
        print(f"{dt:10.1e} {len(dm):4d} {dm.mean():10.3e} ± {dm.std():9.2e} {dr.mean():10.3e} ± {dr.std():9.2e} {rt:12.2f}")
    stats = np.array(stats)

    fig, ax = plt.subplots()
    for dt in show:
        cand = sorted(by_dt[dt], key=lambda x: x["seed"])
        if args.seed is not None:
            cand = [x for x in cand if x["seed"] == args.seed]
            if not cand:
                sys.exit(f"No hay corrida con semilla {args.seed} para dt = {dt:g}")
        r = cand[0]
        ax.plot(r["t"], np.abs(r["e"] - r["e"][0]), linewidth=1.5, label=dt_label(dt))
    ax.set_yscale("log")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Desviación de la energía (J)")
    lo, hi = ax.get_ylim()
    ax.set_ylim(lo, hi * 10 ** 1.8)
    ax.legend(loc="upper left", fontsize=15)
    fig.savefig(out / "energy_abs_deviation_vs_time.png")
    plt.close(fig)

    in_show = np.array([any(abs(dt - d) <= 1e-9 * max(dt, d) for d in show) for dt in stats[:, 0]])
    finite = np.isfinite(stats[:, 1]) & in_show
    fig, ax = plt.subplots()
    ax.errorbar(stats[finite, 0], stats[finite, 1], yerr=stats[finite, 2], marker="o", markersize=5, capsize=4, elinewidth=1.5, capthick=1.5,
                linestyle="-", linewidth=1, label="Máxima")
    if not args.max_only:
        ax.errorbar(stats[finite, 0], stats[finite, 3], yerr=stats[finite, 4], marker="s", markersize=5, capsize=4, elinewidth=1.5, capthick=1.5,
                    linestyle="-", linewidth=1, label="Cuadrática media")
    if args.tolerance:
        e0 = np.mean([r["e"][0] for r in runs])
        ax.axhline(args.tolerance * e0, color="k", linestyle="--", linewidth=1, label="Tolerancia")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Paso temporal (s)")
    ax.set_ylabel("Desviación de la energía (J)")
    ax.legend()
    ax.grid(True, which="major", alpha=0.3)
    fig.savefig(out / "energy_deviation_vs_dt.png")
    plt.close(fig)
    if not np.all(finite):
        print("Aviso: dt con energia no finita (simulacion inestable) omitidos en la figura:", stats[~finite, 0])
    print(f"Figuras en {out}/")


if __name__ == "__main__":
    main()
