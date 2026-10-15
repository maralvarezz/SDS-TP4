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
            ax.errorbar(ns, mean, yerr=std, marker=mk, markersize=8, capsize=4, linestyle="-", linewidth=1, label=name)
        if scale == "log":
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.grid(True, which="major", alpha=0.3)
        ax.set_xlabel("Cantidad de partículas")
        ax.set_ylabel("Tiempo de ejecución (s)")
        ax.legend()
        fig.savefig(out / f"runtime_vs_N_{scale}.png")
        plt.close(fig)

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
