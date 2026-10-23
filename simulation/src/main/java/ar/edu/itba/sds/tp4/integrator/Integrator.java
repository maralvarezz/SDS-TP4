package ar.edu.itba.sds.tp4.integrator;

public interface Integrator {
    String name();

    void init(double position0, double velocity0, double dt, AccelerationLaw law);

    void step();

    double position();

    double velocity();
}
