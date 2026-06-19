/**
 * tracer.test.ts
 *
 * Unit tests for @tracep/sdk Tracer using Vitest.
 * OTLPTraceExporter is fully mocked so no real network calls are made.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

// ---------------------------------------------------------------------------
// Mock @opentelemetry/exporter-trace-otlp-http
// ---------------------------------------------------------------------------

const mockExport = vi.fn((_spans: unknown, cb: (result: { code: number }) => void) => {
  cb({ code: 0 }); // ExportResultCode.SUCCESS = 0
});

vi.mock('@opentelemetry/exporter-trace-otlp-http', () => ({
  OTLPTraceExporter: vi.fn().mockImplementation(() => ({
    export: mockExport,
    shutdown: vi.fn().mockResolvedValue(undefined),
  })),
}));

// ---------------------------------------------------------------------------
// Mock @opentelemetry/sdk-node so NodeTracerProvider is controllable
// ---------------------------------------------------------------------------

const mockForceFlush = vi.fn().mockResolvedValue(undefined);
const mockShutdown = vi.fn().mockResolvedValue(undefined);
const mockRegister = vi.fn();

// Capture span/event calls
const mockAddEvent = vi.fn();
const mockSetStatus = vi.fn();
const mockEnd = vi.fn();
const mockSetAttribute = vi.fn();

// Factory that produces a fresh mock span each call
let spanIdCounter = 0;
function makeMockSpan() {
  const id = ++spanIdCounter;
  return {
    spanContext: () => ({
      traceId: `traceid${String(id).padStart(28, '0')}`,
      spanId: `spanid${String(id).padStart(10, '0')}`,
    }),
    setStatus: mockSetStatus,
    end: mockEnd,
    addEvent: mockAddEvent,
    setAttribute: mockSetAttribute,
    isRecording: () => true,
  };
}

const mockStartSpan = vi.fn().mockImplementation(() => makeMockSpan());

vi.mock('@opentelemetry/sdk-trace-node', () => ({
  NodeTracerProvider: vi.fn().mockImplementation(() => ({
    register: mockRegister,
    forceFlush: mockForceFlush,
    shutdown: mockShutdown,
    getTracer: vi.fn().mockImplementation(() => ({
      startSpan: mockStartSpan,
    })),
    addSpanProcessor: vi.fn(),
  })),
  BatchSpanProcessor: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Mock @opentelemetry/api
// ---------------------------------------------------------------------------

vi.mock('@opentelemetry/api', async () => {
  const SpanStatusCode = { OK: 1, ERROR: 2, UNSET: 0 };

  // Simple context tracking
  let _active = Symbol('root-ctx');
  const ctxStore = new Map<symbol, unknown>();

  return {
    SpanStatusCode,
    trace: {
      getTracer: vi.fn().mockImplementation((_name: string) => ({
        startSpan: mockStartSpan,
      })),
      setSpan: vi.fn().mockImplementation((ctx: symbol, span: unknown) => {
        const newCtx = Symbol('ctx');
        ctxStore.set(newCtx, span);
        return newCtx;
      }),
      getSpan: vi.fn().mockImplementation((ctx: symbol) => ctxStore.get(ctx)),
    },
    context: {
      active: vi.fn().mockImplementation(() => _active),
      with: vi.fn().mockImplementation((_ctx: unknown, fn: () => unknown) => fn()),
    },
  };
});

// ---------------------------------------------------------------------------
// Import Tracer AFTER mocks are established
// ---------------------------------------------------------------------------

const { Tracer } = await import('../../src/tracer.js');

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Tracer', () => {
  const ENDPOINT = 'http://localhost:4318';
  const API_KEY = 'test-api-key';
  const SERVICE = 'test-service';

  let tracer: InstanceType<typeof Tracer>;

  beforeEach(() => {
    vi.clearAllMocks();
    spanIdCounter = 0;
    tracer = new Tracer(ENDPOINT, API_KEY, SERVICE);
  });

  afterEach(async () => {
    await tracer.close();
  });

  // -------------------------------------------------------------------------
  // start()
  // -------------------------------------------------------------------------

  describe('start()', () => {
    it('returns a non-empty hex string trace ID', () => {
      const tid = tracer.start('my-operation');
      expect(typeof tid).toBe('string');
      expect(tid.length).toBeGreaterThan(0);
    });

    it('returns a different tid on each call', () => {
      const tid1 = tracer.start('op-a');
      const tid2 = tracer.start('op-b');
      expect(tid1).not.toBe(tid2);
    });

    it('calls otelTracer.startSpan with the supplied name', () => {
      tracer.start('hello-world');
      expect(mockStartSpan).toHaveBeenCalledWith('hello-world');
    });
  });

  // -------------------------------------------------------------------------
  // trace()
  // -------------------------------------------------------------------------

  describe('trace()', () => {
    it('adds an event to the span with step name and message', () => {
      const tid = tracer.start('root');
      tracer.trace(tid, 'MyClass', 'myMethod', 'step-1', 'hello there');

      expect(mockAddEvent).toHaveBeenCalledWith('step-1', {
        message: 'hello there',
        level: 'info',
      });
    });

    it('uses the provided level in the event attributes', () => {
      const tid = tracer.start('root');
      tracer.trace(tid, 'Cls', 'fn', 'step', 'msg', { level: 'warn' });

      expect(mockAddEvent).toHaveBeenCalledWith('step', {
        message: 'msg',
        level: 'warn',
      });
    });

    it('defaults level to "info" when not provided', () => {
      const tid = tracer.start('root');
      tracer.trace(tid, 'Cls', 'fn', 'step', 'msg');

      expect(mockAddEvent).toHaveBeenCalledWith('step', {
        message: 'msg',
        level: 'info',
      });
    });

    it('reuses the same span for the same cls+fn pair', () => {
      const tid = tracer.start('root');
      tracer.trace(tid, 'Cls', 'fn', 'step-1', 'first');
      tracer.trace(tid, 'Cls', 'fn', 'step-2', 'second');

      // startSpan called once for root + once for the cls+fn child (not twice)
      const childCalls = mockStartSpan.mock.calls.filter(
        ([name]) => name === 'Cls.fn',
      );
      expect(childCalls).toHaveLength(1);

      // But two events should have been added
      expect(mockAddEvent).toHaveBeenCalledTimes(2);
    });

    it('creates different spans for different cls+fn pairs', () => {
      const tid = tracer.start('root');
      tracer.trace(tid, 'ClsA', 'fnA', 'step', 'msg-a');
      tracer.trace(tid, 'ClsB', 'fnB', 'step', 'msg-b');

      const clsACalls = mockStartSpan.mock.calls.filter(([n]) => n === 'ClsA.fnA');
      const clsBCalls = mockStartSpan.mock.calls.filter(([n]) => n === 'ClsB.fnB');
      expect(clsACalls).toHaveLength(1);
      expect(clsBCalls).toHaveLength(1);
    });

    it('silently drops trace() calls for unknown tid', () => {
      expect(() =>
        tracer.trace('nonexistent-tid', 'Cls', 'fn', 'step', 'msg'),
      ).not.toThrow();
      expect(mockAddEvent).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // end()
  // -------------------------------------------------------------------------

  describe('end()', () => {
    it('calls forceFlush after ending spans', async () => {
      const tid = tracer.start('root');
      await tracer.end(tid, 'ok');
      expect(mockForceFlush).toHaveBeenCalledTimes(1);
    });

    it('sets OK status on spans when status is "ok"', async () => {
      const tid = tracer.start('root');
      tracer.trace(tid, 'Cls', 'fn', 'step', 'msg');
      await tracer.end(tid, 'ok');

      expect(mockSetStatus).toHaveBeenCalledWith({ code: 1 }); // SpanStatusCode.OK
    });

    it('sets ERROR status on spans when status is "error"', async () => {
      const tid = tracer.start('root');
      tracer.trace(tid, 'Cls', 'fn', 'step', 'msg');
      await tracer.end(tid, 'error');

      expect(mockSetStatus).toHaveBeenCalledWith({
        code: 2, // SpanStatusCode.ERROR
        message: 'trace ended with error',
      });
    });

    it('ends all child spans and the root span', async () => {
      const tid = tracer.start('root');
      tracer.trace(tid, 'A', 'x', 's', 'm');
      tracer.trace(tid, 'B', 'y', 's', 'm');
      await tracer.end(tid, 'ok');

      // 1 root + 2 children → 3 end() calls
      expect(mockEnd).toHaveBeenCalledTimes(3);
    });

    it('is a no-op for unknown tid and does not throw', async () => {
      await expect(tracer.end('bad-tid', 'ok')).resolves.toBeUndefined();
      expect(mockForceFlush).not.toHaveBeenCalled();
    });

    it('removes the trace entry so a second end() is a no-op', async () => {
      const tid = tracer.start('root');
      await tracer.end(tid, 'ok');
      mockForceFlush.mockClear();
      await tracer.end(tid, 'ok');
      expect(mockForceFlush).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // 401 / auth failure  (simulated via mock)
  // -------------------------------------------------------------------------

  describe('401 / auth failure', () => {
    it('silently drops data when the exporter receives a non-success result', async () => {
      // Simulate the exporter signalling failure (what a 401 / 5xx would cause)
      mockExport.mockImplementationOnce(
        (_spans: unknown, cb: (result: { code: number }) => void) => {
          cb({ code: 1 }); // ExportResultCode.FAILED
        },
      );

      const tid = tracer.start('secure-op');
      tracer.trace(tid, 'Auth', 'check', 'step', 'classified');

      // end() must resolve without throwing even when export fails
      await expect(tracer.end(tid, 'ok')).resolves.toBeUndefined();
    });

    it('constructs the exporter with the correct Authorization header', () => {
      const mockedExporter = vi.mocked(OTLPTraceExporter);
      // The constructor was called during new Tracer(...)
      expect(mockedExporter).toHaveBeenCalledWith(
        expect.objectContaining({
          url: `${ENDPOINT}/v1/traces`,
          headers: expect.objectContaining({
            Authorization: `Bearer ${API_KEY}`,
          }),
        }),
      );
    });
  });

  // -------------------------------------------------------------------------
  // close()
  // -------------------------------------------------------------------------

  describe('close()', () => {
    it('calls provider.shutdown()', async () => {
      await tracer.close();
      expect(mockShutdown).toHaveBeenCalledTimes(1);
    });

    it('ends any open traces before shutdown', async () => {
      tracer.start('open-trace');
      await tracer.close();
      // root span of the open trace should have been ended
      expect(mockEnd).toHaveBeenCalled();
      expect(mockShutdown).toHaveBeenCalledTimes(1);
    });
  });

  // -------------------------------------------------------------------------
  // OTLPTraceExporter configuration
  // -------------------------------------------------------------------------

  describe('OTLPTraceExporter configuration', () => {
    it('appends /v1/traces to the endpoint URL', () => {
      const mockedExporter = vi.mocked(OTLPTraceExporter);
      expect(mockedExporter).toHaveBeenCalledWith(
        expect.objectContaining({ url: 'http://localhost:4318/v1/traces' }),
      );
    });

    it('strips trailing slash from endpoint before appending /v1/traces', () => {
      new Tracer('http://collector:4318/', API_KEY, SERVICE);
      const mockedExporter = vi.mocked(OTLPTraceExporter);
      const lastCall = mockedExporter.mock.calls.at(-1)!;
      expect(lastCall[0].url).toBe('http://collector:4318/v1/traces');
    });
  });
});
