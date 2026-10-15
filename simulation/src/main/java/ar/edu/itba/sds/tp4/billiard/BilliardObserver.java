package ar.edu.itba.sds.tp4.billiard;

/** Recibe el estado del billar. Todos los arreglos son de solo lectura y validos solo durante la llamada. */
public interface BilliardObserver {
    /** Estado en t = step * dt: r_n, v_n (Verlet: diferencia central), used[i] ya actualizado. */
    void onStep(int step, double time, double[] x, double[] y, double[] vx, double[] vy, boolean[] used);

    /** Primer contacto fresca -> usada de la particula id, ocurre una sola vez por particula. */
    void onFirstContact(int id, double time);
}
