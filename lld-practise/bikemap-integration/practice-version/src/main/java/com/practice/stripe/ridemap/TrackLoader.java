package com.practice.stripe.ridemap;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/** Reads the recorded ride used by the command line application. */
public class TrackLoader {
    private final ObjectMapper mapper;

    public TrackLoader(ObjectMapper mapper) {
        this.mapper = mapper;
    }

    public List<GeoPoint> load(Path path) throws IOException {
        var ride = mapper.readTree(path.toFile());
        var coordinates = ride.get("geometry").get("coordinates");
        var points = new ArrayList<GeoPoint>();
        for (var coordinate : coordinates) {
            points.add(new GeoPoint(coordinate.get(0).asDouble(), coordinate.get(1).asDouble()));
        }
        return points;
    }
}
