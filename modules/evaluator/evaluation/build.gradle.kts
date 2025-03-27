import java.net.URI

plugins {
    java
    application
    antlr
    id("com.bmuschko.docker-remote-api") version "9.4.0"
    id("com.bmuschko.docker-java-application") version "9.4.0"
}

group = "edu.institution.lab"
version = "0.6.3"

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.10.0"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testImplementation("org.assertj:assertj-core:3.25.1")

    // brics for coverage
    implementation(project(":dk.brics.automaton"))

    // serialization
    implementation(platform("com.fasterxml.jackson:jackson-bom:2.17.2"))
    implementation("com.fasterxml.jackson.core:jackson-core")
    implementation("com.fasterxml.jackson.core:jackson-databind")
    implementation("com.fasterxml.jackson.core:jackson-annotations")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-jdk8:2.17.2")

    // sqlite driver for JDBC
    implementation("org.xerial:sqlite-jdbc:3.46.0.0")

    // antlr for parsing regexes
    antlr("org.antlr:antlr4:4.9.2")

    // logging
    implementation("org.slf4j:slf4j-api:2.0.13")
    implementation("org.slf4j:slf4j-simple:2.0.13")

    // cli
    implementation("org.jcommander:jcommander:1.83")
}

tasks.test {
    useJUnitPlatform()
}

application {
    mainClass = "edu.institution.lab.evaluation.EvaluationMain"
}

docker {
    javaApplication {
        baseImage.set("amazoncorretto:22-jdk")
        user.set("anonymous")
        // TODO this will need to be updated to your own Docker hub account.
        images.set(setOf("anonymous/regex-evaluator:$version"))
        jvmArgs.set(listOf("-Xms50g", "-Xmx125g"))
    }
}

tasks.generateGrammarSource {
    arguments = arguments + listOf("-visitor", "-long-messages")
}
