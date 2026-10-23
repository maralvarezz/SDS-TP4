import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.style import apply_style, plt

LABELS = {"beeman": "Beeman", "verlet": "Verlet original",
          "velocityVerlet": "Velocity Verlet", "eulerPC": "Euler predictor-corrector"}
MARKERS = {"beeman": "o", "verlet": "s", "velocityVerlet": "^", "eulerPC": "D"}


def load(path):
    data = {}
    for line in Path(path).read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        method, dt, _steps, ecm = line.split()
        data.setdefault(method, []).append((float(dt), float(ecm)))
    return {m: np.array(sorted(v)) for m, v in data.items()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("ecm_file")
    p.add_argument("--out", default="output/figures/system1_ecm_vs_dt.png")
    args = p.parse_args()

    apply_style()
    fig, ax = plt.subplots()
    for method, arr in load(args.ecm_file).items():
        ax.plot(arr[:, 0], arr[:, 1], marker=MARKERS.get(method, "o"), linestyle="-", linewidth=1,
                markersize=8, label=LABELS.get(method, method))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Paso temporal (s)")
    ax.set_ylabel("Error cuadrático medio (m$^2$)")
    ax.legend()
    ax.grid(True, which="major", alpha=0.3)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out)
    print(f"Figura guardada en {args.out}")


if __name__ == "__main__":
    main()
