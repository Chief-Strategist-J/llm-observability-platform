package io.tracep;

public class JavaIntegration {
    public static void main(String[] args) throws Exception {
        Tracer tracer = new Tracer("http://localhost:4318", "test-token-12345", "java-integration-service");
        String tid = tracer.start("java-live-test");
        tracer.trace(tid, "JavaClass", "run_test", "step_1", "Hello from Java OTel SDK!");
        tracer.end(tid, "ok");
        tracer.close();
        System.out.println(tid);
        System.exit(0);
    }
}
