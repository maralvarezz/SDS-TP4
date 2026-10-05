package ar.edu.itba.sds.tp4.integrator;

/** Esquema de integracion de paso fijo para una particula 1D (Sistema 1). */
public interface Integrator {
    String name();

    void init(double position0, double velocity0, double dt, AccelerationLaw law);

    /** Avanza exactamente un paso dt. */
    void step();

    /** Posicion en el instante alcanzado luego del ultimo step(). */
    double position();

    /**
     * Velocidad disponible tras el ultimo step(). Para Verlet original es la diferencia
     * central (r(t+dt) - r(t-dt)) / 2dt, es decir, corresponde al instante anterior.
     */
    double velocity();
}
