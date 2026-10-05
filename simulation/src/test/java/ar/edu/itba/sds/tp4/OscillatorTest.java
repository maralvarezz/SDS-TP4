package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.config.ConfigLoader;
import ar.edu.itba.sds.tp4.integrator.IntegratorFactory;
import ar.edu.itba.sds.tp4.oscillator.DampedOscillator;
import ar.edu.itba.sds.tp4.oscillator.OscillatorExperiment;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

class OscillatorTest {
    private final DampedOscillator osc = new DampedOscillator(70, 1e4, 100, 1);

    @Test
    void analyticSolutionMatchesInitialConditions() {
        assertEquals(1.0, osc.analyticPosition(0), 1e-15);
        double h = 1e-7;
        double v0 = (osc.analyticPosition(h) - osc.analyticPosition(-h)) / (2 * h);
        assertEquals(osc.initialVelocity(), v0, 1e-6);
    }

    @Test
    void allIntegratorsConvergeToAnalyticSolution() {
        for (String name : IntegratorFactory.NAMES) {
            double coarse = OscillatorExperiment.ecm(osc, name, 1e-3, 5.0, null);
            double fine = OscillatorExperiment.ecm(osc, name, 5e-4, 5.0, null);
            assertTrue(fine < coarse / 1.8, name + ": ECM no decrece al reducir dt (" + coarse + " -> " + fine + ")");
            assertTrue(fine < 1e-3, name + ": ECM demasiado grande: " + fine);
        }
    }

    @Test
    void secondOrderSchemesBeatEulerPredictorCorrector() {
        double euler = OscillatorExperiment.ecm(osc, "eulerPC", 1e-3, 5.0, null);
        for (String name : new String[]{"beeman", "verlet", "velocityVerlet"}) {
            assertTrue(OscillatorExperiment.ecm(osc, name, 1e-3, 5.0, null) < euler, name);
        }
    }

    @Test
    void stepCountMustDivideTotalTime() {
        assertEquals(5000, OscillatorExperiment.steps(5.0, 1e-3));
        assertThrows(IllegalArgumentException.class, () -> OscillatorExperiment.steps(5.0, 0.3));
    }

    @Test
    void unknownIntegratorFails() {
        assertThrows(IllegalArgumentException.class, () -> IntegratorFactory.create("rk4"));
    }

    @Test
    void sampleConfigParses() throws Exception {
        var tree = ConfigLoader.readTree(Path.of("../input/config/system1_damped_oscillator.json"));
        var cfg = ConfigLoader.loadOscillator(tree);
        assertEquals(4, cfg.sweep().integrators().size());
        assertTrue(cfg.sweep().dtValues().stream().allMatch(dt -> dt < 1e-2));
    }
}
