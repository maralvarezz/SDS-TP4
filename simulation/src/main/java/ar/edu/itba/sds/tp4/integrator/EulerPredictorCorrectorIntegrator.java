package ar.edu.itba.sds.tp4.integrator;

public final class EulerPredictorCorrectorIntegrator implements Integrator {
    private AccelerationLaw law;
    private double dt, r, v;

    @Override public String name() { return "eulerPC"; }

    @Override public void init(double r0, double v0, double dt, AccelerationLaw law) {
        this.law = law; this.dt = dt; this.r = r0; this.v = v0;
    }

    @Override public void step() {
        double a = law.acceleration(r, v);
        double vPred = v + a * dt;
        double rPred = r + v * dt;
        double aNext = law.acceleration(rPred, vPred);
        double vNew = v + aNext * dt;
        double rNew = r + vNew * dt;
        v = vNew; r = rNew;
    }

    @Override public double position() { return r; }
    @Override public double velocity() { return v; }
}
