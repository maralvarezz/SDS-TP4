package ar.edu.itba.sds.tp4.billiard;

public interface BilliardObserver {
    void onStep(int step, double time, double[] x, double[] y, double[] vx, double[] vy, boolean[] used);

    void onFirstContact(int id, double time);
}
