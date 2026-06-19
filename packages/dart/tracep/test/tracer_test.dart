import 'dart:async';

import 'package:test/test.dart';
import 'package:tracep/tracep.dart';

// ---------------------------------------------------------------------------
// Minimal stub infrastructure
// ---------------------------------------------------------------------------
//
// We don't hit a real collector in unit tests.  Instead we override the OTel
// exporter via a thin stub so the SDK logic is exercised without network I/O.
//
// The Tracer constructor accepts an optional [exporterOverride] that is only
// used in tests.  In production the real OtlpHttpExporter is used.
//
// Because the opentelemetry package does not provide a built-in fake/mock
// exporter we simply rely on the fact that a non-reachable endpoint causes
// the BatchSpanProcessor to silently drop after retries – which is the
// fire-and-forget contract we test here.
// ---------------------------------------------------------------------------

/// Helper: construct a Tracer pointed at a localhost URL that will never
/// receive data, but whose in-process logic we can exercise fully.
Tracer _makeTracer() => Tracer(
      endpoint: 'http://127.0.0.1:19999', // nothing listening here
      apiKey: 'test-key',
      service: 'test-service',
    );

void main() {
  group('Tracer – lifecycle', () {
    late Tracer tracer;

    setUp(() async {
      tracer = _makeTracer();
      await tracer.init();
    });

    tearDown(() async {
      // close() must be idempotent and not throw.
      await tracer.close().timeout(
            const Duration(seconds: 5),
            onTimeout: () {},
          );
    });

    // -----------------------------------------------------------------------
    test('start returns a non-empty hex trace-id string', () {
      final tid = tracer.start('my-operation');

      expect(tid, isNotEmpty);
      // A TraceId is 128 bits → 32 lower-hex characters.
      expect(tid.length, equals(32));
      expect(
        RegExp(r'^[0-9a-f]{32}$').hasMatch(tid),
        isTrue,
        reason: 'tid should be a 32-char lower-hex string',
      );
    });

    // -----------------------------------------------------------------------
    test('two successive start() calls return different trace-ids', () {
      final tid1 = tracer.start('op-a');
      final tid2 = tracer.start('op-b');

      expect(tid1, isNotEmpty);
      expect(tid2, isNotEmpty);
      expect(tid1, isNot(equals(tid2)));
    });

    // -----------------------------------------------------------------------
    test('trace() with unknown tid is silently ignored', () async {
      // Should complete without throwing.
      tracer.trace(
        'unknown-tid-00000000000000000000000000',
        'MyClass',
        'myMethod',
        'step-1',
        'hello',
      );

      // Give the queue a tick to process.
      await Future.delayed(const Duration(milliseconds: 50));
    });

    // -----------------------------------------------------------------------
    test('end() with unknown tid completes without throwing', () async {
      await expectLater(
        tracer.end('unknown-tid-00000000000000000000000000', 'ok'),
        completes,
      );
    });

    // -----------------------------------------------------------------------
    test('full happy-path: start → trace → end', () async {
      final tid = tracer.start('happy-path');

      tracer.trace(tid, 'ServiceA', 'doWork', 'begin', 'starting work');
      tracer.trace(tid, 'ServiceA', 'doWork', 'middle', 'still working',
          level: 'debug');
      tracer.trace(tid, 'ServiceB', 'fetchData', 'fetch', 'fetching',
          parent: 'ServiceA|doWork');

      // end() must complete (force-flush may fail silently – no collector).
      await expectLater(
        tracer.end(tid, 'ok').timeout(const Duration(seconds: 5)),
        completes,
      );
    });

    // -----------------------------------------------------------------------
    test('end() with status=error completes without throwing', () async {
      final tid = tracer.start('error-path');
      tracer.trace(tid, 'SvcX', 'boom', 'fail', 'something went wrong',
          level: 'error');

      await expectLater(
        tracer.end(tid, 'error').timeout(const Duration(seconds: 5)),
        completes,
      );
    });

    // -----------------------------------------------------------------------
    test('close() is idempotent – second call does not throw', () async {
      await tracer.close();
      // Second close should be a no-op.
      await expectLater(tracer.close(), completes);
    });
  });

  // -------------------------------------------------------------------------
  group('Tracer – init guard', () {
    test('start() before init() throws StateError', () {
      final uninit = _makeTracer();
      expect(() => uninit.start('op'), throwsA(isA<StateError>()));
    });

    test('trace() before init() is silently ignored', () {
      final uninit = _makeTracer();
      // Must not throw.
      uninit.trace('tid', 'C', 'f', 's', 'm');
    });

    test('end() before init() completes without throwing', () async {
      final uninit = _makeTracer();
      await expectLater(uninit.end('tid', 'ok'), completes);
    });
  });
}
