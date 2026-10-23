package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.billiard.BilliardSimulation;
import ar.edu.itba.sds.tp4.billiard.ForceField;
import ar.edu.itba.sds.tp4.billiard.InitialConditions;
import ar.edu.itba.sds.tp4.config.CircularBilliardConfig;
import ar.edu.itba.sds.tp4.config.ConfigLoader;
import ar.edu.itba.sds.tp4.config.DampedOscillatorConfig;
import ar.edu.itba.sds.tp4.oscillator.DampedOscillator;
import ar.edu.itba.sds.tp4.oscillator.OscillatorExperiment;
import ar.edu.itba.sds.tp4.output.BilliardOutputWriter;
import ar.edu.itba.sds.tp4.output.OscillatorOutputWriter;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Locale;
import java.util.Random;

public final class Main {
    public static void main(String[] args) throws IOException {
        if (args.length != 1) {
            System.err.println("Uso: java -jar sds_tp4_g8.jar <input/config/archivo.json>");
            System.exit(2);
        }
        var tree = ConfigLoader.readTree(Path.of(args[0]));
        String system = tree.path("system").asText("");
        switch (system) {
            case "damped_oscillator" -> runOscillator(ConfigLoader.loadOscillator(tree), Path.of(args[0]));
            case "circular_billiard" -> runBilliard(ConfigLoader.loadBilliard(tree), Path.of(args[0]));
            default -> throw new IllegalArgumentException("system desconocido: '" + system + "'");
        }
    }

    private static void saveConfigCopy(Path configFile, String outputDirectory) throws IOException {
        Path target = Path.of(outputDirectory).resolve("config.json");
        if (!configFile.toAbsolutePath().normalize().equals(target.toAbsolutePath().normalize())) {
            Files.copy(configFile, target, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private static void runOscillator(DampedOscillatorConfig cfg, Path configFile) throws IOException {
        var o = cfg.oscillator();
        var osc = new DampedOscillator(o.mass(), o.springConstant(), o.damping(), o.amplitude());
        try (var out = new OscillatorOutputWriter(cfg)) {
            saveConfigCopy(configFile, cfg.output().directory());
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

    private static void runBilliard(CircularBilliardConfig cfg, Path configFile) throws IOException {
        var p = cfg.particles();
        double dt = cfg.simulation().dt();
        int steps = TimeSteps.count(cfg.simulation().totalTime(), dt);
        boolean obstacles = cfg.obstacles().enabled();
        double x0 = cfg.obstacles().x0();
        var rnd = new Random(cfg.seed());
        var initial = "hexagonal".equals(cfg.initialCondition().mode())
                ? InitialConditions.hexagonal(p.count(), cfg.domain().radius(), p.radius(), p.initialSpeed(), obstacles, x0, rnd)
                : InitialConditions.random(p.count(), cfg.domain().radius(), p.radius(), p.initialSpeed(), obstacles, x0, rnd);
        var field = new ForceField(p.count(), cfg.domain().radius(), p.radius(), cfg.interaction().springConstant(), obstacles, x0);
        var sim = new BilliardSimulation(field, p.mass(), dt, steps, initial);
        try (var out = new BilliardOutputWriter(cfg)) {
            saveConfigCopy(configFile, cfg.output().directory());
            long start = System.nanoTime();
            var result = sim.run(out);
            double ms = (System.nanoTime() - start) / 1e6;
            out.writeSummary(result.steps(), ms);
            System.out.printf(Locale.ROOT, "N=%d steps=%d runtime=%.1f ms%n", p.count(), result.steps(), ms);
        }
    }
}
