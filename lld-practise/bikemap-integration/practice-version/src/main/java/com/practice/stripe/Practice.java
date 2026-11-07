package com.practice.stripe;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.practice.stripe.ridemap.Config;
import com.practice.stripe.ridemap.TrackLoader;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Path;

/** Plain Java entry point. Run with: mvn compile exec:java -Dexec.args="part1". */
public class Practice {
    public static void main(String[] args) throws IOException {
        System.exit(run(args, System.out, System.err));
    }

    public static int run(String[] args, PrintStream out, PrintStream err) throws IOException {
        if (args.length == 0 || args[0].equals("--help")) {
            out.println("Usage: part1 [path]");
            return 0;
        }
        if (!args[0].equals("part1") || args.length > 2) {
            err.println("Usage: part1 [path]");
            return 2;
        }
        var path = args.length == 2 ? Path.of(args[1]) : Config.fromEnvironment().defaultTrack();
        var points = new TrackLoader(new ObjectMapper()).load(path);
        points.stream().limit(10).forEach(out::println);
        return 0;
    }
}
