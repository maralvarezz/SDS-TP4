package ar.edu.itba.sds.tp4;

public final class TimeSteps {
    private TimeSteps() {}

    public static int count(double totalTime, double dt) {
        long n = Math.round(totalTime / dt);
        if (n < 1 || n > Integer.MAX_VALUE || Math.abs(n * dt - totalTime) > 1e-9 * totalTime) {
            throw new IllegalArgumentException("dt=" + dt + " no divide exactamente a tf=" + totalTime);
        }
        return (int) n;
    }
}
