package ar.edu.itba.sds.tp4.billiard;

import java.util.Arrays;

public final class ForceField {
    private final double wallRadius, radius, k;
    private final boolean hasObstacles;
    private final double obstacleX0;

    private final double cellSize;
    private final int cellsPerSide;
    private final int[] head, next;

    public ForceField(int n, double wallRadius, double particleRadius, double springConstant,
                      boolean hasObstacles, double obstacleX0) {
        this.wallRadius = wallRadius;
        this.radius = particleRadius;
        this.k = springConstant;
        this.hasObstacles = hasObstacles;
        this.obstacleX0 = obstacleX0;
        this.cellSize = 2 * particleRadius;
        this.cellsPerSide = (int) Math.ceil(2 * wallRadius / cellSize) + 2;
        this.head = new int[cellsPerSide * cellsPerSide];
        this.next = new int[n];
    }

    public static double wallOverlap(double x, double y, double wallRadius, double r) {
        double rho = Math.hypot(x, y);
        if (rho <= wallRadius - r) return 0;
        double nx = x / rho, ny = y / rho;
        double dx = (wallRadius + r) * nx - x, dy = (wallRadius + r) * ny - y;
        return 2 * r - Math.hypot(dx, dy);
    }

    public double compute(double[] x, double[] y, double[] fx, double[] fy, boolean[] touchedObstacle) {
        int n = x.length;
        Arrays.fill(fx, 0);
        Arrays.fill(fy, 0);
        Arrays.fill(touchedObstacle, false);
        double epot = 0;
        double contactDist = 2 * radius;
        double contactDist2 = contactDist * contactDist;

        Arrays.fill(head, -1);
        for (int i = 0; i < n; i++) {
            int c = cell(x[i], y[i]);
            next[i] = head[c];
            head[c] = i;
        }
        for (int i = 0; i < n; i++) {
            int cx = cellCoord(x[i]), cy = cellCoord(y[i]);
            for (int ox = Math.max(cx - 1, 0); ox <= Math.min(cx + 1, cellsPerSide - 1); ox++) {
                for (int oy = Math.max(cy - 1, 0); oy <= Math.min(cy + 1, cellsPerSide - 1); oy++) {
                    for (int j = head[ox * cellsPerSide + oy]; j >= 0; j = next[j]) {
                        if (j <= i) continue;
                        double dx = x[j] - x[i], dy = y[j] - y[i];
                        double d2 = dx * dx + dy * dy;
                        if (d2 >= contactDist2 || d2 == 0) continue;
                        double d = Math.sqrt(d2);
                        double xi = contactDist - d;
                        double fn = k * xi / d;
                        fx[i] -= fn * dx; fy[i] -= fn * dy;
                        fx[j] += fn * dx; fy[j] += fn * dy;
                        epot += 0.5 * k * xi * xi;
                    }
                }
            }
        }
        for (int i = 0; i < n; i++) {
            double rho = Math.hypot(x[i], y[i]);
            if (rho > wallRadius - radius) {
                double nx = x[i] / rho, ny = y[i] / rho;
                double dx = (wallRadius + radius) * nx - x[i];
                double dy = (wallRadius + radius) * ny - y[i];
                double d = Math.hypot(dx, dy);
                double xi = contactDist - d;
                if (xi > 0 && d > 0) {
                    double fn = k * xi / d;
                    fx[i] -= fn * dx; fy[i] -= fn * dy;
                    epot += 0.5 * k * xi * xi;
                }
            }
            if (hasObstacles) {
                for (int s = -1; s <= 1; s += 2) {
                    double dx = s * obstacleX0 - x[i], dy = -y[i];
                    double d2 = dx * dx + dy * dy;
                    if (d2 >= contactDist2 || d2 == 0) continue;
                    double d = Math.sqrt(d2);
                    double xi = contactDist - d;
                    double fn = k * xi / d;
                    fx[i] -= fn * dx; fy[i] -= fn * dy;
                    epot += 0.5 * k * xi * xi;
                    touchedObstacle[i] = true;
                }
            }
        }
        return epot;
    }

    private int cellCoord(double v) {
        int c = (int) ((v + wallRadius) / cellSize) + 1;
        return Math.min(Math.max(c, 0), cellsPerSide - 1);
    }

    private int cell(double px, double py) {
        return cellCoord(px) * cellsPerSide + cellCoord(py);
    }
}
