package dk.brics.automaton;

import static dk.brics.automaton.GenerateStrings.eSimilarity;
import static dk.brics.automaton.GenerateStrings.generateStrings;

public class GenStrTest {

    private static final GenerateStrings.GenerateStringsConfiguration defaultPositiveConfig = new GenerateStrings.GenerateStringsConfiguration(true, 2, 0);

    public static void notMain(String[] args) {
        dbSample();
        metricSample();
        testSuite();
    }


    private static void testSuite() {
        String simpleLoop = "(abc)+";
        generateStrings(simpleLoop, defaultPositiveConfig);

        String middleLoop = "abc(def)+ghi";
        generateStrings(middleLoop, defaultPositiveConfig);

        String versionId = "^v?([0-9]+\\.[0-9]+\\.[0-9]+)";
        generateStrings(versionId, defaultPositiveConfig);
    }

    private static void metricSample() {
        analysisTest("^v?([0-9]+\\.[0-9]+\\.[0-9]+)", "^[a-zA-Z0-9+-.]+$");
        System.out.println("\n");
        analysisTest("^[0-9]+\\.[0-9]+$", "^-?[0-9.,]+$");
        System.out.println("\n");
        analysisTest("^uint([0-9]+)$", "^(u?int)([0-9]+)$");
        System.out.println("\n");
    }

    private static void analysisTest(String truthRegex, String reuseCandidate) {
        double result = eSimilarity(truthRegex, reuseCandidate, defaultPositiveConfig);
        System.out.println(result);
        double invResult = eSimilarity(reuseCandidate, truthRegex, defaultPositiveConfig);
        System.out.println(invResult);
    }

