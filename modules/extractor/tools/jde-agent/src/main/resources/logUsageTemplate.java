try {
    java.io.FileWriter fileWriter = new java.io.FileWriter("${logFilePath}", true);
    java.io.BufferedWriter writer = new java.io.BufferedWriter(fileWriter);
    java.io.PrintWriter pw = new java.io.PrintWriter(writer);
    pw.printf("{\"pattern\": \"%s\", \"subject\": \"%s\", \"func\": \"\", \"stack\": \"\"}%n", new Object[]{ outputFormat, ${r"$1"}.toString() });
    pw.close();
} catch (java.io.IOException exe) {
    exe.printStackTrace();
}