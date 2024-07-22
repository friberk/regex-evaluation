import java.net.URI

plugins {
    java
    application
    antlr
    id("com.bmuschko.docker-remote-api") version "9.4.0"
    id("com.bmuschko.docker-java-application") version "9.4.0"
}

group = "edu.purdue.dualitylab"
version = "0.2.7"

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
    implementation(platform("com.fasterxml.jackson:jackson-bom:2.13.4"))
    implementation("com.fasterxml.jackson.core:jackson-core")
    implementation("com.fasterxml.jackson.core:jackson-databind")
    implementation("com.fasterxml.jackson.core:jackson-annotations")

    // sqlite driver for JDBC
    implementation("org.xerial:sqlite-jdbc:3.46.0.0")

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
    mainClass = "edu.purdue.dualitylab.evaluation.EvaluationMain"
}

docker {
    javaApplication {
        baseImage.set("amazoncorretto:22-jdk")
        user.set("charlie")
        images.set(setOf("softwaresale/regex-evaluator:$version"))
    }
}
