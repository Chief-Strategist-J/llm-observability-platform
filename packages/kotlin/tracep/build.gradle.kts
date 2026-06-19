import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    kotlin("jvm") version "1.9.22"
    `java-library`
}

group = "io.tracep"
version = "0.1.0"

repositories {
    mavenCentral()
}

val otelVersion = "1.32.0"

dependencies {
    // OpenTelemetry SDK
    implementation("io.opentelemetry:opentelemetry-sdk:$otelVersion")
    implementation("io.opentelemetry:opentelemetry-exporter-otlp:$otelVersion")
    implementation("io.opentelemetry:opentelemetry-sdk-trace:$otelVersion")
    implementation("io.opentelemetry:opentelemetry-semconv:1.21.0-alpha")

    // Kotlin coroutines for async dispatch
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")

    // Logging
    implementation("org.slf4j:slf4j-simple:2.0.9")

    // Testing
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.1")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")

    // OTel in-memory exporter for tests
    testImplementation("io.opentelemetry:opentelemetry-sdk-testing:$otelVersion")
}

tasks.withType<KotlinCompile> {
    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf("-opt-in=kotlin.time.ExperimentalTime")
    }
}

tasks.withType<Test> {
    useJUnitPlatform()
    testLogging {
        events("passed", "skipped", "failed")
    }
}

// Place test sources from tests/unit on the test source set
sourceSets {
    test {
        kotlin {
            srcDir("tests/unit")
        }
    }
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
}

tasks.register<JavaExec>("runIntegration") {
    mainClass.set("io.tracep.KotlinIntegrationKt")
    classpath = sourceSets["main"].runtimeClasspath
}
