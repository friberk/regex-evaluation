package parsers.java;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.javaparser.symbolsolver.javaparsermodel.JavaParserFacade;

import java.io.*;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;

public class ParserConnectionHandler implements Runnable {

    private final Socket connection;
    private final ObjectMapper mapper;

    public ParserConnectionHandler(Socket connection, ObjectMapper mapper) {
        this.connection = connection;
        this.mapper = mapper;
    }

    @Override
    public void run() {
        try {
            RegexExtractorManager regexExtractorManager = new RegexExtractorManager(new JavaParserFactory());
            BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
            BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter(connection.getOutputStream()));

            while (connection.isConnected() && !connection.isClosed()) {
                System.out.println("Reading next line...");
                String nextLine = bufferedReader.readLine();
                if (nextLine == null || nextLine.isBlank()) {
                    System.out.println("Blank line sent. Closing connection...");
                    break;
                }

                System.out.printf("Parsing path: '%s'%n", nextLine);

                String sourceFilePath = nextLine.trim();

                File inputFile = new File(sourceFilePath);

                List<RegexObject> parsedObjects;
                try {
                    parsedObjects = regexExtractorManager.parseRegexObjects(inputFile);
                } catch (StackOverflowError stackOverflowError) {
                    System.out.printf("StackOverflow encountered while parsing file, skipping: %s%n", stackOverflowError.getMessage());
                    parsedObjects = new ArrayList<>();
                }

                System.out.printf("Got %d results%n", parsedObjects.size());

                parsedObjects.forEach(item -> item.setSourceFile(sourceFilePath));
                String stringified = mapper.writeValueAsString(parsedObjects);
                bufferedWriter.write(stringified);
                bufferedWriter.write("\r\n");
            }

            bufferedWriter.write("\r\n");
            bufferedWriter.flush();

            bufferedReader.close();
            bufferedWriter.close();
            this.connection.close();
        } catch (IOException exe) {
            // TODO
            throw new RuntimeException(exe);
        }
    }
}
