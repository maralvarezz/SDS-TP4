"""Punto 2.4: tiempos t90 y t100 vs densidad. Reutiliza las corridas de 2.1.b (obstaculos en contacto, x0 = r).

Lee <root>/*/seed_*/ : contacts.txt (evento fresca->usada, "id t_s"), metadata.txt (N, R, totalTime). No se simula nada nuevo.
Definiciones (se calculan aca; el motor solo registra el evento):
  rho     = N / (pi R^2)                      densidad de particulas (1/m^2), R = radio del dominio
  F_u(t)  = (cantidad de particulas con primer contacto <= t) / N
  t90     = instante del ceil(0.9 N)-esimo primer contacto   (menor t con F_u >= 0.9)
  t100    = instante del N-esimo primer contacto             (menor t con F_u = 1)
Si una corrida no alcanza el umbral antes de t_max, ese tiempo "no esta alcanzado" y la corrida no entra en la media
(la media sobre las que si lo alcanzan queda subestimada: se informa cuantas lo alcanzan). Tambien se grafica F_u(t_max).
Media y desvio muestral (ddof = 1) entre realizaciones.

Se pueden pasar varias carpetas: para cada N se usa la corrida de la ULTIMA carpeta que lo contenga (permite alargar t_max
solo para los N altos). Cada N conserva su propio t_max.

Uso: python3 viz/system2/plot_t90_t100_vs_density.py output/sys2_exp4 output/sys2_exp4_long --out-dir output/figures/sys2_exp4
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


def load(root):
    by_n = defaultdict(list)
    for contacts in sorted(Path(root).glob("*/seed_*/contacts.txt")):
        d = contacts.parent
        if not (d / "summary.txt").exists():
            continue
        meta = read_meta(d)
        _, times = read_contacts(d)
        times = np.sort(times)
        n = meta["n"]
        k90 = math.ceil(0.9 * n - 1e-9)
        by_n[n].append({
            "R": meta["R"], "tf": meta["tf"],
            "t90": times[k90 - 1] if len(times) >= k90 else np.nan,
            "t100": times[n - 1] if len(times) >= n else np.nan,
            "fu_end": len(times) / n,
        })
    if not by_n:
        sys.exit(f"No hay corridas completas en {root}")
    return by_n


def mean_std(values):
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return np.nan, np.nan, 0
    return v.mean(), (v.std(ddof=1) if v.size > 1 else 0.0), v.size


def plot_series(ax, rho, rows, key, marker, label):
    full = [(r, s) for r, s in zip(rho, rows) if s[key]["k"] == s["runs"]]
    part = [(r, s) for r, s in zip(rho, rows) if 0 < s[key]["k"] < s["runs"]]
    line = None
    if full:
        line = ax.errorbar([r for r, _ in full], [s[key]["mean"] for _, s in full], yerr=[s[key]["std"] for _, s in full],
                           marker=marker, markersize=8, capsize=4, linestyle="-", linewidth=1, label=label)
    if part:
        color = line[0].get_color() if line else None
        ax.errorbar([r for r, _ in part], [s[key]["mean"] for _, s in part], yerr=[s[key]["std"] for _, s in part],
                    marker=marker, markersize=8, capsize=4, linestyle="none", markerfacecolor="white", color=color,
                    label=None if line else label)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("roots", nargs="+")
    p.add_argument("--out-dir", default="output/figures/sys2_exp4")
    args = p.parse_args()

    apply_style()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    by_n = {}
    for root in args.roots:
        by_n.update(load(root))  # la ultima carpeta que contiene a N reemplaza a las anteriores
    ns = sorted(by_n)
    R = by_n[ns[0]][0]["R"]
    tfs = [by_n[n][0]["tf"] for n in ns]
    rho = [n / (math.pi * R ** 2) for n in ns]

    rows = []
    print(f"R = {R} m\n")
    print(f"{'N':>5} {'tmax (s)':>9} {'rho (1/m^2)':>12} {'runs':>5} | {'t90 alc.':>8} {'t90 media (s)':>14} {'sigma':>7} | {'t100 alc.':>9} {'t100 media (s)':>15} {'sigma':>7} | {'Fu(tmax)':>9} {'sigma':>7}")
    for n, r in zip(ns, rho):
        runs = by_n[n]
        row = {"runs": len(runs)}
        for key in ("t90", "t100"):
            m, s, k = mean_std([x[key] for x in runs])
            row[key] = {"mean": m, "std": s, "k": k}
        fm, fs, _ = mean_std([x["fu_end"] for x in runs])
        row["fu"] = {"mean": fm, "std": fs}
        rows.append(row)
        print(f"{n:5d} {runs[0]['tf']:9.0f} {r:12.1f} {len(runs):5d} | {row['t90']['k']:3d}/{len(runs):<4d} {row['t90']['mean']:14.2f} {row['t90']['std']:7.2f} | "
              f"{row['t100']['k']:4d}/{len(runs):<4d} {row['t100']['mean']:15.2f} {row['t100']['std']:7.2f} | {fm:9.3f} {fs:7.3f}")

    fig, ax = plt.subplots()
    plot_series(ax, rho, rows, "t90", "o", "$t_{90}$")
    plot_series(ax, rho, rows, "t100", "s", "$t_{100}$")
    ax.set_yscale("log")
    ax.set_xlabel("Densidad (1/m$^2$)")
    ax.set_ylabel("Tiempo (s)")
    ax.legend()
    fig.savefig(out / "t90_t100_vs_density.png")
    plt.close(fig)

    fig, ax = plt.subplots()
    ax.errorbar(rho, [r["fu"]["mean"] for r in rows], yerr=[r["fu"]["std"] for r in rows], marker="o", markersize=8,
                capsize=4, linestyle="-", linewidth=1)
    ax.axhline(0.9, color="k", linestyle="--", linewidth=1)
    ax.set_xlabel("Densidad (1/m$^2$)")
    ax.set_ylabel("Fracción de partículas usadas en $t_{max}$")
    ax.set_ylim(0, 1.02)
    fig.savefig(out / "fu_tmax_vs_density.png")
    plt.close(fig)
    print(f"\nMarcador vacio: no todas las corridas alcanzan el umbral.")
    print(f"Figuras en {out}/")


if __name__ == "__main__":
    main()
