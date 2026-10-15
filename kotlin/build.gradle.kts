buildscript {
    repositories { mavenCentral() }
    dependencies { classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.0.21") }
}

apply(plugin = "org.jetbrains.kotlin.jvm")

repositories { mavenCentral() }

dependencies {
    "testImplementation"(kotlin("stdlib"))
    "testImplementation"("org.junit.jupiter:junit-jupiter:5.11.3")
    "testRuntimeOnly"("org.junit.platform:junit-platform-launcher")

    // For a production run against your real Spring Security filter chain, add:
    // testImplementation("org.springframework.boot:spring-boot-starter-test")
    // testImplementation("org.springframework.security:spring-security-test")
    // and back AppUnderTest with a WebTestClient over your application context.
}

tasks.named<Test>("test") {
    useJUnitPlatform()
    testLogging {
        events("passed", "failed", "skipped")
        showStandardStreams = true
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }
}
