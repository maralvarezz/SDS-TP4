package ar.edu.itba.sds.tp4.oscillator;

import ar.edu.itba.sds.tp4.integrator.Integrator;
import ar.edu.itba.sds.tp4.integrator.IntegratorFactory;

import java.util.function.BiConsumer;

public final class OscillatorExperiment {
    private OscillatorExperiment() {}

    public static int steps(double totalTime, double dt) {
        return ar.edu.itba.sds.tp4.TimeSteps.count(totalTime, dt);
    }

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
