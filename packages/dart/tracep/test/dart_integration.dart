import 'package:tracep/tracep.dart';
import 'dart:io';

void main() async {
  final tracer = Tracer(
    endpoint: 'http://localhost:4318',
    apiKey: 'test-token-12345',
    service: 'dart-integration-service',
  );
  await tracer.init();

  final tid = tracer.start('dart-live-test');
  tracer.trace(tid, 'DartClass', 'run_test', 'step_1', 'Hello from Dart OTel SDK!');
  await tracer.end(tid, 'ok');
  await Future.delayed(const Duration(seconds: 2));
  await tracer.close();
  print(tid);
  exit(0);
}
