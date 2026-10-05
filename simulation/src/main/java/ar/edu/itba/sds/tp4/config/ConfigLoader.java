package ar.edu.itba.sds.tp4.config;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.file.Path;

public final class ConfigLoader {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private ConfigLoader() {}

    public static JsonNode readTree(Path path) throws IOException {
        return MAPPER.readTree(path.toFile());
    }

    public static DampedOscillatorConfig loadOscillator(JsonNode tree) throws IOException {
        return MAPPER.treeToValue(tree, DampedOscillatorConfig.class);
    }
}
