package ar.edu.itba.sds.tp4.config;

/** Configuracion del Sistema 2 (billar circular). Unidades SI. */
public record CircularBilliardConfig(String system, Long seed, String integrationMethod, Simulation simulation,
                                     Particles particles, Domain domain, Interaction interaction,
                                     Obstacles obstacles, InitialCondition initialCondition, Output output) {

    public record Simulation(double dt, double totalTime) {}

    public record Particles(int count, double radius, double mass, double initialSpeed) {}

    public record Domain(double radius) {}

    public record Interaction(double springConstant) {}

    /** x0: centros en (-x0, 0) y (+x0, 0); radio = radio de las particulas. */
    public record Obstacles(boolean enabled, double x0) {}

    /** mode: "random" (rechazo secuencial) o "hexagonal" (red hexagonal con subconjunto aleatorio). */
    public record InitialCondition(String mode) {}

    /**
     * stateEverySteps: escribir posiciones y velocidades cada n pasos (0 = no escribir).
     * El motor no calcula ni escribe observables (energia, F_u, etc.): eso es postproceso.
     * El primer contacto de cada particula siempre se registra (contacts.txt).
     */
    public record Output(String directory, boolean overwrite, int stateEverySteps) {}

    public CircularBilliardConfig {
        if (!"circular_billiard".equals(system)) throw new IllegalArgumentException("system debe ser 'circular_billiard'");
        if (seed == null) throw new IllegalArgumentException("seed es obligatoria (reproducibilidad)");
        if (!"verlet".equals(integrationMethod)) throw new IllegalArgumentException("integrationMethod debe ser 'verlet' (consigna)");
        if (simulation == null || particles == null || domain == null || interaction == null
                || obstacles == null || initialCondition == null || output == null) {
            throw new IllegalArgumentException("Faltan secciones en el JSON");
        }
        if (!(simulation.dt() > 0) || !(simulation.totalTime() > 0)) throw new IllegalArgumentException("dt y totalTime deben ser > 0");
        if (particles.count() < 1 || !(particles.radius() > 0) || !(particles.mass() > 0) || particles.initialSpeed() < 0) {
            throw new IllegalArgumentException("Parametros de particulas invalidos");
        }
        if (!(domain.radius() > 2 * particles.radius())) throw new IllegalArgumentException("domain.radius debe ser > 2r");
        if (!(interaction.springConstant() > 0)) throw new IllegalArgumentException("springConstant debe ser > 0");
        if (obstacles.enabled()) {
            double r = particles.radius(), R = domain.radius(), tol = 1e-12;
            if (obstacles.x0() < r - tol || obstacles.x0() > R - r + tol) {
                throw new IllegalArgumentException("obstacles.x0=" + obstacles.x0() + " fuera de [r, R-r]=[" + r + ", " + (R - r) + "]");
            }
        }
        if (!"random".equals(initialCondition.mode()) && !"hexagonal".equals(initialCondition.mode())) {
            throw new IllegalArgumentException("initialCondition.mode debe ser 'random' o 'hexagonal'");
        }
        if (output.directory() == null || output.directory().isBlank()) throw new IllegalArgumentException("output.directory vacio");
        if (output.stateEverySteps() < 0) throw new IllegalArgumentException("stateEverySteps debe ser >= 0");
    }
}
