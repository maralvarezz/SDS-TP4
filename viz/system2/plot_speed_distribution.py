"""Punto 2.3: distribucion de rapideces f(v) y ajuste de Maxwell-Boltzmann (N = 100, sin obstaculos).

Lee <root>/*/seed_*/states.txt (posiciones y velocidades) y metadata.txt. Todo observable se calcula aca.

Observables:
  v_i(t)  = |velocidad de la particula i| en el instante t
  <v>(t)  = (1/N) sum_i v_i(t)                       (evolucion temporal; sirve para elegir el estacionario)
  f(v)    : PDF por histograma, y_j = N_j / (N_total * dv_j)  (N_j: cuentas en el bin j, N_total: muestras totales)
Modelo (2D): f(v; kBT) = (m v / kBT) exp(-m v^2 / (2 kBT)), con kBT como unico parametro libre.
Ajuste (Teorica 0): E(kBT) = sum_j [ y_j - f(v_j; kBT) ]^2 sobre los centros v_j de los bins; se barre kBT en una
grilla y el minimo de E da el valor ajustado. Se ajusta cada realizacion por separado y se informa media y desvio
muestral (ddof = 1) entre realizaciones; la curva E(kBT) mostrada es la del histograma promedio.
Referencia (no es un ajuste): kBT = m v0^2 / 2 = energia cinetica inicial por particula.

El estado estacionario se elige a mano: primero correr SIN --t-start para ver <v>(t); luego repetir con --t-start.
Con --t-start se ajusta k_BT en el estacionario y se grafica, para cada instante de --times, el histograma de f(v) (todas las
realizaciones juntas, en el instante guardado mas cercano) junto a la curva de Maxwell-Boltzmann ajustada (media y desvio muestral entre realizaciones): se ve como la
distribucion parte lejos de la curva (t = 0: todas con |v| = v0) y se va pareciendo a ella.

Uso: python3 viz/system2/plot_speed_distribution.py output/sys2_exp3 --out-dir output/figures/sys2_exp3
        [--t-start 2] [--times 0 0.1 0.3 1 3 10] [--bins 40] [--vmax 3]
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.billiard_io import read_meta, read_states  # noqa: E402
from common.style import apply_style, plt  # noqa: E402


def mb_pdf(v, m, kbt):
    return (m * v / kbt) * np.exp(-m * v ** 2 / (2 * kbt))


def mb_mean_speed(m, kbt):
    return math.sqrt(math.pi * kbt / (2 * m))


def histogram_pdf(speeds, edges):
    counts, _ = np.histogram(speeds, bins=edges)
    return counts / (speeds.size * np.diff(edges))


def fit_kbt(centers, y, m, grid):
    err = np.array([np.sum((y - mb_pdf(centers, m, c)) ** 2) for c in grid])
    return grid[int(np.argmin(err))], err


def fmt_pm(mean, std):
    """Cifras significativas del valor segun el error (1 cifra, 2 si empieza en 1)."""
    if not np.isfinite(std) or std <= 0:
        return f"{mean:.4g}"
    exp = math.floor(math.log10(std))
    digits = 1 if int(std / 10 ** exp) != 1 else 2
    dec = -(exp - (digits - 1))
    return f"{round(mean, dec):.{max(dec, 0)}f} ± {round(std, dec):.{max(dec, 0)}f}"


def load(root):
    runs = []
    for states in sorted(Path(root).glob("*/seed_*/states.txt")):
        d = states.parent
        if not (d / "summary.txt").exists():
            continue
        meta = read_meta(d)
        t, _, _, vx, vy, _ = read_states(d)
        runs.append({"meta": meta, "t": t, "v": np.hypot(vx, vy)})
    if not runs:
        sys.exit(f"No hay corridas completas con states.txt en {root}")
    return runs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("--out-dir", default="output/figures/sys2_exp3")
    p.add_argument("--t-start", type=float, help="inicio del estado estacionario (s); se elige mirando <v>(t)")
    p.add_argument("--times", type=float, nargs="*", default=[0.0, 0.1, 0.3, 1.0, 3.0, 10.0],
                   help="instantes (s) para los que se grafica f(v) junto a la curva ajustada")
    p.add_argument("--bins", type=int, default=40)
    p.add_argument("--vmax", type=float, default=3.0)
    args = p.parse_args()

    apply_style()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    runs = load(args.root)
    meta = runs[0]["meta"]
    m, v0, n = meta["m"], meta["v0"], meta["n"]
    e0 = 0.5 * m * v0 ** 2
    t = runs[0]["t"]
    edges = np.linspace(0, args.vmax, args.bins + 1)
    centers = 0.5 * (edges[1:] + edges[:-1])
    print(f"{len(runs)} realizaciones, N = {n}, m = {m} kg, v0 = {v0} m/s, m v0^2/2 = {e0:.5f} J, {len(t)} instantes")

    # --- <v>(t) ---
    mean_v = np.array([r["v"].mean(axis=1) for r in runs])
    mu, sd = mean_v.mean(axis=0), mean_v.std(axis=0, ddof=1) if len(runs) > 1 else np.zeros(len(t))
    fig, ax = plt.subplots()
    ax.plot(t, mu, linewidth=2, label="Simulación")
    if args.t_start is not None:
        ax.axvline(args.t_start, color="tab:red", linestyle=":", linewidth=2, label="Inicio del estacionario")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Rapidez media (m/s)")
    ax.legend()
    fig.savefig(out / "mean_speed_vs_time.png")
    plt.close(fig)

    if args.t_start is None:
        print("\nElegir el inicio del estado estacionario mirando mean_speed_vs_time.png y repetir con --t-start <s>.")
        print(f"Figuras en {out}/")
        return

    # --- estado estacionario + ajuste ---
    sel = t >= args.t_start
    if sel.sum() < 2:
        sys.exit("t-start deja menos de 2 instantes")
    grid = np.linspace(0.3 * e0, 2.0 * e0, 4001)
    ys, fits = [], []
    for r in runs:
        y = histogram_pdf(r["v"][sel].ravel(), edges)
        ys.append(y)
        fits.append(fit_kbt(centers, y, m, grid)[0])
    ys, fits = np.array(ys), np.array(fits)
    y_mean = ys.mean(axis=0)
    y_std = ys.std(axis=0, ddof=1) if len(runs) > 1 else np.zeros_like(y_mean)
    k_mean, k_std = fits.mean(), fits.std(ddof=1) if len(fits) > 1 else 0.0
    k_pool, err_pool = fit_kbt(centers, y_mean, m, grid)
    print(f"\nEstado estacionario: t >= {args.t_start:g} s ({int(sel.sum())} instantes por realizacion), {args.bins} bins en [0, {args.vmax:g}] m/s")
    for r, k in zip(runs, fits):
        print(f"  seed {r['meta']['seed']}: kBT = {k:.5f} J")
    print(f"kBT (media ± sigma entre realizaciones) = {fmt_pm(k_mean, k_std)} J")
    print(f"kBT del histograma promedio = {k_pool:.5f} J   |  m v0^2/2 = {e0:.5f} J  |  cociente kBT/(m v0^2/2) = {k_mean / e0:.3f}")
    print(f"<v> medida en el estacionario = {mean_v[:, sel].mean():.4f} m/s  |  <v> MB ajustado = {mb_mean_speed(m, k_mean):.4f} m/s")

    # --- evolucion temporal: f(v) en cada instante vs la curva de Maxwell-Boltzmann ajustada (misma curva en todos) ---
    vv = np.linspace(1e-4, args.vmax, 400)
    mb_curve = mb_pdf(vv, m, k_mean)
    y_common = 1.6 * mb_curve.max()
    for tt in args.times:
        i = int(np.argmin(np.abs(t - tt)))
        # histograma de cada realizacion en el instante t (N muestras); barras = media, barras de error = desvio muestral
        ys_t = np.array([histogram_pdf(r["v"][i], edges) for r in runs])
        y = ys_t.mean(axis=0)
        y_sd = ys_t.std(axis=0, ddof=1) if len(runs) > 1 else np.zeros_like(y)
        fig, ax = plt.subplots()
        ax.bar(centers, y, width=np.diff(edges), yerr=y_sd, capsize=3, alpha=0.6, color="tab:blue",
               error_kw={"elinewidth": 1.2, "ecolor": "k"}, label="Simulación")
        ax.plot(vv, mb_curve, color="tab:red", linewidth=2.5, label="Maxwell-Boltzmann")
        ax.set_ylim(0, max(y_common, 1.05 * (y + y_sd).max()))
        ax.set_xlabel("Rapidez (m/s)")
        ax.set_ylabel("$f(v)$ (s/m)")
        ax.legend(title=f"$t$ = {t[i]:g} s", loc="upper right")
        fig.savefig(out / (f"fv_t_{t[i]:.2f}".replace(".", "p") + ".png"))
        plt.close(fig)
        print(f"f(v) en t = {t[i]:.2f} s: {len(runs)} realizaciones x {n} particulas")

    vv = np.linspace(1e-4, args.vmax, 400)
    fig, ax = plt.subplots()
    ax.errorbar(centers, y_mean, yerr=y_std, fmt="o", markersize=6, capsize=3, label="Simulación")
    ax.plot(vv, mb_pdf(vv, m, k_mean), linewidth=2.5, label="Ajuste")
    ax.set_xlabel("Rapidez (m/s)")
    ax.set_ylabel("$f(v)$ (s/m)")
    ax.legend()
    fig.savefig(out / "fv_steady_fit.png")
    plt.close(fig)

    # Error del ajuste E(c) (Teorica 0, diapositiva 70): escala lineal y ventana alrededor del minimo c*,
    # con lineas que bajan de E(c*) a los ejes.
    win = (grid >= 0.7 * k_pool) & (grid <= 1.3 * k_pool)
    e_min = err_pool.min()
    fig, ax = plt.subplots()
    ax.plot(grid[win], err_pool[win], linewidth=2.5, color="tab:blue")
    ax.plot([k_pool], [e_min], "o", markersize=9, color="tab:orange", zorder=5, clip_on=False)
    ax.vlines(k_pool, 0, e_min, color="k", linestyle=":", linewidth=1.5)
    ax.hlines(e_min, grid[win].min(), k_pool, color="k", linestyle=":", linewidth=1.5)
    ax.set_xlim(grid[win].min(), grid[win].max())
    ax.set_ylim(0, err_pool[win].max() * 1.05)
    ticks = [t for t in ax.get_xticks() if grid[win].min() <= t <= grid[win].max() and abs(t - k_pool) > 0.06 * k_pool]
    ax.set_xticks(ticks + [k_pool])
    ax.set_xticklabels([f"{t:.3f}" for t in ticks] + [f"{k_pool:.4f}"])
    ax.set_xlabel("$k_BT$ (J)")
    ax.set_ylabel("Error $E(k_BT)$ (s$^2$/m$^2$)")
    fig.savefig(out / "fit_error.png")
    plt.close(fig)
    print(f"Figuras en {out}/")


if __name__ == "__main__":
    main()
