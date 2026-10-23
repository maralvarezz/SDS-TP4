import argparse, subprocess, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import EllipseCollection
from matplotlib.patches import Circle

plt.rcParams.update({"font.size": 20})


def read_meta(path):
    d = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_dir")
    p.add_argument("--out", default=None)
    p.add_argument("--stride", type=int, default=4)
    p.add_argument("--speed", type=float, default=1.0, help="velocidad respecto del tiempo real (1 = tiempo real)")
    p.add_argument("--tmax", type=float, default=None, help="tiempo final de la animacion (s)")
    p.add_argument("--size", type=float, default=7.0, help="lado de la figura (pulgadas)")
    p.add_argument("--dpi", type=int, default=120)
    args = p.parse_args()

    run = Path(args.run_dir)
    meta = read_meta(run / "metadata.txt")
    R, r, x0 = float(meta["domainRadius_m"]), float(meta["particleRadius_m"]), float(meta["obstacleX0_m"])
    data = np.loadtxt(run / "states.txt", comments="#")
    t_all = np.unique(data[:, 0])
    n = int(meta["N"])
    data = data[np.argsort(data[:, 0], kind="stable")].reshape(len(t_all), n, -1)
    order = np.argsort(data[:, :, 1], axis=1)
    data = np.take_along_axis(data, order[:, :, None], axis=1)
    dt_state = float(t_all[1] - t_all[0])
    fps = args.speed / (args.stride * dt_state)
    frames = np.arange(0, len(t_all), args.stride)
    if args.tmax is not None:
        frames = frames[t_all[frames] <= args.tmax]

    fig, ax = plt.subplots(figsize=(args.size, args.size))
    ax.set_xlim(-R * 1.03, R * 1.03); ax.set_ylim(-R * 1.03, R * 1.03); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Circle((0, 0), R, fill=False, edgecolor="k", linewidth=2))
    for sx in (-1, 1):
        ax.add_patch(Circle((sx * x0, 0), r, facecolor="k", edgecolor="k"))
    first = data[frames[0]]
    coll = EllipseCollection(widths=2 * r, heights=2 * r, angles=0, units="xy", offsets=first[:, 2:4],
                             offset_transform=ax.transData, facecolors="tab:blue", edgecolors="k", linewidths=0.5)
    ax.add_collection(coll)
    txt = ax.text(0.5, 1.0, "", transform=ax.transAxes, ha="center", va="bottom", fontsize=20)
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.93)

    out = Path(args.out) if args.out else run / "animacion.mp4"
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}",
           "-r", f"{fps:.6f}", "-i", "-", "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        s = data[f]
        coll.set_offsets(s[:, 2:4])
        coll.set_facecolor(np.where(s[:, 6] > 0.5, "tab:red", "tab:blue"))
        fu = s[:, 6].mean()
        txt.set_text(f"$t$ = {t_all[f]:.2f} s    $F_u$ = {fu:.2f}")
        fig.canvas.draw()
        ff.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
    ff.stdin.close(); ff.wait()
    real = (t_all[frames[-1]] - t_all[frames[0]])
    print(f"{out}: {len(frames)} frames, {len(frames) / fps:.1f} s de video, {real:.1f} s simulados "
          f"(x{real / (len(frames) / fps):.2f} del tiempo real, {fps:.2f} fps)")


if __name__ == "__main__":
    main()
