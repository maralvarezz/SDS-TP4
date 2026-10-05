package ar.edu.itba.sds.tp4.oscillator;

import ar.edu.itba.sds.tp4.integrator.AccelerationLaw;

/**
 * Oscilador amortiguado m r'' = -k r - gamma r' (Teorica 4, diapositiva 37).
 * Condiciones iniciales: r(0) = A, v(0) = -A gamma / (2m). Unidades SI.
 */
public record DampedOscillator(double mass, double springConstant, double damping, double amplitude) {

    public DampedOscillator {
        if (mass <= 0 || springConstant <= 0 || damping < 0 || amplitude == 0) {
            throw new IllegalArgumentException("Parametros invalidos del oscilador");
        }
        if (springConstant / mass - damping * damping / (4 * mass * mass) <= 0) {
            throw new IllegalArgumentException("El oscilador debe ser subamortiguado (k/m > gamma^2/4m^2)");
        }
    }

    public double initialPosition() { return amplitude; }

    public double initialVelocity() { return -amplitude * damping / (2 * mass); }

    public AccelerationLaw law() {
        return (r, v) -> (-springConstant * r - damping * v) / mass;
    }

    public double analyticPosition(double t) {
        double omega = Math.sqrt(springConstant / mass - damping * damping / (4 * mass * mass));
        return amplitude * Math.exp(-damping / (2 * mass) * t) * Math.cos(omega * t);
    }
}
