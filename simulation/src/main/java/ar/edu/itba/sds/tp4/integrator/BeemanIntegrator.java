package ar.edu.itba.sds.tp4.integrator;

/**
 * Beeman con fuerzas dependientes de la velocidad, variante predictor-corrector
 * (Teorica 4, diapositiva 20). a(t-dt) inicial por Euler evaluado en -dt.
 */
public final class BeemanIntegrator implements Integrator {
    private AccelerationLaw law;
    private double dt, r, v, aCur, aPrev;

    @Override public String name() { return "beeman"; }

    @Override public void init(double r0, double v0, double dt, AccelerationLaw law) {
        this.law = law; this.dt = dt; this.r = r0; this.v = v0;
        this.aCur = law.acceleration(r0, v0);
        double rBack = r0 - dt * v0 + 0.5 * dt * dt * aCur;
        double vBack = v0 - dt * aCur;
        this.aPrev = law.acceleration(rBack, vBack);
    }

    @Override public void step() {
        double dt2 = dt * dt;
        double rNew = r + v * dt + (2.0 / 3.0) * aCur * dt2 - (1.0 / 6.0) * aPrev * dt2;
        double vPred = v + 1.5 * aCur * dt - 0.5 * aPrev * dt;
        double aNew = law.acceleration(rNew, vPred);
        double vNew = v + (1.0 / 3.0) * aNew * dt + (5.0 / 6.0) * aCur * dt - (1.0 / 6.0) * aPrev * dt;
        aPrev = aCur; aCur = aNew;
        r = rNew; v = vNew;
    }

    @Override public double position() { return r; }
    @Override public double velocity() { return v; }
}
