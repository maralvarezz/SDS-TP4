"""Lectura de salidas del billar circular y observables derivados (postproceso).

El motor solo escribe posiciones y velocidades (states.txt), el evento de primer contacto (contacts.txt)
y metadatos. Todo observable (energia, F_u, t90, ...) se calcula aca.
"""
from pathlib import Path

import numpy as np


def read_kv(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


def read_meta(run_dir):
    m = read_kv(Path(run_dir) / "metadata.txt")
    return {
        "seed": int(m["seed"]), "dt": float(m["dt_s"]), "tf": float(m["totalTime_s"]), "n": int(m["N"]),
        "r": float(m["particleRadius_m"]), "m": float(m["particleMass_kg"]), "R": float(m["domainRadius_m"]),
        "k": float(m["springConstant_N_per_m"]), "obstacles": m["obstaclesEnabled"] == "true",
        "x0": float(m["obstacleX0_m"]),
        "v0": float(m["initialSpeed_mps"]),
    }


def read_runtime_ms(run_dir):
    f = Path(run_dir) / "summary.txt"
    return float(read_kv(f).get("runtimeMilliseconds", "nan")) if f.exists() else float("nan")


def read_states(run_dir):
    """Devuelve (t[S], x[S,N], y[S,N], vx[S,N], vy[S,N], used[S,N]) desde states.txt."""
    data = np.loadtxt(Path(run_dir) / "states.txt")
    n = read_meta(run_dir)["n"]
    s = data.shape[0] // n
    data = data[: s * n].reshape(s, n, 7)
    return data[:, 0, 0], data[:, :, 2], data[:, :, 3], data[:, :, 4], data[:, :, 5], data[:, :, 6].astype(bool)


def read_contacts(run_dir):
    """Devuelve (ids, tiempos) del primer contacto con un obstaculo, ordenados por tiempo."""
    f = Path(run_dir) / "contacts.txt"
    data = np.loadtxt(f, ndmin=2)
    if data.size == 0:
        return np.zeros(0, int), np.zeros(0)
    return data[:, 0].astype(int), data[:, 1]


def kinetic_energy(m, vx, vy):
    """Energia cinetica total por instante: (m/2) sum_i |v_i|^2. vx, vy de forma [S, N]."""
    return 0.5 * m * np.sum(vx ** 2 + vy ** 2, axis=1)


def potential_energy(meta, x, y):
    """Energia potencial elastica total por instante, mismo modelo que la fuerza (F = -k xi, U = k xi^2 / 2):
    pares: xi = 2r - d_ij ; pared: xi = |r_i| + r - R ; obstaculos en (+-x0, 0): xi = 2r - d. Solo xi > 0 cuenta."""
    r, R, k = meta["r"], meta["R"], meta["k"]
    s, n = x.shape
    u = np.zeros(s)
    iu = np.triu_indices(n, 1)
    with np.errstate(invalid="ignore", over="ignore"):
        for t in range(s):
            d = np.hypot(x[t, :, None] - x[t, None, :], y[t, :, None] - y[t, None, :])[iu]
            xi = 2 * r - d
            u[t] += np.sum(xi[xi > 0] ** 2)
            xw = np.hypot(x[t], y[t]) + r - R
            u[t] += np.sum(xw[xw > 0] ** 2)
            if meta["obstacles"]:
                for sign in (-1.0, 1.0):
                    xo = 2 * r - np.hypot(x[t] - sign * meta["x0"], y[t])
                    u[t] += np.sum(xo[xo > 0] ** 2)
    return 0.5 * k * u


def total_energy(meta, x, y, vx, vy):
    return kinetic_energy(meta["m"], vx, vy) + potential_energy(meta, x, y)
