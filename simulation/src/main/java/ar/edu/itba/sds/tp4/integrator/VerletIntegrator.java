package ar.edu.itba.sds.tp4.integrator;

public final class VerletIntegrator implements Integrator {
    private static final int MAX_ITER = 100;
    private static final double REL_TOL = 1e-15;

    private AccelerationLaw law;
    private double dt, r, rPrev, v;

    @Override public String name() { return "verlet"; }

    @Override public void init(double r0, double v0, double dt, AccelerationLaw law) {
        this.law = law; this.dt = dt; this.r = r0; this.v = v0;
        double a0 = law.acceleration(r0, v0);
        this.rPrev = r0 - dt * v0 + 0.5 * dt * dt * a0;
    }

    @Override public void step() {
        double dt2 = dt * dt;
        double rNext = 2 * r - rPrev + dt2 * law.acceleration(r, (r - rPrev) / dt);
        for (int i = 0; i < MAX_ITER; i++) {
            double vCentral = (rNext - rPrev) / (2 * dt);
            double refined = 2 * r - rPrev + dt2 * law.acceleration(r, vCentral);
            boolean converged = Math.abs(refined - rNext) <= REL_TOL * (Math.abs(r) + Math.abs(rPrev) + Math.abs(refined));
            rNext = refined;
            if (converged) break;
        }
        v = (rNext - rPrev) / (2 * dt);
        rPrev = r;
        r = rNext;
    }

    @Override public double position() { return r; }
    @Override public double velocity() { return v; }
}
