package ar.edu.itba.sds.tp4.billiard;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * Condiciones iniciales sin solapes (particula-particula, particula-obstaculo, particula-pared).
 * Velocidades: modulo v0 y angulo uniforme en [0, 2 pi).
 * "random": rechazo secuencial (se traba para fraccion de area > ~0.5).
 * "hexagonal": sitios de una red hexagonal con rotacion y desplazamiento aleatorios, se eligen N al azar;
 *              permite densidades altas (N > 600).
 */
public final class InitialConditions {
    private static final double EPS = 1e-9;
    private static final int MAX_ATTEMPTS_PER_PARTICLE = 200_000;

    public record State(double[] x, double[] y, double[] vx, double[] vy) {}

    private InitialConditions() {}

    public static State random(int n, double wallRadius, double r, double v0, boolean obstacles, double x0, Random rnd) {
        double rMax = wallRadius - r;
        double[] x = new double[n], y = new double[n];
        for (int i = 0; i < n; i++) {
            boolean placed = false;
            for (int attempt = 0; attempt < MAX_ATTEMPTS_PER_PARTICLE && !placed; attempt++) {
                double rho = rMax * Math.sqrt(rnd.nextDouble());
                double th = 2 * Math.PI * rnd.nextDouble();
                double px = rho * Math.cos(th), py = rho * Math.sin(th);
                if (free(px, py, i, x, y, r, obstacles, x0)) {
                    x[i] = px; y[i] = py; placed = true;
                }
            }
            if (!placed) {
                throw new IllegalStateException("No se pudo ubicar la particula " + i + " de " + n + " por rechazo tras "
                        + MAX_ATTEMPTS_PER_PARTICLE + " intentos. Usar initialCondition.mode=\"hexagonal\" para densidades altas.");
            }
        }
        return withVelocities(x, y, v0, rnd);
    }

    public static State hexagonal(int n, double wallRadius, double r, double v0, boolean obstacles, double x0, Random rnd) {
        double rMax = wallRadius - r - EPS;
        double theta = 2 * Math.PI * rnd.nextDouble();
        double u = rnd.nextDouble(), w = rnd.nextDouble();
        double minSpacing = 2 * r * (1 + 1e-4);
        List<double[]> sites = null;
        for (double s = wallRadius; s >= minSpacing; s *= 0.999) {
            List<double[]> candidate = lattice(s, theta, u, w, rMax, r, obstacles, x0);
            if (candidate.size() >= n) { sites = candidate; break; }
        }
        if (sites == null) {
            throw new IllegalStateException("N=" + n + " no entra en el dominio con red hexagonal (espaciado minimo 2r)");
        }
        Collections.shuffle(sites, rnd);
        double[] x = new double[n], y = new double[n];
        for (int i = 0; i < n; i++) { x[i] = sites.get(i)[0]; y[i] = sites.get(i)[1]; }
        return withVelocities(x, y, v0, rnd);
    }

    private static List<double[]> lattice(double s, double theta, double u, double w, double rMax, double r,
                                          boolean obstacles, double x0) {
        double a1x = Math.cos(theta), a1y = Math.sin(theta);
        double a2x = Math.cos(theta + Math.PI / 3), a2y = Math.sin(theta + Math.PI / 3);
        double ox = u * s * a1x + w * s * a2x, oy = u * s * a1y + w * s * a2y;
        int m = (int) Math.ceil(2 * rMax / (s * 0.8660254)) + 2;
        double minObs = 2 * r * (1 + 1e-9);
        List<double[]> out = new ArrayList<>();
        for (int i = -m; i <= m; i++) {
            for (int j = -m; j <= m; j++) {
                double px = ox + s * (i * a1x + j * a2x), py = oy + s * (i * a1y + j * a2y);
                if (Math.hypot(px, py) > rMax) continue;
                if (obstacles && (Math.hypot(px - x0, py) < minObs || Math.hypot(px + x0, py) < minObs)) continue;
                out.add(new double[]{px, py});
            }
        }
        return out;
    }

    private static boolean free(double px, double py, int placed, double[] x, double[] y, double r,
                                boolean obstacles, double x0) {
        double min = 2 * r, min2 = min * min;
        if (obstacles && (Math.hypot(px - x0, py) < min || Math.hypot(px + x0, py) < min)) return false;
        for (int j = 0; j < placed; j++) {
            double dx = px - x[j], dy = py - y[j];
            if (dx * dx + dy * dy < min2) return false;
        }
        return true;
    }

    private static State withVelocities(double[] x, double[] y, double v0, Random rnd) {
        int n = x.length;
        double[] vx = new double[n], vy = new double[n];
        for (int i = 0; i < n; i++) {
            double a = 2 * Math.PI * rnd.nextDouble();
            vx[i] = v0 * Math.cos(a);
            vy[i] = v0 * Math.sin(a);
        }
        return new State(x, y, vx, vy);
    }
}
