"""Punto 2.1.a: conservacion de la energia total vs dt (billar sin obstaculos).

Lee, para cada corrida de <root>/*/seed_*/ : states.txt (posiciones y velocidades), metadata.txt y
summary.txt (runtimeMilliseconds). La energia (cinetica + elastica) se calcula aca, en postproceso
(viz/common/billiard_io.py); el motor no escribe observables.

Observable escalar (el sistema es conservativo y sin disipacion, luego toda variacion de E es error numerico):
  E_0           = E(t = 0)  (sin solapes iniciales: E_0 = N m v_0^2 / 2)
  delta_max(dt) = max_t |E(t) - E_0|                    (peor desviacion en toda la corrida, en J)
  delta_rms(dt) = sqrt( mean_t (E(t) - E_0)^2 )         (desviacion tipica sostenida, en J)
Son las mismas magnitudes (absolutas, en J) que la figura de |E(t) - E_0| vs tiempo, para que sean comparables,
y se grafican solo para los dt de --show-dts (los mismos de la figura temporal); la tabla impresa incluye todos.
La tolerancia (--tolerance, relativa) se dibuja como tolerancia * E_0.
Se reporta media y desvio estandar entre seeds (corridas) para cada dt.

Uso: python3 viz/system2/plot_energy_conservation.py output/sys2_exp1a --out-dir output/figures/2_1a
        [--show-dts 1e-5 5e-5 1e-4 5e-4] [--seed 1002] [--tolerance 1e-3]
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.billiard_io import read_meta, read_runtime_ms, read_states, total_energy  # noqa: E402
from common.style import apply_style, plt  # noqa: E402


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
    """Etiqueta con notacion 10^n: 'dt = 5 x 10^-5 s'."""
    m, e = f"{dt:.0e}".split("e")
    mant = "" if m == "1" else f"{m}\\times "
    return rf"dt = ${mant}10^{{{int(e)}}}$ s"


def deltas(run):
    dev = run["e"] - run["e"][0]   # desviacion absoluta (J)
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

    # --- tabla ---
    print(f"{'dt (s)':>10} {'runs':>4} {'delta_max':>22} {'delta_rms':>22} {'runtime (s)':>12}")
    stats = []
    for dt in dts:
        dm, dr = zip(*[deltas(r)[:2] for r in by_dt[dt]])
        dm, dr = np.array(dm), np.array(dr)
        rt = np.nanmean([r["runtime_ms"] for r in by_dt[dt]]) / 1000
        stats.append((dt, dm.mean(), dm.std(ddof=0), dr.mean(), dr.std(ddof=0)))
        print(f"{dt:10.1e} {len(dm):4d} {dm.mean():10.3e} ± {dm.std():9.2e} {dr.mean():10.3e} ± {dr.std():9.2e} {rt:12.2f}")
    stats = np.array(stats)

    # --- Fig 1: desviacion de la energia, |E(t) - E_0|, vs tiempo (escala log) (seed menor de cada dt) ---
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
    ax.set_ylim(lo, hi * 10 ** 1.8)  # espacio libre arriba para la leyenda, dentro del grafico
    ax.legend(loc="upper left", fontsize=15)
    fig.savefig(out / "energy_abs_deviation_vs_time.png")
    plt.close(fig)

    # --- Fig 2: observable escalar vs dt (solo los mismos dt que se muestran en la figura temporal) ---
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
