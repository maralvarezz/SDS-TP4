package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.config.ConfigLoader;
import ar.edu.itba.sds.tp4.config.DampedOscillatorConfig;
import ar.edu.itba.sds.tp4.oscillator.DampedOscillator;
import ar.edu.itba.sds.tp4.oscillator.OscillatorExperiment;
import ar.edu.itba.sds.tp4.output.OscillatorOutputWriter;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.Locale;

/** Uso: java -jar sds_tp4_g8.jar <config.json>. El campo "system" elige el sistema a simular. */
public final class Main {
    public static void main(String[] args) throws IOException {
        if (args.length != 1) {
            System.err.println("Uso: java -jar sds_tp4_g8.jar <input/config/archivo.json>");
            System.exit(2);
        }
        var tree = ConfigLoader.readTree(Path.of(args[0]));
        String system = tree.path("system").asText("");
        switch (system) {
            case "damped_oscillator" -> runOscillator(ConfigLoader.loadOscillator(tree));
            default -> throw new IllegalArgumentException("system desconocido: '" + system + "'");
        }
    }

    private static void runOscillator(DampedOscillatorConfig cfg) throws IOException {
        var o = cfg.oscillator();
        var osc = new DampedOscillator(o.mass(), o.springConstant(), o.damping(), o.amplitude());
        try (var out = new OscillatorOutputWriter(cfg)) {
            for (String method : cfg.sweep().integrators()) {
                for (double dt : cfg.sweep().dtValues()) {
                    int steps = OscillatorExperiment.steps(o.totalTime(), dt);
                    double ecm;
                    if (cfg.sweep().trajectoryDts().contains(dt)) {
                        try (BufferedWriter w = out.openTrajectory(method, dt)) {
                            ecm = OscillatorExperiment.ecm(osc, method, dt, o.totalTime(), (t, r) -> {
                                try {
                                    w.write(String.format(Locale.ROOT, "%.12e %.17e %.17e%n", t, r[0], r[1]));
                                } catch (IOException e) { throw new UncheckedIOException(e); }
                            });
                        }
                    } else {
                        ecm = OscillatorExperiment.ecm(osc, method, dt, o.totalTime(), null);
                    }
                    out.writeEcm(method, dt, steps, ecm);
                    System.out.printf(Locale.ROOT, "%s dt=%.3e ECM=%.6e%n", method, dt, ecm);
                }
            }
        }
    }
}
