package ar.edu.itba.sds.tp4.oscillator;

import ar.edu.itba.sds.tp4.integrator.Integrator;
import ar.edu.itba.sds.tp4.integrator.IntegratorFactory;

import java.util.function.BiConsumer;

public final class OscillatorExperiment {
    private OscillatorExperiment() {}

    /** Numero de pasos n = round(tf/dt); exige que n*dt coincida con tf. */
    public static int steps(double totalTime, double dt) {
        long n = Math.round(totalTime / dt);
        if (n < 1 || n > Integer.MAX_VALUE || Math.abs(n * dt - totalTime) > 1e-9 * totalTime) {
            throw new IllegalArgumentException("dt=" + dt + " no divide exactamente a tf=" + totalTime);
        }
        return (int) n;
    }

    /**
     * ECM(dt) = (1/n) sum_{i=1..n} (r_num(t_i) - r_analitica(t_i))^2, t_i = i dt.
     * El paso i=0 se excluye porque el error es nulo por construccion.
     * Si trajectory != null recibe (t_i, r_num_i) para i = 0..n.
     */
    public static double ecm(DampedOscillator osc, String integratorName, double dt, double totalTime,
                             BiConsumer<Double, double[]> trajectory) {
        int n = steps(totalTime, dt);
        Integrator integrator = IntegratorFactory.create(integratorName);
        integrator.init(osc.initialPosition(), osc.initialVelocity(), dt, osc.law());
        if (trajectory != null) trajectory.accept(0.0, new double[]{integrator.position(), osc.analyticPosition(0)});
        double sum = 0;
        for (int i = 1; i <= n; i++) {
            integrator.step();
            double t = i * dt;
            double analytic = osc.analyticPosition(t);
            double diff = integrator.position() - analytic;
            sum += diff * diff;
            if (trajectory != null) trajectory.accept(t, new double[]{integrator.position(), analytic});
        }
        return sum / n;
    }
}
