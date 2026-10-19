"""Punto 2.1.b: tiempo de ejecucion vs N (billar con obstaculos en contacto, t_f = 30 s).

Lee <root>/*/seed_*/ : metadata.txt (N) y summary.txt (runtimeMilliseconds). Alcance del tiempo medido:
lazo de integracion + escrituras habilitadas; excluye la generacion de condiciones iniciales.

Observable: T(N) = tiempo de ejecucion de una corrida. Para cada N se reporta la media y el desvio estandar
muestral (ddof = 1) entre las realizaciones.

Ajuste de la ley T = c N^b (Teorica 0): para cada exponente b de una grilla, el c que minimiza
E(b, c) = sum_i [T_i - c N_i^b]^2 es c(b) = sum_i T_i N_i^b / sum_i N_i^(2b); se grafica E(b) = E(b, c(b)) y el
minimo da el exponente. Las T_i son las medias por N.

Comparacion con TP3 (misma computadora): --tp3-log guarda la salida de viz/hexagonal_execution_time.py del TP3
(lineas "N=25 realizacion 1/10 seed=... runtime=... ms"); se recalculan media y desvio con el mismo criterio.

Uso: python3 viz/system2/plot_runtime_vs_N.py output/sys2_exp1b --out-dir output/figures/sys2_exp1b [--tp3-log tp3.log]
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.billiard_io import read_kv, read_meta, read_runtime_ms  # noqa: E402
from common.style import apply_style, plt  # noqa: E402


def load_tp4(root):
    by_n = defaultdict(list)
    steps = None
    for summary in sorted(Path(root).glob("*/seed_*/summary.txt")):
        d = summary.parent
        meta = read_meta(d)
        by_n[meta["n"]].append(read_runtime_ms(d) / 1000.0)
        steps = int(read_kv(summary)["steps"])
    if not by_n:
        sys.exit(f"No hay corridas con summary.txt en {root}")
    return by_n, steps


def load_tp3(path):
    by_n = defaultdict(list)
    pat = re.compile(r"N=(\d+) realizacion \d+/\d+ seed=\d+ runtime=([\d.]+) ms")
    for line in Path(path).read_text().splitlines():
        m = pat.search(line)
        if m:
            by_n[int(m.group(1))].append(float(m.group(2)) / 1000.0)
    if not by_n:
        sys.exit(f"No se encontraron lineas de runtime en {path}")
    return by_n


def stats(by_n):
    ns = np.array(sorted(by_n))
    mean = np.array([np.mean(by_n[n]) for n in ns])
    std = np.array([np.std(by_n[n], ddof=1) if len(by_n[n]) > 1 else 0.0 for n in ns])
    count = np.array([len(by_n[n]) for n in ns])
    return ns, mean, std, count


def power_scan(ns, t, exponents):
    errs, cs = [], []
    for b in exponents:
        x = ns.astype(float) ** b
        c = np.sum(t * x) / np.sum(x * x)
        cs.append(c)
        errs.append(np.sum((t - c * x) ** 2))
    return np.array(errs), np.array(cs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("--out-dir", default="output/figures/sys2_exp1b")
    p.add_argument("--tp3-log")
    p.add_argument("--label-tp4", default="Paso temporal (TP4)")
    p.add_argument("--label-tp3", default="Eventos (TP3)")
    args = p.parse_args()

    apply_style()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tp4, steps = load_tp4(args.root)
    series = {args.label_tp4: stats(tp4)}
    if args.tp3_log:
        series[args.label_tp3] = stats(load_tp3(args.tp3_log))

    exponents = np.linspace(0.5, 6.0, 1101)
    fits = {}
    for name, (ns, mean, std, count) in series.items():
        print(f"\n{name}\n{'N':>5} {'runs':>4} {'T media (s)':>12} {'sigma (s)':>10}")
        for n, m, s, c in zip(ns, mean, std, count):
            print(f"{n:5d} {c:4d} {m:12.3f} {s:10.3f}")
        errs, cs = power_scan(ns, mean, exponents)
        i = int(np.argmin(errs))
        fits[name] = (exponents, errs, exponents[i], cs[i])
        print(f"Ajuste T = c N^b: b = {exponents[i]:.2f}, c = {cs[i]:.3e} s, E_min = {errs[i]:.3e} s^2")
        if i in (0, len(exponents) - 1):
            print("AVISO: el minimo cae en el borde de la grilla de b; el ajuste no es valido")
        local = np.diff(np.log(mean)) / np.diff(np.log(ns))
        print("Exponente local entre N consecutivos:", " ".join(f"{v:.2f}" for v in local))

    markers = ["o", "s"]
    for scale in ("lin", "log"):
        fig, ax = plt.subplots()
        for (name, (ns, mean, std, _)), mk in zip(series.items(), markers):
            ax.errorbar(ns, mean, yerr=std, marker=mk, markersize=5, capsize=4, elinewidth=1.5, capthick=1.5, linestyle="-", linewidth=1, label=name)
        ax.set_xscale("log")
        ax.set_yscale("log")
        all_n = sorted(set().union(*[set(v[0].tolist()) for v in series.values()]))
        ax.set_xticks(all_n)
        ax.set_xticklabels([str(n) if n in (25, 50, 100, 200, 300, 500, 700) else "" for n in all_n])
        ax.xaxis.set_minor_formatter(plt.NullFormatter())
        ax.grid(True, which="major", alpha=0.3)
        ax.set_xlabel("Cantidad de partículas")
        ax.set_ylabel("Tiempo de ejecución (s)")
        ax.legend()
        fig.savefig(out / f"runtime_vs_N_{scale}.png")
        plt.close(fig)

    # Zoom en el cruce TP4 / TP3. El cruce se estima suponiendo que, entre dos N medidos consecutivos, log T es lineal
    # en log N (es decir, las rectas que se ven en la escala log-log) y resolviendo la interseccion de ambas rectas.
    if len(series) == 2:
        (n4, m4, s4, _), (n3, m3, s3, _) = series.values()
        common = sorted(set(n4.tolist()) & set(n3.tolist()))
        i4 = {n: i for i, n in enumerate(n4.tolist())}
        i3 = {n: i for i, n in enumerate(n3.tolist())}
        cross = None
        for a, b in zip(common[:-1], common[1:]):
            la, lb = np.log(a), np.log(b)
            d_a = np.log(m4[i4[a]]) - np.log(m3[i3[a]])
            d_b = np.log(m4[i4[b]]) - np.log(m3[i3[b]])
            if d_a * d_b < 0:  # cambia el signo de log(T4/T3): hay cruce en [a, b]
                f = d_a / (d_a - d_b)
                ln_star = la + f * (lb - la)
                t_star = np.exp(np.log(m4[i4[a]]) + f * (np.log(m4[i4[b]]) - np.log(m4[i4[a]])))
                cross = (a, b, np.exp(ln_star), t_star)
                break
        if cross:
            a, b, n_star, t_star = cross
            print(f"\nCruce TP4/TP3 entre N={a} y N={b}: N* = {n_star:.0f}, T* = {t_star:.2f} s (interpolacion log-log)")
            # zoom moderado: un N medido antes y uno despues del par que enmarca el cruce, con algo de margen
            k = common.index(a)
            x_lo = common[max(k - 1, 0)] * 0.7
            x_hi = common[min(k + 2, len(common) - 1)] * 1.085
            fig, ax = plt.subplots()
            vis = []
            for (name, (ns, mean, std, _)), mk in zip(series.items(), markers):
                ax.errorbar(ns, mean, yerr=std, marker=mk, markersize=5, capsize=4, elinewidth=1.5, capthick=1.5,
                            linestyle="-", linewidth=1, label=name)
                vis += [m for n, m in zip(ns, mean) if x_lo <= n <= x_hi]
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlim(x_lo, x_hi)
            y_lo = min(vis) * 0.25
            ax.set_ylim(y_lo, max(vis) * 0.8)
            # punto de cruce y linea punteada que baja hasta el eje x, donde se rotula su valor
            ax.vlines(n_star, y_lo, t_star, color="k", linestyle=":", linewidth=1.5, zorder=4)
            ax.plot([n_star], [t_star], marker="o", markersize=9, color="k", linestyle="none", zorder=5)
            ticks = [n for n in common if x_lo <= n <= x_hi] + [n_star]
            ax.set_xticks(ticks)
            ax.set_xticklabels([f"{n_star:.0f}" if n == n_star else str(n) for n in ticks])
            ax.xaxis.set_minor_formatter(plt.NullFormatter())
            ax.grid(True, which="major", alpha=0.3)
            ax.set_xlabel("Cantidad de partículas")
            ax.set_ylabel("Tiempo de ejecución (s)")
            ax.legend(loc="upper left", fontsize=15)
            fig.savefig(out / "runtime_vs_N_zoom_cruce.png")
            plt.close(fig)
        else:
            print("\nAviso: las curvas TP4 y TP3 no se cruzan en el rango medido; no se genera el zoom.")

    # Costo por paso y por particula: t_c = T / (pasos * N). Si el costo fuera exactamente lineal en N seria constante.
    ns, mean, std, _ = series[args.label_tp4]
    scale_ns = 1e9 / (steps * ns)
    print(f"\nCosto por paso y por particula (ns), pasos = {steps}:")
    for n, v in zip(ns, mean * scale_ns):
        print(f"{n:5d} {v:8.2f}")
    fig, ax = plt.subplots()
    ax.errorbar(ns, mean * scale_ns, yerr=std * scale_ns, marker="o", markersize=8, capsize=4, linestyle="-", linewidth=1)
    ax.set_xlabel("Cantidad de partículas")
    ax.set_ylabel("Tiempo por paso y por partícula (ns)")
    fig.savefig(out / "runtime_per_step_particle.png")
    plt.close(fig)

    fig, ax = plt.subplots()
    for name, (ex, errs, b, _) in fits.items():
        line, = ax.plot(ex, errs, linewidth=2, label=name)
        ax.plot([b], [errs.min()], "o", markersize=9, color=line.get_color())
    ax.set_yscale("log")
    ax.set_xlabel("Exponente $b$")
    ax.set_ylabel("Error $E(b)$ (s$^2$)")
    ax.legend()
    fig.savefig(out / "runtime_fit_error.png")
    plt.close(fig)
    print(f"\nFiguras en {out}/")


if __name__ == "__main__":
    main()
