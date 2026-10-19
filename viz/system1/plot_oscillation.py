"""Oscilacion del Sistema 1 (oscilador amortiguado): posicion vs tiempo, solucion analitica y los cuatro integradores.

Lee output/<run>/trajectory_<metodo>_dt<dt>.txt (columnas: t, r_numerica, r_analitica).
Uso: python viz/system1/plot_oscillation.py output/system1 --dt 5.000000e-03 --out output/figures/system1_oscilacion.png
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.style import apply_style, plt  # noqa: E402

LABELS = {"beeman": "Beeman", "verlet": "Verlet original",
          "velocityVerlet": "Velocity Verlet", "eulerPC": "Euler predictor-corrector"}
MARKERS = {"beeman": "o", "verlet": "s", "velocityVerlet": "^", "eulerPC": "D"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_dir")
    p.add_argument("--dt", default="5.000000e-03", help="sufijo del archivo, ej. 5.000000e-03")
    p.add_argument("--stride", type=int, default=20, help="un marcador cada tantos pasos")
    p.add_argument("--out", default="output/figures/system1_oscilacion.png")
    args = p.parse_args()

    apply_style()
    fig, ax = plt.subplots()
    analytic = None
    for i, method in enumerate(LABELS):
        f = Path(args.run_dir) / ("trajectory_%s_dt%s.txt" % (method, args.dt))
        d = np.loadtxt(f)
        analytic = d
        s = slice(i * args.stride // 4, None, args.stride)
        ax.plot(d[s, 0], d[s, 1], MARKERS[method], markersize=7, markerfacecolor="none", markeredgewidth=1.5,
                label=LABELS[method])
    ax.plot(analytic[:, 0], analytic[:, 2], "k-", linewidth=1.5, label="Analítica", zorder=0)
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Posición (m)")
    ax.legend(loc="upper right")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out)
    print("Figura guardada en", args.out)


if __name__ == "__main__":
    main()
