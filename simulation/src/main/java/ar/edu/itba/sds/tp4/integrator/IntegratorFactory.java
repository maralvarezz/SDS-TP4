package ar.edu.itba.sds.tp4.integrator;

import java.util.List;

public final class IntegratorFactory {
    public static final List<String> NAMES = List.of("beeman", "verlet", "velocityVerlet", "eulerPC");

    private IntegratorFactory() {}

    public static Integrator create(String name) {
        return switch (name) {
            case "beeman" -> new BeemanIntegrator();
            case "verlet" -> new VerletIntegrator();
            case "velocityVerlet" -> new VelocityVerletIntegrator();
            case "eulerPC" -> new EulerPredictorCorrectorIntegrator();
            default -> throw new IllegalArgumentException("Integrador desconocido: '" + name + "'. Validos: " + NAMES);
        };
    }
}
