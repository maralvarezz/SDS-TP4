package ar.edu.itba.sds.tp4.billiard;

public final class BilliardSimulation {
    private final ForceField field;
    private final double mass, dt;
    private final int steps;
    private final InitialConditions.State initial;

    public record Result(int steps) {}

    public BilliardSimulation(ForceField field, double mass, double dt, int steps, InitialConditions.State initial) {
        this.field = field; this.mass = mass; this.dt = dt; this.steps = steps; this.initial = initial;
    }

    public Result run(BilliardObserver observer) {
        int n = initial.x().length;
        double[] x = initial.x().clone(), y = initial.y().clone();
        double[] vx = initial.vx().clone(), vy = initial.vy().clone();
        double[] xPrev = new double[n], yPrev = new double[n], xNext = new double[n], yNext = new double[n];
        double[] fx = new double[n], fy = new double[n];
        boolean[] touched = new boolean[n], used = new boolean[n];
        double dt2OverM = dt * dt / mass;

        for (int step = 0; step <= steps; step++) {
            double t = step * dt;
            field.compute(x, y, fx, fy, touched);
            for (int i = 0; i < n; i++) {
                if (touched[i] && !used[i]) {
                    used[i] = true;
                    observer.onFirstContact(i, t);
                }
            }
            if (step == 0) {
                for (int i = 0; i < n; i++) {
                    xPrev[i] = x[i] - dt * vx[i] + 0.5 * dt2OverM * fx[i];
                    yPrev[i] = y[i] - dt * vy[i] + 0.5 * dt2OverM * fy[i];
                }
            }
            for (int i = 0; i < n; i++) {
                xNext[i] = 2 * x[i] - xPrev[i] + dt2OverM * fx[i];
                yNext[i] = 2 * y[i] - yPrev[i] + dt2OverM * fy[i];
                if (step > 0) {
                    vx[i] = (xNext[i] - xPrev[i]) / (2 * dt);
                    vy[i] = (yNext[i] - yPrev[i]) / (2 * dt);
                }
            }
            observer.onStep(step, t, x, y, vx, vy, used);
            double[] tmp = xPrev; xPrev = x; x = xNext; xNext = tmp;
            tmp = yPrev; yPrev = y; y = yNext; yNext = tmp;
        }
        return new Result(steps);
    }
}
