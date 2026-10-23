package ar.edu.itba.sds.tp4.integrator;

@FunctionalInterface
public interface AccelerationLaw {
    double acceleration(double position, double velocity);
}
