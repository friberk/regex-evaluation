package parsers.java;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.module.SimpleModule;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketAddress;

public class Extractor {
    public static void main(String[] args) throws IOException {

        if (args.length < 2) {
            System.err.println("Usage: java-extractor <listening_port> <thread_count>");
            System.exit(1);
        }

        int listeningPort = Integer.parseInt(args[0]);

        // set up an object mapper

        SimpleModule mod = new SimpleModule();
        mod.addSerializer(RegexObject.class, new RegexObjectSerializer(RegexObject.class));

        // setup the unix server
        try (ServerSocket server = new ServerSocket()) {
            SocketAddress address = new InetSocketAddress(listeningPort);
            server.bind(address);
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                try {
                    server.close();
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            }));

            ObjectMapper objectMapper = new ObjectMapper();
            objectMapper.registerModule(mod);

            System.out.println("Listening for connections...");
            while (server.isBound()) {
                Socket connection = server.accept();
                // Give each connection its own object mapper
                System.out.println("Got a connection!");
                new ParserConnectionHandler(connection, objectMapper).run();
            }
        }
    }
}
