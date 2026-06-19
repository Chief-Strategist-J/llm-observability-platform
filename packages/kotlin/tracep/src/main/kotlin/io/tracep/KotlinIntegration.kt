package io.tracep

import kotlin.system.exitProcess

fun main() {
    val tracer = Tracer("http://localhost:4318", "test-token-12345", "kotlin-integration-service")
    val tid = tracer.start("kotlin-live-test")
    tracer.trace(tid, "KotlinClass", "run_test", "step_1", "Hello from Kotlin OTel SDK!")
    tracer.end(tid, "ok")
    tracer.close()
    println(tid)
    exitProcess(0)
}
