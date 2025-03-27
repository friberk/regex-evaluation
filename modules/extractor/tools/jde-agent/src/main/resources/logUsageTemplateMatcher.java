try{
UsageRecord usageRecord = new UsageRecord(
        parentPattern.pattern(),
        text.toString(),
        "${functionName}",
        ""
);
FileWriter fileWriter = new FileWriter("${logFilePath}", true);
BufferedWriter writer = new BufferedWriter(fileWriter);
PrintWriter pw = new java.io.PrintWriter(writer);
ObjectMapper mapper = new ObjectMapper();
String line = mapper.writeValueAsString(usageRecord);
pw.println(line);
pw.close();
} catch (Exception exe) {
    System.err.printf("Error while attempting to save usage record: %s%n", new Object[]{exe.getMessage()});
}