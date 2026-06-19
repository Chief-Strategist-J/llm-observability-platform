const { Tracer } = require('./dist/tracer.js');
async function run() {
  const t = new Tracer("http://localhost:4318", "test-token-12345", "node-integration-service");
  const tid = t.start("node-live-test");
  t.trace(tid, "NodeClass", "run_test", "step_1", "Hello from Node OTel SDK!");
  await t.end(tid, "ok");
  await t.close();
  console.log(tid);
}
run();