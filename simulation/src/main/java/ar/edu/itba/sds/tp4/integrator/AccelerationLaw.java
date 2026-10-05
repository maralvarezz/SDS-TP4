package ar.edu.itba.sds.tp4.integrator;

/** Aceleracion de una particula 1D en funcion de su estado: a(r, v). Unidades SI. */
@FunctionalInterface
public interface AccelerationLaw {
    double acceleration(double position, double velocity);
}
