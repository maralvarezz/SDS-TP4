package ar.edu.itba.sds.tp4.output;

import ar.edu.itba.sds.tp4.config.DampedOscillatorConfig;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * Escribe: metadata.txt, ecm.txt (method dt_s steps ecm_m2) y trajectory_<metodo>_dt<dt>.txt
 * (t_s r_numeric_m r_analytic_m). Separador: espacio. Decimales con punto.
 */
public final class OscillatorOutputWriter implements AutoCloseable {
    private final Path dir;
    private final BufferedWriter ecm;

    public OscillatorOutputWriter(DampedOscillatorConfig cfg) throws IOException {
        this.dir = Path.of(cfg.output().directory());
        Path ecmFile = dir.resolve("ecm.txt");
        if (Files.exists(ecmFile) && !cfg.output().overwrite()) {
            throw new IOException("Ya existe " + ecmFile + ". Usar otro output.directory o output.overwrite=true");
        }
        Files.createDirectories(dir);
        writeMetadata(cfg);
        this.ecm = Files.newBufferedWriter(ecmFile);
        ecm.write("# method dt_s steps ecm_m2\n");
    }

    private void writeMetadata(DampedOscillatorConfig cfg) throws IOException {
        var o = cfg.oscillator();
        String text = String.format(Locale.ROOT,
                "system=damped_oscillator%nmass_kg=%s%nspringConstant_N_per_m=%s%ndamping_kg_per_s=%s%namplitude_m=%s%ntotalTime_s=%s%n"
                        + "integrators=%s%ndtValues_s=%s%ntrajectoryDts_s=%s%n"
                        + "ecmDefinition=(1/n)*sum_{i=1..n}(r_num(t_i)-r_analytic(t_i))^2, t_i=i*dt, n=totalTime/dt%n",
                o.mass(), o.springConstant(), o.damping(), o.amplitude(), o.totalTime(),
                cfg.sweep().integrators(), cfg.sweep().dtValues(), cfg.sweep().trajectoryDts());
        Files.writeString(dir.resolve("metadata.txt"), text);
    }

    public void writeEcm(String method, double dt, int steps, double ecmValue) throws IOException {
        ecm.write(String.format(Locale.ROOT, "%s %.12e %d %.17e%n", method, dt, steps, ecmValue));
    }

    public BufferedWriter openTrajectory(String method, double dt) throws IOException {
        BufferedWriter w = Files.newBufferedWriter(dir.resolve(String.format(Locale.ROOT, "trajectory_%s_dt%.6e.txt", method, dt)));
        w.write("# t_s r_numeric_m r_analytic_m\n");
        return w;
    }

    @Override public void close() throws IOException { ecm.close(); }
}