    private static void dbSample()  {

        int MAX_DEPTH = 2;

        String regex1 = "^[0-9]+$";
        String regex2 = "\\r?\\n";
        String regex3 = "[A-Z]";
        String regex4 = "^\\/\\/\n";
        String regex5 = "^[0-9]+$";
        String regex6 = "\\s{2,}";
        String regex7 = "\\.(html)$";
        String regex8 = "\\.(jpe?g|png|gif|svg)$";
        String regex9 = "\\.css$";
        String regex10 = "\\.ts$";
        String regex11 = "^(file|folder)$";
        String regex12 = "[/\\\\]";
        String regex13 = "[A-Z]";
        String regex14 = "^text\\/";
        String regex15 = "^\\d+\\.\\d+\\.\\d+$";
        String regex16 = "\\r?\\n";
        String regex17 = "^operations\\/[-A-Za-z0-9]+$";
        String regex18 = "^operations\\/([-A-Za-z0-9]+)$";
        String regex19 = "^projects\\/([\\-\\w]+)\\/locations\\/([\\-\\w]+)\\/functions\\/([A-Za-z][\\-A-Za-z0-9_]*)$";
        String regex20 = "^[A-Za-z][\\-A-Za-z0-9_]*$";
        String regex21 = "firebase\\.database";
        String regex22 = "\\s\\s*$";
        String regex23 = "^\\[([^\\]]+)\\]\\s*(?:#.*)?$|^([a-z_]+)\\s*=\\s*(.+?)\\s*(?:#.*)?$";
        String regex24 = "^[ ]+$";
        String regex25 = "application\\/x-amz-json";
        String regex26 = "(application|text)\\/xml";
        String regex27 = "\\r?\\n";
        String regex28 = "\\r\\n?";
        String regex29 = "[\\s,]+";
        String regex30 = "^Lorem,?\\sipsum,?\\sdolor";
        String regex31 = "moduleId=(\\w+)";
        String regex32 = "moduleId=(?!none)(\\w+)";
        String regex33 = "^[.\\d]+";
        String regex34 = "^(?:-o|--output)$";
        String regex35 = "^(?:-m|--source-map)$";
        String regex36 = "\\bfunction\\b|\\b[a-z]+(?:[A-Z][a-z]+)+\\(|\\broot\\.(?:[A-Z][a-z0-9]+)+\\b";
        String regex37 = "([A-Za-z0-9\\u00C0-\\u00FF])";
        String regex38 = "([ :–—-])";
        String regex39 = "[A-Z]|\\..";
        String regex40 = "^\\/([^\\/^~]+)$";
        String regex41 = "^fields\\/[^\\/^~]+\\/~locale$";
        String regex42 = "(<|>)(\\d{1,})(px|cm|mm|in|pt|pc)$";
        String regex43 = "^[a-zA-Z0-9-_]{1,32}$";
        String regex44 = "^[a-zA-Z0-9-_]{1,21}$";
        String regex45 = "^[a-zA-Z0-9-_]{1,54}$";
        String regex46 = "^\\*$|^<[0-9*]+px$";
        String regex47 = "px|<|>";
        String regex48 = "[A-Z]";
        String regex49 = "^\\d+\\.?\\d*$";
        String regex50 = "[:.]$";
        String regex51 = "^[0-9]+$";
        String regex52 = "^[?#]";
        String regex53 = "(\\/?:[^\\/]+)?";
        String regex54 = "^(\\/:[^\\/]+)?";
        String regex55 = "^.*?#";
        String regex56 = "\\.(bpmn|xml|css)$";
        String regex57 = "\\r?\\n";
        String regex58 = "^\\/\\/";
        String regex59 = "(localhost|127\\.0\\.0\\.1):\\d+";
        String regex60 = "Bearer .*";
        String regex61 = "^\\s*$";
        String regex62 = "[A-Z]";
        String regex63 = "options must be constructed with changing\\.options function";
        String regex64 = "invalid date(time array)?";
        String regex65 = "invalid date.*begining";
        String regex66 = "\\\\x2d";
        String regex67 = "read\\.only";
        String regex68 = "not extensible|non-writable";
        String regex69 = "Cannot delete|non-configurable";
        String regex70 = "Expect.+a string";
        String regex71 = "^[_a-z][_a-z0-9]*$";
        String regex72 = "\\r?\\n";
        String regex73 = "^\\/\\/";
        String regex74 = "\\r?\\n";
        String regex75 = "^\\s*#";
        String regex76 = "[\\s,]+";
        String regex77 = "^[0-9]+$";
        String regex78 = "\\r?\\n";
        String regex79 = "\\r\\n?";
        String regex80 = "^TypeError.*, but got a non-string value undefined\\.";
        String regex81 = "^TypeError.*Expected a file path to write a file, but got a non-string value \\[ 'a', <Buffer 62> ]\\.";
        String regex82 = "^Error.*Expected a file path to write a file, but got '' \\(empty string\\)\\.";
        String regex83 = "^TypeError";
        String regex84 = "\\.(m?js|json|svg|css|html)$";
        String regex85 = "[\\s'\\\\$]";
        String regex86 = "(.*\\/|\\^):([a-z0-9_\\-\\.\\*\\@\\#]+)(\\/.*|\\$)";
        String regex87 = "\\{platform\\}";
        String regex88 = "\\{arch\\}";
        String regex89 = "error\\.error";
        String regex90 = "info\\.info";
        String regex91 = "error\\.info";
        String regex92 = " D debug\\.debug";
        String regex93 = " I info\\.debug";
        String regex94 = " ERROR error\\.debug";
        String regex95 = " D debug\\.any";
        String regex96 = " I info\\.any";
        String regex97 = " ERROR error\\.any";
        String regex98 = "(\\\\[a-zA-Z0-9_\\s]+)*";
        String regex99 = "\\/#\\/";
        String regex100 = "(^[.#]|(?:__|~)$)";

        System.out.println("1 " + generateStrings(regex1, defaultPositiveConfig) + "\n");
        System.out.println("2 " + generateStrings(regex2, defaultPositiveConfig) + "\n");
        System.out.println("3 " + generateStrings(regex3, defaultPositiveConfig) + "\n");
        System.out.println("4 " + generateStrings(regex4, defaultPositiveConfig) + "\n");
        System.out.println("5 " + generateStrings(regex5, defaultPositiveConfig) + "\n");
        System.out.println("6 " + generateStrings(regex6, defaultPositiveConfig) + "\n");
        System.out.println("7 " + generateStrings(regex7, defaultPositiveConfig) + "\n");
        System.out.println("8 " + generateStrings(regex8, defaultPositiveConfig) + "\n");
        System.out.println("9 " + generateStrings(regex9, defaultPositiveConfig) + "\n");
        System.out.println("10 " + generateStrings(regex10, defaultPositiveConfig) + "\n");
        System.out.println("11 " + generateStrings(regex11, defaultPositiveConfig) + "\n");
        System.out.println("12 " + generateStrings(regex12, defaultPositiveConfig) + "\n");
        System.out.println("13 " + generateStrings(regex13, defaultPositiveConfig) + "\n");
        System.out.println("14 " + generateStrings(regex14, defaultPositiveConfig) + "\n");
        System.out.println("15 " + generateStrings(regex15, defaultPositiveConfig) + "\n");
        System.out.println("16 " + generateStrings(regex16, defaultPositiveConfig) + "\n");
        System.out.println("17 " + generateStrings(regex17, defaultPositiveConfig) + "\n");
        System.out.println("18 " + generateStrings(regex18, defaultPositiveConfig) + "\n");
        System.out.println("19 " + generateStrings(regex19, defaultPositiveConfig) + "\n");
        System.out.println("20 " + generateStrings(regex20, defaultPositiveConfig) + "\n");
        System.out.println("21 " + generateStrings(regex21, defaultPositiveConfig) + "\n");
        System.out.println("22 " + generateStrings(regex22, defaultPositiveConfig) + "\n");
        System.out.println("23 " + generateStrings(regex23, defaultPositiveConfig) + "\n");
        System.out.println("24 " + generateStrings(regex24, defaultPositiveConfig) + "\n");
        System.out.println("25 " + generateStrings(regex25, defaultPositiveConfig) + "\n");
        System.out.println("26 " + generateStrings(regex26, defaultPositiveConfig) + "\n");
        System.out.println("27 " + generateStrings(regex27, defaultPositiveConfig) + "\n");
        System.out.println("28 " + generateStrings(regex28, defaultPositiveConfig) + "\n");
        System.out.println("29 " + generateStrings(regex29, defaultPositiveConfig) + "\n");
        System.out.println("30 " + generateStrings(regex30, defaultPositiveConfig) + "\n");
        System.out.println("31 " + generateStrings(regex31, defaultPositiveConfig) + "\n");
        System.out.println("32 " + generateStrings(regex32, defaultPositiveConfig) + "\n");
        System.out.println("33 " + generateStrings(regex33, defaultPositiveConfig) + "\n");
        System.out.println("34 " + generateStrings(regex34, defaultPositiveConfig) + "\n");
        System.out.println("35 " + generateStrings(regex35, defaultPositiveConfig) + "\n");
        System.out.println("36 " + generateStrings(regex36, defaultPositiveConfig) + "\n");
        System.out.println("37 " + generateStrings(regex37, defaultPositiveConfig) + "\n");
        System.out.println("38 " + generateStrings(regex38, defaultPositiveConfig) + "\n");
        System.out.println("39 " + generateStrings(regex39, defaultPositiveConfig) + "\n");
        System.out.println("40 " + generateStrings(regex40, defaultPositiveConfig) + "\n");
        System.out.println("41 " + generateStrings(regex41, defaultPositiveConfig) + "\n");
        System.out.println("42 " + generateStrings(regex42, defaultPositiveConfig) + "\n");
        System.out.println("43 " + generateStrings(regex43, defaultPositiveConfig) + "\n");
        System.out.println("44 " + generateStrings(regex44, defaultPositiveConfig) + "\n");
        System.out.println("45 " + generateStrings(regex45, defaultPositiveConfig) + "\n");
        System.out.println("46 " + generateStrings(regex46, defaultPositiveConfig) + "\n");
        System.out.println("47 " + generateStrings(regex47, defaultPositiveConfig) + "\n");
        System.out.println("48 " + generateStrings(regex48, defaultPositiveConfig) + "\n");
        System.out.println("49 " + generateStrings(regex49, defaultPositiveConfig) + "\n");
        System.out.println("50 " + generateStrings(regex50, defaultPositiveConfig) + "\n");
        System.out.println("51 " + generateStrings(regex51, defaultPositiveConfig) + "\n");
        System.out.println("52 " + generateStrings(regex52, defaultPositiveConfig) + "\n");
        System.out.println("53 " + generateStrings(regex53, defaultPositiveConfig) + "\n");
        System.out.println("54 " + generateStrings(regex54, defaultPositiveConfig) + "\n");
        System.out.println("55 " + generateStrings(regex55, defaultPositiveConfig) + "\n");
        System.out.println("56 " + generateStrings(regex56, defaultPositiveConfig) + "\n");
        System.out.println("57 " + generateStrings(regex57, defaultPositiveConfig) + "\n");
        System.out.println("58 " + generateStrings(regex58, defaultPositiveConfig) + "\n");
        System.out.println("59 " + generateStrings(regex59, defaultPositiveConfig) + "\n");
        System.out.println("60 " + generateStrings(regex60, defaultPositiveConfig) + "\n");
        System.out.println("61 " + generateStrings(regex61, defaultPositiveConfig) + "\n");
        System.out.println("62 " + generateStrings(regex62, defaultPositiveConfig) + "\n");
        System.out.println("63 " + generateStrings(regex63, defaultPositiveConfig) + "\n");
        System.out.println("64 " + generateStrings(regex64, defaultPositiveConfig) + "\n");
        System.out.println("65 " + generateStrings(regex65, defaultPositiveConfig) + "\n");
        System.out.println("66 " + generateStrings(regex66, defaultPositiveConfig) + "\n");
        System.out.println("67 " + generateStrings(regex67, defaultPositiveConfig) + "\n");
        System.out.println("68 " + generateStrings(regex68, defaultPositiveConfig) + "\n");
        System.out.println("69 " + generateStrings(regex69, defaultPositiveConfig) + "\n");
        System.out.println("70 " + generateStrings(regex70, defaultPositiveConfig) + "\n");
        System.out.println("71 " + generateStrings(regex71, defaultPositiveConfig) + "\n");
        System.out.println("72 " + generateStrings(regex72, defaultPositiveConfig) + "\n");
        System.out.println("73 " + generateStrings(regex73, defaultPositiveConfig) + "\n");
        System.out.println("74 " + generateStrings(regex74, defaultPositiveConfig) + "\n");
        System.out.println("75 " + generateStrings(regex75, defaultPositiveConfig) + "\n");
        System.out.println("76 " + generateStrings(regex76, defaultPositiveConfig) + "\n");
        System.out.println("77 " + generateStrings(regex77, defaultPositiveConfig) + "\n");
        System.out.println("78 " + generateStrings(regex78, defaultPositiveConfig) + "\n");
        System.out.println("79 " + generateStrings(regex79, defaultPositiveConfig) + "\n");
        System.out.println("80 " + generateStrings(regex80, defaultPositiveConfig) + "\n");
        System.out.println("81 " + generateStrings(regex81, defaultPositiveConfig) + "\n");
        System.out.println("82 " + generateStrings(regex82, defaultPositiveConfig) + "\n");
        System.out.println("83 " + generateStrings(regex83, defaultPositiveConfig) + "\n");
        System.out.println("84 " + generateStrings(regex84, defaultPositiveConfig) + "\n");
        System.out.println("85 " + generateStrings(regex85, defaultPositiveConfig) + "\n");
        System.out.println("86 " + generateStrings(regex86, defaultPositiveConfig) + "\n");
        System.out.println("87 " + generateStrings(regex87, defaultPositiveConfig) + "\n");
        System.out.println("88 " + generateStrings(regex88, defaultPositiveConfig) + "\n");
        System.out.println("89 " + generateStrings(regex89, defaultPositiveConfig) + "\n");
        System.out.println("90 " + generateStrings(regex90, defaultPositiveConfig) + "\n");
        System.out.println("91 " + generateStrings(regex91, defaultPositiveConfig) + "\n");
        System.out.println("92 " + generateStrings(regex92, defaultPositiveConfig) + "\n");
        System.out.println("93 " + generateStrings(regex93, defaultPositiveConfig) + "\n");
        System.out.println("94 " + generateStrings(regex94, defaultPositiveConfig) + "\n");
        System.out.println("95 " + generateStrings(regex95, defaultPositiveConfig) + "\n");
        System.out.println("96 " + generateStrings(regex96, defaultPositiveConfig) + "\n");
        System.out.println("97 " + generateStrings(regex97, defaultPositiveConfig) + "\n");
        System.out.println("98 " + generateStrings(regex98, defaultPositiveConfig) + "\n");
        System.out.println("99 " + generateStrings(regex99, defaultPositiveConfig) + "\n");
        System.out.println("100 " + generateStrings(regex100, defaultPositiveConfig) + "\n");
    }
}
