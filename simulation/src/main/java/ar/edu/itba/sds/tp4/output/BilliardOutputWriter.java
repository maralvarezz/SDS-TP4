package ar.edu.itba.sds.tp4.output;

import ar.edu.itba.sds.tp4.billiard.BilliardObserver;
import ar.edu.itba.sds.tp4.config.CircularBilliardConfig;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * Archivos de salida (texto, separador espacio, decimales con punto, SI):
 *  metadata.txt  key=value con todos los parametros de la corrida.
 *  states.txt    "# t_s id x_m y_m vx_mps vy_mps used" (used: 0 fresca / 1 usada), cada stateEverySteps pasos.
 *  contacts.txt  "# id t_first_obstacle_contact_s", evento fresca->usada (una fila por particula usada).
 *  summary.txt   key=value (seed, N, steps, runtimeMilliseconds).
 */
public final class BilliardOutputWriter implements BilliardObserver, AutoCloseable {
    private final Path dir;
    private final CircularBilliardConfig cfg;
    private final int stateEvery;
    private BufferedWriter states, contacts;

    public BilliardOutputWriter(CircularBilliardConfig cfg) throws IOException {
        this.cfg = cfg;
        this.dir = Path.of(cfg.output().directory());
        if (Files.exists(dir.resolve("summary.txt")) && !cfg.output().overwrite()) {
            throw new IOException("Ya existe " + dir.resolve("summary.txt") + ". Usar otro output.directory o output.overwrite=true");
        }
        Files.createDirectories(dir);
        this.stateEvery = cfg.output().stateEverySteps();
        writeMetadata();
        contacts = Files.newBufferedWriter(dir.resolve("contacts.txt"));
        contacts.write("# id t_first_obstacle_contact_s\n");
        if (stateEvery > 0) {
            states = Files.newBufferedWriter(dir.resolve("states.txt"));
            states.write("# t_s id x_m y_m vx_mps vy_mps used\n");
        }
    }

    private void writeMetadata() throws IOException {
        var s = cfg.simulation();
        var p = cfg.particles();
        String text = String.format(Locale.ROOT,
                "system=circular_billiard%nseed=%d%nintegrationMethod=%s%ndt_s=%s%ntotalTime_s=%s%n"
                        + "N=%d%nparticleRadius_m=%s%nparticleMass_kg=%s%ninitialSpeed_mps=%s%n"
                        + "domainRadius_m=%s%nspringConstant_N_per_m=%s%nobstaclesEnabled=%b%nobstacleX0_m=%s%n"
                        + "initialConditionMode=%s%nstateEverySteps=%d%n",
                cfg.seed(), cfg.integrationMethod(), s.dt(), s.totalTime(), p.count(), p.radius(), p.mass(), p.initialSpeed(),
                cfg.domain().radius(), cfg.interaction().springConstant(), cfg.obstacles().enabled(), cfg.obstacles().x0(),
                cfg.initialCondition().mode(), stateEvery);
        Files.writeString(dir.resolve("metadata.txt"), text);
    }

    @Override
    public void onStep(int step, double time, double[] x, double[] y, double[] vx, double[] vy, boolean[] used) {
        try {
            if (stateEvery > 0 && step % stateEvery == 0) {
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < x.length; i++) {
                    sb.append(String.format(Locale.ROOT, "%.10e %d %.10e %.10e %.10e %.10e %d%n",
                            time, i, x[i], y[i], vx[i], vy[i], used[i] ? 1 : 0));
                }
                states.write(sb.toString());
            }
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    @Override
    public void onFirstContact(int id, double time) {
        try {
            contacts.write(String.format(Locale.ROOT, "%d %.10e%n", id, time));
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public void writeSummary(int steps, double runtimeMilliseconds) throws IOException {
        String text = String.format(Locale.ROOT, "seed=%d%nN=%d%nsteps=%d%nruntimeMilliseconds=%.3f%n"
                        + "runtimeScope=integration loop including enabled output writes; excludes initial condition generation%n",
                cfg.seed(), cfg.particles().count(), steps, runtimeMilliseconds);
        Files.writeString(dir.resolve("summary.txt"), text);
    }

    @Override
    public void close() throws IOException {
        contacts.close();
        if (states != null) states.close();
    }
}
