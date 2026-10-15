package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.billiard.BilliardObserver;
import ar.edu.itba.sds.tp4.billiard.BilliardSimulation;
import ar.edu.itba.sds.tp4.billiard.ForceField;
import ar.edu.itba.sds.tp4.billiard.InitialConditions;
import ar.edu.itba.sds.tp4.config.ConfigLoader;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.*;

class BilliardTest {
    private static final double R = 0.51, r = 0.0175, m = 0.025, k = 1e4;

    private static double minGap(InitialConditions.State s, boolean obstacles, double x0) {
        int n = s.x().length;
        double min = Double.MAX_VALUE;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                min = Math.min(min, Math.hypot(s.x()[i] - s.x()[j], s.y()[i] - s.y()[j]) - 2 * r);
            }
            min = Math.min(min, R - r - Math.hypot(s.x()[i], s.y()[i]));
            if (obstacles) {
                min = Math.min(min, Math.hypot(s.x()[i] - x0, s.y()[i]) - 2 * r);
                min = Math.min(min, Math.hypot(s.x()[i] + x0, s.y()[i]) - 2 * r);
            }
        }
        return min;
    }

    @Test
    void initialConditionsDoNotOverlap() {
        var random = InitialConditions.random(300, R, r, 1.0, false, 0, new Random(1));
        assertTrue(minGap(random, false, 0) >= 0);
        var hex = InitialConditions.hexagonal(700, R, r, 1.0, true, r, new Random(2));
        assertTrue(minGap(hex, true, r) >= 0);
        for (int i = 0; i < 700; i++) assertEquals(1.0, Math.hypot(hex.vx()[i], hex.vy()[i]), 1e-12);
    }

    @Test
    void impossibleDensityFailsExplicitly() {
        assertThrows(IllegalStateException.class, () -> InitialConditions.hexagonal(900, R, r, 1.0, false, 0, new Random(3)));
    }

    @Test
    void pairForceIsSymmetricAndNormal() {
        var ff = new ForceField(2, R, r, k, false, 0);
        double[] fx = new double[2], fy = new double[2];
        double epot = ff.compute(new double[]{0, 0.03}, new double[]{0, 0}, fx, fy, new boolean[2]);
        double xi = 2 * r - 0.03;
        assertEquals(-fx[0], fx[1], 1e-12);
        assertEquals(k * xi, fx[1], 1e-9);
        assertEquals(0, fy[0], 1e-12);
        assertEquals(0.5 * k * xi * xi, epot, 1e-12);
    }

    @Test
    void wallImageForceIsRadialInward() {
        var ff = new ForceField(1, R, r, k, false, 0);
        double rho = R - r + 0.002;
        double[] fx = new double[1], fy = new double[1];
        double epot = ff.compute(new double[]{rho / Math.sqrt(2)}, new double[]{rho / Math.sqrt(2)}, fx, fy, new boolean[1]);
        assertEquals(k * 0.002, Math.hypot(fx[0], fy[0]), 1e-9);
        assertEquals(fx[0], fy[0], 1e-9);
        assertTrue(fx[0] < 0);
        assertEquals(0.5 * k * 0.002 * 0.002, epot, 1e-12);
        assertEquals(0.002, ForceField.wallOverlap(rho, 0, R, r), 1e-12);
    }

    @Test
    void obstacleContactIsFlaggedAndNoContactIsNot() {
        var ff = new ForceField(1, R, r, k, true, 0.1);
        double[] fx = new double[1], fy = new double[1];
        boolean[] touched = new boolean[1];
        ff.compute(new double[]{0.13}, new double[]{0}, fx, fy, touched);
        assertTrue(touched[0]);
        assertTrue(fx[0] > 0);
        ff.compute(new double[]{0.14}, new double[]{0}, fx, fy, touched);
        assertFalse(touched[0]);
    }

    private static final class Probe implements BilliardObserver {
        final int[] contacts;
        double e0 = Double.NaN, maxDeviation = 0, checksum = 0;
        final int n;
        final ForceField field;

        Probe(int n, ForceField field) { this.n = n; this.field = field; contacts = new int[n]; }

        @Override public void onStep(int step, double t, double[] x, double[] y, double[] vx, double[] vy, boolean[] used) {
            double epot = field.compute(x, y, new double[n], new double[n], new boolean[n]);
            double ek = 0;
            for (int i = 0; i < n; i++) ek += vx[i] * vx[i] + vy[i] * vy[i];
            double e = 0.5 * m * ek + epot;
            if (Double.isNaN(e0)) e0 = e; else maxDeviation = Math.max(maxDeviation, Math.abs(e - e0) / e0);
            checksum = 0;
            for (int i = 0; i < n; i++) checksum += x[i] * (i + 1) + y[i];
        }

        @Override public void onFirstContact(int id, double t) { contacts[id]++; }
    }

    private static Probe run(int n, boolean obstacles, double x0, long seed, double dt, double tf) {
        var initial = InitialConditions.random(n, R, r, 1.0, obstacles, x0, new Random(seed));
        var field = new ForceField(n, R, r, k, obstacles, x0);
        var probe = new Probe(n, field);
        new BilliardSimulation(field, m, dt, TimeSteps.count(tf, dt), initial).run(probe);
        return probe;
    }

    @Test
    void energyIsApproximatelyConservedWithoutObstacles() {
        assertTrue(run(100, false, 0, 11, 1e-4, 2.0).maxDeviation < 1e-2);
    }

    @Test
    void freshToUsedHappensOnlyOncePerParticle() {
        var probe = run(100, true, r, 21, 1e-4, 10.0);
        int total = 0;
        for (int c : probe.contacts) { assertTrue(c <= 1); total += c; }
        assertTrue(total > 0);
    }

    @Test
    void sameSeedGivesSameResult() {
        assertEquals(run(50, true, 0.2, 5, 1e-4, 1.0).checksum, run(50, true, 0.2, 5, 1e-4, 1.0).checksum);
        assertNotEquals(run(50, true, 0.2, 5, 1e-4, 1.0).checksum, run(50, true, 0.2, 6, 1e-4, 1.0).checksum);
    }

    @Test
    void sampleConfigsParse() throws Exception {
        for (String f : new String[]{"config_sys2_exp1a.json", "config_sys2_exp2.json", "config_sys2_animation.json"}) {
            var cfg = ConfigLoader.loadBilliard(ConfigLoader.readTree(Path.of("../input/config/" + f)));
            assertEquals("verlet", cfg.integrationMethod());
        }
    }
}
