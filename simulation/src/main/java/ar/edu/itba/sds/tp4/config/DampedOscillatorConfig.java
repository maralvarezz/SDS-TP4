package ar.edu.itba.sds.tp4.config;

import java.util.List;

/** Configuracion del Sistema 1 (oscilador amortiguado). Unidades SI. */
public record DampedOscillatorConfig(String system, Oscillator oscillator, Sweep sweep, Output output) {

    public record Oscillator(double mass, double springConstant, double damping, double amplitude, double totalTime) {}

    /** trajectoryDts: subconjunto de dtValues para los que ademas se escribe la trayectoria. */
    public record Sweep(List<String> integrators, List<Double> dtValues, List<Double> trajectoryDts) {
        public Sweep {
            trajectoryDts = trajectoryDts == null ? List.of() : trajectoryDts;
        }
    }

    public record Output(String directory, boolean overwrite) {}

    public DampedOscillatorConfig {
        if (!"damped_oscillator".equals(system)) throw new IllegalArgumentException("system debe ser 'damped_oscillator'");
        if (oscillator == null || sweep == null || output == null) throw new IllegalArgumentException("Faltan secciones en el JSON");
        if (oscillator.totalTime() <= 0) throw new IllegalArgumentException("totalTime debe ser > 0");
        if (sweep.integrators() == null || sweep.integrators().isEmpty()) throw new IllegalArgumentException("sweep.integrators vacio");
        if (sweep.dtValues() == null || sweep.dtValues().isEmpty()) throw new IllegalArgumentException("sweep.dtValues vacio");
        for (double dt : sweep.dtValues()) {
            if (!(dt > 0)) throw new IllegalArgumentException("dt debe ser > 0: " + dt);
        }
        for (double dt : sweep.trajectoryDts()) {
            if (!sweep.dtValues().contains(dt)) throw new IllegalArgumentException("trajectoryDts debe estar incluido en dtValues: " + dt);
        }
        if (output.directory() == null || output.directory().isBlank()) throw new IllegalArgumentException("output.directory vacio");
    }
}
