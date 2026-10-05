"""Estilo comun de figuras (Guia de presentaciones: sin titulos, fuente >= 20, notacion 10^n)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

FONT_SIZE = 20


def apply_style():
    plt.rcParams.update({
        "font.size": FONT_SIZE,
        "axes.labelsize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE,
        "ytick.labelsize": FONT_SIZE,
        "legend.fontsize": FONT_SIZE - 2,
        "axes.formatter.use_mathtext": True,
        "figure.figsize": (10, 7),
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })
