package ar.edu.itba.sds.tp4.integrator;

/**
 * Velocity Verlet (Teorica 4, diapositiva 17). Con aceleracion dependiente de v,
 * a(t+dt) se resuelve por iteracion de punto fijo sobre v(t+dt).
 */
public final class VelocityVerletIntegrator implements Integrator {
    private static final int MAX_ITER = 100;
    private static final double REL_TOL = 1e-15;

    private AccelerationLaw law;
    private double dt, r, v, a;

    @Override public String name() { return "velocityVerlet"; }

    @Override public void init(double r0, double v0, double dt, AccelerationLaw law) {
        this.law = law; this.dt = dt; this.r = r0; this.v = v0;
        this.a = law.acceleration(r0, v0);
    }

    @Override public void step() {
        double rNew = r + dt * v + 0.5 * dt * dt * a;
        double vHalf = v + 0.5 * dt * a;
        double vNew = vHalf + 0.5 * dt * a;
        double aNew = law.acceleration(rNew, vNew);
        for (int i = 0; i < MAX_ITER; i++) {
            double refined = vHalf + 0.5 * dt * aNew;
            boolean converged = Math.abs(refined - vNew) <= REL_TOL * (Math.abs(v) + Math.abs(refined));
            vNew = refined;
            aNew = law.acceleration(rNew, vNew);
            if (converged) break;
        }
        r = rNew; v = vNew; a = aNew;
    }

    @Override public double position() { return r; }
    @Override public double velocity() { return v; }
}
