//
//  Generated code. Do not modify.
//  source: llm/observability/v1/instrumentation.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:convert' as $convert;
import 'dart:core' as $core;
import 'dart:typed_data' as $typed_data;

@$core.Deprecated('Use instrumentationStatusDescriptor instead')
const InstrumentationStatus$json = {
  '1': 'InstrumentationStatus',
  '2': [
    {'1': 'INSTRUMENTATION_STATUS_UNSPECIFIED', '2': 0},
    {'1': 'INSTRUMENTATION_STATUS_INITIALIZED', '2': 1},
    {'1': 'INSTRUMENTATION_STATUS_DISABLED', '2': 2},
    {'1': 'INSTRUMENTATION_STATUS_PARTIAL', '2': 3},
  ],
};

/// Descriptor for `InstrumentationStatus`. Decode as a `google.protobuf.EnumDescriptorProto`.
final $typed_data.Uint8List instrumentationStatusDescriptor = $convert.base64Decode(
    'ChVJbnN0cnVtZW50YXRpb25TdGF0dXMSJgoiSU5TVFJVTUVOVEFUSU9OX1NUQVRVU19VTlNQRU'
    'NJRklFRBAAEiYKIklOU1RSVU1FTlRBVElPTl9TVEFUVVNfSU5JVElBTElaRUQQARIjCh9JTlNU'
    'UlVNRU5UQVRJT05fU1RBVFVTX0RJU0FCTEVEEAISIgoeSU5TVFJVTUVOVEFUSU9OX1NUQVRVU1'
    '9QQVJUSUFMEAM=');

@$core.Deprecated('Use initInstrumentationRequestDescriptor instead')
const InitInstrumentationRequest$json = {
  '1': 'InitInstrumentationRequest',
  '2': [
    {'1': 'service_name', '3': 1, '4': 1, '5': 9, '10': 'serviceName'},
    {'1': 'environment', '3': 2, '4': 1, '5': 9, '10': 'environment'},
  ],
};

/// Descriptor for `InitInstrumentationRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List initInstrumentationRequestDescriptor = $convert.base64Decode(
    'ChpJbml0SW5zdHJ1bWVudGF0aW9uUmVxdWVzdBIhCgxzZXJ2aWNlX25hbWUYASABKAlSC3Nlcn'
    'ZpY2VOYW1lEiAKC2Vudmlyb25tZW50GAIgASgJUgtlbnZpcm9ubWVudA==');

@$core.Deprecated('Use disableInstrumentationRequestDescriptor instead')
const DisableInstrumentationRequest$json = {
  '1': 'DisableInstrumentationRequest',
};

/// Descriptor for `DisableInstrumentationRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List disableInstrumentationRequestDescriptor = $convert.base64Decode(
    'Ch1EaXNhYmxlSW5zdHJ1bWVudGF0aW9uUmVxdWVzdA==');

@$core.Deprecated('Use getStatusRequestDescriptor instead')
const GetStatusRequest$json = {
  '1': 'GetStatusRequest',
};

/// Descriptor for `GetStatusRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getStatusRequestDescriptor = $convert.base64Decode(
    'ChBHZXRTdGF0dXNSZXF1ZXN0');

@$core.Deprecated('Use detectProviderRequestDescriptor instead')
const DetectProviderRequest$json = {
  '1': 'DetectProviderRequest',
  '2': [
    {'1': 'url', '3': 1, '4': 1, '5': 9, '10': 'url'},
    {'1': 'body', '3': 2, '4': 1, '5': 9, '10': 'body'},
  ],
};

/// Descriptor for `DetectProviderRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List detectProviderRequestDescriptor = $convert.base64Decode(
    'ChVEZXRlY3RQcm92aWRlclJlcXVlc3QSEAoDdXJsGAEgASgJUgN1cmwSEgoEYm9keRgCIAEoCV'
    'IEYm9keQ==');

@$core.Deprecated('Use detectProviderResponseDescriptor instead')
const DetectProviderResponse$json = {
  '1': 'DetectProviderResponse',
  '2': [
    {'1': 'provider', '3': 1, '4': 1, '5': 9, '10': 'provider'},
    {'1': 'model', '3': 2, '4': 1, '5': 9, '10': 'model'},
  ],
};

/// Descriptor for `DetectProviderResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List detectProviderResponseDescriptor = $convert.base64Decode(
    'ChZEZXRlY3RQcm92aWRlclJlc3BvbnNlEhoKCHByb3ZpZGVyGAEgASgJUghwcm92aWRlchIUCg'
    'Vtb2RlbBgCIAEoCVIFbW9kZWw=');

@$core.Deprecated('Use triggerTestCallRequestDescriptor instead')
const TriggerTestCallRequest$json = {
  '1': 'TriggerTestCallRequest',
  '2': [
    {'1': 'method', '3': 1, '4': 1, '5': 9, '10': 'method'},
    {'1': 'provider', '3': 2, '4': 1, '5': 9, '10': 'provider'},
  ],
};

/// Descriptor for `TriggerTestCallRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List triggerTestCallRequestDescriptor = $convert.base64Decode(
    'ChZUcmlnZ2VyVGVzdENhbGxSZXF1ZXN0EhYKBm1ldGhvZBgBIAEoCVIGbWV0aG9kEhoKCHByb3'
    'ZpZGVyGAIgASgJUghwcm92aWRlcg==');

@$core.Deprecated('Use triggerTestStreamCallRequestDescriptor instead')
const TriggerTestStreamCallRequest$json = {
  '1': 'TriggerTestStreamCallRequest',
  '2': [
    {'1': 'provider', '3': 1, '4': 1, '5': 9, '10': 'provider'},
    {'1': 'chunks', '3': 2, '4': 3, '5': 9, '10': 'chunks'},
  ],
};

/// Descriptor for `TriggerTestStreamCallRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List triggerTestStreamCallRequestDescriptor = $convert.base64Decode(
    'ChxUcmlnZ2VyVGVzdFN0cmVhbUNhbGxSZXF1ZXN0EhoKCHByb3ZpZGVyGAEgASgJUghwcm92aW'
    'RlchIWCgZjaHVua3MYAiADKAlSBmNodW5rcw==');

@$core.Deprecated('Use instrumentationResponseDescriptor instead')
const InstrumentationResponse$json = {
  '1': 'InstrumentationResponse',
  '2': [
    {'1': 'success', '3': 1, '4': 1, '5': 8, '10': 'success'},
    {'1': 'message', '3': 2, '4': 1, '5': 9, '10': 'message'},
    {'1': 'status', '3': 3, '4': 1, '5': 14, '6': '.llm.observability.v1.InstrumentationStatus', '10': 'status'},
  ],
};

/// Descriptor for `InstrumentationResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List instrumentationResponseDescriptor = $convert.base64Decode(
    'ChdJbnN0cnVtZW50YXRpb25SZXNwb25zZRIYCgdzdWNjZXNzGAEgASgIUgdzdWNjZXNzEhgKB2'
    '1lc3NhZ2UYAiABKAlSB21lc3NhZ2USQwoGc3RhdHVzGAMgASgOMisubGxtLm9ic2VydmFiaWxp'
    'dHkudjEuSW5zdHJ1bWVudGF0aW9uU3RhdHVzUgZzdGF0dXM=');

@$core.Deprecated('Use initInstrumentationResponseDescriptor instead')
const InitInstrumentationResponse$json = {
  '1': 'InitInstrumentationResponse',
  '2': [
    {'1': 'success', '3': 1, '4': 1, '5': 8, '10': 'success'},
    {'1': 'message', '3': 2, '4': 1, '5': 9, '10': 'message'},
    {'1': 'status', '3': 3, '4': 1, '5': 14, '6': '.llm.observability.v1.InstrumentationStatus', '10': 'status'},
  ],
};

/// Descriptor for `InitInstrumentationResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List initInstrumentationResponseDescriptor = $convert.base64Decode(
    'ChtJbml0SW5zdHJ1bWVudGF0aW9uUmVzcG9uc2USGAoHc3VjY2VzcxgBIAEoCFIHc3VjY2Vzcx'
    'IYCgdtZXNzYWdlGAIgASgJUgdtZXNzYWdlEkMKBnN0YXR1cxgDIAEoDjIrLmxsbS5vYnNlcnZh'
    'YmlsaXR5LnYxLkluc3RydW1lbnRhdGlvblN0YXR1c1IGc3RhdHVz');

@$core.Deprecated('Use disableInstrumentationResponseDescriptor instead')
const DisableInstrumentationResponse$json = {
  '1': 'DisableInstrumentationResponse',
  '2': [
    {'1': 'success', '3': 1, '4': 1, '5': 8, '10': 'success'},
    {'1': 'message', '3': 2, '4': 1, '5': 9, '10': 'message'},
    {'1': 'status', '3': 3, '4': 1, '5': 14, '6': '.llm.observability.v1.InstrumentationStatus', '10': 'status'},
  ],
};

/// Descriptor for `DisableInstrumentationResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List disableInstrumentationResponseDescriptor = $convert.base64Decode(
    'Ch5EaXNhYmxlSW5zdHJ1bWVudGF0aW9uUmVzcG9uc2USGAoHc3VjY2VzcxgBIAEoCFIHc3VjY2'
    'VzcxIYCgdtZXNzYWdlGAIgASgJUgdtZXNzYWdlEkMKBnN0YXR1cxgDIAEoDjIrLmxsbS5vYnNl'
    'cnZhYmlsaXR5LnYxLkluc3RydW1lbnRhdGlvblN0YXR1c1IGc3RhdHVz');

@$core.Deprecated('Use getStatusResponseDescriptor instead')
const GetStatusResponse$json = {
  '1': 'GetStatusResponse',
  '2': [
    {'1': 'success', '3': 1, '4': 1, '5': 8, '10': 'success'},
    {'1': 'message', '3': 2, '4': 1, '5': 9, '10': 'message'},
    {'1': 'status', '3': 3, '4': 1, '5': 14, '6': '.llm.observability.v1.InstrumentationStatus', '10': 'status'},
  ],
};

/// Descriptor for `GetStatusResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getStatusResponseDescriptor = $convert.base64Decode(
    'ChFHZXRTdGF0dXNSZXNwb25zZRIYCgdzdWNjZXNzGAEgASgIUgdzdWNjZXNzEhgKB21lc3NhZ2'
    'UYAiABKAlSB21lc3NhZ2USQwoGc3RhdHVzGAMgASgOMisubGxtLm9ic2VydmFiaWxpdHkudjEu'
    'SW5zdHJ1bWVudGF0aW9uU3RhdHVzUgZzdGF0dXM=');

@$core.Deprecated('Use triggerTestCallResponseDescriptor instead')
const TriggerTestCallResponse$json = {
  '1': 'TriggerTestCallResponse',
  '2': [
    {'1': 'success', '3': 1, '4': 1, '5': 8, '10': 'success'},
    {'1': 'message', '3': 2, '4': 1, '5': 9, '10': 'message'},
    {'1': 'status', '3': 3, '4': 1, '5': 14, '6': '.llm.observability.v1.InstrumentationStatus', '10': 'status'},
  ],
};

/// Descriptor for `TriggerTestCallResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List triggerTestCallResponseDescriptor = $convert.base64Decode(
    'ChdUcmlnZ2VyVGVzdENhbGxSZXNwb25zZRIYCgdzdWNjZXNzGAEgASgIUgdzdWNjZXNzEhgKB2'
    '1lc3NhZ2UYAiABKAlSB21lc3NhZ2USQwoGc3RhdHVzGAMgASgOMisubGxtLm9ic2VydmFiaWxp'
    'dHkudjEuSW5zdHJ1bWVudGF0aW9uU3RhdHVzUgZzdGF0dXM=');

@$core.Deprecated('Use triggerTestStreamCallResponseDescriptor instead')
const TriggerTestStreamCallResponse$json = {
  '1': 'TriggerTestStreamCallResponse',
  '2': [
    {'1': 'success', '3': 1, '4': 1, '5': 8, '10': 'success'},
    {'1': 'message', '3': 2, '4': 1, '5': 9, '10': 'message'},
    {'1': 'status', '3': 3, '4': 1, '5': 14, '6': '.llm.observability.v1.InstrumentationStatus', '10': 'status'},
  ],
};

/// Descriptor for `TriggerTestStreamCallResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List triggerTestStreamCallResponseDescriptor = $convert.base64Decode(
    'Ch1UcmlnZ2VyVGVzdFN0cmVhbUNhbGxSZXNwb25zZRIYCgdzdWNjZXNzGAEgASgIUgdzdWNjZX'
    'NzEhgKB21lc3NhZ2UYAiABKAlSB21lc3NhZ2USQwoGc3RhdHVzGAMgASgOMisubGxtLm9ic2Vy'
    'dmFiaWxpdHkudjEuSW5zdHJ1bWVudGF0aW9uU3RhdHVzUgZzdGF0dXM=');

@$core.Deprecated('Use instrumentationEventDescriptor instead')
const InstrumentationEvent$json = {
  '1': 'InstrumentationEvent',
  '2': [
    {'1': 'event_id', '3': 1, '4': 1, '5': 9, '10': 'eventId'},
    {'1': 'timestamp_utc', '3': 2, '4': 1, '5': 9, '10': 'timestampUtc'},
    {'1': 'service_name', '3': 3, '4': 1, '5': 9, '10': 'serviceName'},
    {'1': 'action', '3': 4, '4': 1, '5': 14, '6': '.llm.observability.v1.InstrumentationStatus', '10': 'action'},
    {'1': 'metadata', '3': 5, '4': 1, '5': 9, '10': 'metadata'},
  ],
};

/// Descriptor for `InstrumentationEvent`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List instrumentationEventDescriptor = $convert.base64Decode(
    'ChRJbnN0cnVtZW50YXRpb25FdmVudBIZCghldmVudF9pZBgBIAEoCVIHZXZlbnRJZBIjCg10aW'
    '1lc3RhbXBfdXRjGAIgASgJUgx0aW1lc3RhbXBVdGMSIQoMc2VydmljZV9uYW1lGAMgASgJUgtz'
    'ZXJ2aWNlTmFtZRJDCgZhY3Rpb24YBCABKA4yKy5sbG0ub2JzZXJ2YWJpbGl0eS52MS5JbnN0cn'
    'VtZW50YXRpb25TdGF0dXNSBmFjdGlvbhIaCghtZXRhZGF0YRgFIAEoCVIIbWV0YWRhdGE=');

@$core.Deprecated('Use countTokensRequestDescriptor instead')
const CountTokensRequest$json = {
  '1': 'CountTokensRequest',
  '2': [
    {'1': 'prompt', '3': 1, '4': 1, '5': 9, '10': 'prompt'},
    {'1': 'model', '3': 2, '4': 1, '5': 9, '10': 'model'},
    {'1': 'provider', '3': 3, '4': 1, '5': 9, '10': 'provider'},
  ],
};

/// Descriptor for `CountTokensRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List countTokensRequestDescriptor = $convert.base64Decode(
    'ChJDb3VudFRva2Vuc1JlcXVlc3QSFgoGcHJvbXB0GAEgASgJUgZwcm9tcHQSFAoFbW9kZWwYAi'
    'ABKAlSBW1vZGVsEhoKCHByb3ZpZGVyGAMgASgJUghwcm92aWRlcg==');

@$core.Deprecated('Use countTokensResponseDescriptor instead')
const CountTokensResponse$json = {
  '1': 'CountTokensResponse',
  '2': [
    {'1': 'tokens', '3': 1, '4': 1, '5': 5, '10': 'tokens'},
    {'1': 'method', '3': 2, '4': 1, '5': 9, '10': 'method'},
  ],
};

/// Descriptor for `CountTokensResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List countTokensResponseDescriptor = $convert.base64Decode(
    'ChNDb3VudFRva2Vuc1Jlc3BvbnNlEhYKBnRva2VucxgBIAEoBVIGdG9rZW5zEhYKBm1ldGhvZB'
    'gCIAEoCVIGbWV0aG9k');

@$core.Deprecated('Use scanPiiInjectionRequestDescriptor instead')
const ScanPiiInjectionRequest$json = {
  '1': 'ScanPiiInjectionRequest',
  '2': [
    {'1': 'prompt', '3': 1, '4': 1, '5': 9, '10': 'prompt'},
  ],
};

/// Descriptor for `ScanPiiInjectionRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List scanPiiInjectionRequestDescriptor = $convert.base64Decode(
    'ChdTY2FuUGlpSW5qZWN0aW9uUmVxdWVzdBIWCgZwcm9tcHQYASABKAlSBnByb21wdA==');

@$core.Deprecated('Use scanPiiInjectionResponseDescriptor instead')
const ScanPiiInjectionResponse$json = {
  '1': 'ScanPiiInjectionResponse',
  '2': [
    {'1': 'pii_detected', '3': 1, '4': 1, '5': 8, '10': 'piiDetected'},
    {'1': 'injection_attempt', '3': 2, '4': 1, '5': 8, '10': 'injectionAttempt'},
  ],
};

/// Descriptor for `ScanPiiInjectionResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List scanPiiInjectionResponseDescriptor = $convert.base64Decode(
    'ChhTY2FuUGlpSW5qZWN0aW9uUmVzcG9uc2USIQoMcGlpX2RldGVjdGVkGAEgASgIUgtwaWlEZX'
    'RlY3RlZBIrChFpbmplY3Rpb25fYXR0ZW1wdBgCIAEoCFIQaW5qZWN0aW9uQXR0ZW1wdA==');

@$core.Deprecated('Use initMetricsRequestDescriptor instead')
const InitMetricsRequest$json = {
  '1': 'InitMetricsRequest',
  '2': [
    {'1': 'port', '3': 1, '4': 1, '5': 5, '9': 0, '10': 'port', '17': true},
  ],
  '8': [
    {'1': '_port'},
  ],
};

/// Descriptor for `InitMetricsRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List initMetricsRequestDescriptor = $convert.base64Decode(
    'ChJJbml0TWV0cmljc1JlcXVlc3QSFwoEcG9ydBgBIAEoBUgAUgRwb3J0iAEBQgcKBV9wb3J0');

@$core.Deprecated('Use getMetricsHealthRequestDescriptor instead')
const GetMetricsHealthRequest$json = {
  '1': 'GetMetricsHealthRequest',
};

/// Descriptor for `GetMetricsHealthRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getMetricsHealthRequestDescriptor = $convert.base64Decode(
    'ChdHZXRNZXRyaWNzSGVhbHRoUmVxdWVzdA==');

@$core.Deprecated('Use initMetricsResponseDescriptor instead')
const InitMetricsResponse$json = {
  '1': 'InitMetricsResponse',
  '2': [
    {'1': 'initialized', '3': 1, '4': 1, '5': 8, '10': 'initialized'},
    {'1': 'message', '3': 2, '4': 1, '5': 9, '10': 'message'},
  ],
};

/// Descriptor for `InitMetricsResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List initMetricsResponseDescriptor = $convert.base64Decode(
    'ChNJbml0TWV0cmljc1Jlc3BvbnNlEiAKC2luaXRpYWxpemVkGAEgASgIUgtpbml0aWFsaXplZB'
    'IYCgdtZXNzYWdlGAIgASgJUgdtZXNzYWdl');

@$core.Deprecated('Use getMetricsHealthResponseDescriptor instead')
const GetMetricsHealthResponse$json = {
  '1': 'GetMetricsHealthResponse',
  '2': [
    {'1': 'initialized', '3': 1, '4': 1, '5': 8, '10': 'initialized'},
    {'1': 'message', '3': 2, '4': 1, '5': 9, '10': 'message'},
  ],
};

/// Descriptor for `GetMetricsHealthResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getMetricsHealthResponseDescriptor = $convert.base64Decode(
    'ChhHZXRNZXRyaWNzSGVhbHRoUmVzcG9uc2USIAoLaW5pdGlhbGl6ZWQYASABKAhSC2luaXRpYW'
    'xpemVkEhgKB21lc3NhZ2UYAiABKAlSB21lc3NhZ2U=');

@$core.Deprecated('Use recordMetricsRequestDescriptor instead')
const RecordMetricsRequest$json = {
  '1': 'RecordMetricsRequest',
  '2': [
    {'1': 'model', '3': 1, '4': 1, '5': 9, '10': 'model'},
    {'1': 'provider', '3': 2, '4': 1, '5': 9, '10': 'provider'},
    {'1': 'service_name', '3': 3, '4': 1, '5': 9, '10': 'serviceName'},
    {'1': 'prompt_tokens', '3': 4, '4': 1, '5': 5, '9': 0, '10': 'promptTokens', '17': true},
    {'1': 'completion_tokens', '3': 5, '4': 1, '5': 5, '9': 1, '10': 'completionTokens', '17': true},
    {'1': 'cost_usd_micro', '3': 6, '4': 1, '5': 3, '9': 2, '10': 'costUsdMicro', '17': true},
    {'1': 'latency_ms_total', '3': 7, '4': 1, '5': 5, '9': 3, '10': 'latencyMsTotal', '17': true},
    {'1': 'latency_ms_ttft', '3': 8, '4': 1, '5': 5, '9': 4, '10': 'latencyMsTtft', '17': true},
    {'1': 'finish_reason', '3': 9, '4': 1, '5': 9, '9': 5, '10': 'finishReason', '17': true},
    {'1': 'status', '3': 10, '4': 1, '5': 9, '10': 'status'},
    {'1': 'pii_detected', '3': 11, '4': 1, '5': 8, '10': 'piiDetected'},
    {'1': 'injection_attempt', '3': 12, '4': 1, '5': 8, '10': 'injectionAttempt'},
    {'1': 'retry_count', '3': 13, '4': 1, '5': 5, '10': 'retryCount'},
  ],
  '8': [
    {'1': '_prompt_tokens'},
    {'1': '_completion_tokens'},
    {'1': '_cost_usd_micro'},
    {'1': '_latency_ms_total'},
    {'1': '_latency_ms_ttft'},
    {'1': '_finish_reason'},
  ],
};

/// Descriptor for `RecordMetricsRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List recordMetricsRequestDescriptor = $convert.base64Decode(
    'ChRSZWNvcmRNZXRyaWNzUmVxdWVzdBIUCgVtb2RlbBgBIAEoCVIFbW9kZWwSGgoIcHJvdmlkZX'
    'IYAiABKAlSCHByb3ZpZGVyEiEKDHNlcnZpY2VfbmFtZRgDIAEoCVILc2VydmljZU5hbWUSKAoN'
    'cHJvbXB0X3Rva2VucxgEIAEoBUgAUgxwcm9tcHRUb2tlbnOIAQESMAoRY29tcGxldGlvbl90b2'
    'tlbnMYBSABKAVIAVIQY29tcGxldGlvblRva2Vuc4gBARIpCg5jb3N0X3VzZF9taWNybxgGIAEo'
    'A0gCUgxjb3N0VXNkTWljcm+IAQESLQoQbGF0ZW5jeV9tc190b3RhbBgHIAEoBUgDUg5sYXRlbm'
    'N5TXNUb3RhbIgBARIrCg9sYXRlbmN5X21zX3R0ZnQYCCABKAVIBFINbGF0ZW5jeU1zVHRmdIgB'
    'ARIoCg1maW5pc2hfcmVhc29uGAkgASgJSAVSDGZpbmlzaFJlYXNvbogBARIWCgZzdGF0dXMYCi'
    'ABKAlSBnN0YXR1cxIhCgxwaWlfZGV0ZWN0ZWQYCyABKAhSC3BpaURldGVjdGVkEisKEWluamVj'
    'dGlvbl9hdHRlbXB0GAwgASgIUhBpbmplY3Rpb25BdHRlbXB0Eh8KC3JldHJ5X2NvdW50GA0gAS'
    'gFUgpyZXRyeUNvdW50QhAKDl9wcm9tcHRfdG9rZW5zQhQKEl9jb21wbGV0aW9uX3Rva2Vuc0IR'
    'Cg9fY29zdF91c2RfbWljcm9CEwoRX2xhdGVuY3lfbXNfdG90YWxCEgoQX2xhdGVuY3lfbXNfdH'
    'RmdEIQCg5fZmluaXNoX3JlYXNvbg==');

@$core.Deprecated('Use recordMetricsResponseDescriptor instead')
const RecordMetricsResponse$json = {
  '1': 'RecordMetricsResponse',
  '2': [
    {'1': 'recorded', '3': 1, '4': 1, '5': 8, '10': 'recorded'},
    {'1': 'cost_usd_micro', '3': 2, '4': 1, '5': 3, '9': 0, '10': 'costUsdMicro', '17': true},
    {'1': 'price_version', '3': 3, '4': 1, '5': 9, '9': 1, '10': 'priceVersion', '17': true},
  ],
  '8': [
    {'1': '_cost_usd_micro'},
    {'1': '_price_version'},
  ],
};

/// Descriptor for `RecordMetricsResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List recordMetricsResponseDescriptor = $convert.base64Decode(
    'ChVSZWNvcmRNZXRyaWNzUmVzcG9uc2USGgoIcmVjb3JkZWQYASABKAhSCHJlY29yZGVkEikKDm'
    'Nvc3RfdXNkX21pY3JvGAIgASgDSABSDGNvc3RVc2RNaWNyb4gBARIoCg1wcmljZV92ZXJzaW9u'
    'GAMgASgJSAFSDHByaWNlVmVyc2lvbogBAUIRCg9fY29zdF91c2RfbWljcm9CEAoOX3ByaWNlX3'
    'ZlcnNpb24=');

@$core.Deprecated('Use recordMetricsBatchRequestDescriptor instead')
const RecordMetricsBatchRequest$json = {
  '1': 'RecordMetricsBatchRequest',
  '2': [
    {'1': 'spans', '3': 1, '4': 3, '5': 11, '6': '.llm.observability.v1.RecordMetricsRequest', '10': 'spans'},
  ],
};

/// Descriptor for `RecordMetricsBatchRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List recordMetricsBatchRequestDescriptor = $convert.base64Decode(
    'ChlSZWNvcmRNZXRyaWNzQmF0Y2hSZXF1ZXN0EkAKBXNwYW5zGAEgAygLMioubGxtLm9ic2Vydm'
    'FiaWxpdHkudjEuUmVjb3JkTWV0cmljc1JlcXVlc3RSBXNwYW5z');

@$core.Deprecated('Use recordMetricsBatchResponseDescriptor instead')
const RecordMetricsBatchResponse$json = {
  '1': 'RecordMetricsBatchResponse',
  '2': [
    {'1': 'recorded_count', '3': 1, '4': 1, '5': 5, '10': 'recordedCount'},
  ],
};

/// Descriptor for `RecordMetricsBatchResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List recordMetricsBatchResponseDescriptor = $convert.base64Decode(
    'ChpSZWNvcmRNZXRyaWNzQmF0Y2hSZXNwb25zZRIlCg5yZWNvcmRlZF9jb3VudBgBIAEoBVINcm'
    'Vjb3JkZWRDb3VudA==');

const $core.Map<$core.String, $core.dynamic> InstrumentationControlServiceBase$json = {
  '1': 'InstrumentationControlService',
  '2': [
    {'1': 'InitInstrumentation', '2': '.llm.observability.v1.InitInstrumentationRequest', '3': '.llm.observability.v1.InitInstrumentationResponse'},
    {'1': 'DisableInstrumentation', '2': '.llm.observability.v1.DisableInstrumentationRequest', '3': '.llm.observability.v1.DisableInstrumentationResponse'},
    {'1': 'GetStatus', '2': '.llm.observability.v1.GetStatusRequest', '3': '.llm.observability.v1.GetStatusResponse'},
    {'1': 'DetectProvider', '2': '.llm.observability.v1.DetectProviderRequest', '3': '.llm.observability.v1.DetectProviderResponse'},
    {'1': 'TriggerTestCall', '2': '.llm.observability.v1.TriggerTestCallRequest', '3': '.llm.observability.v1.TriggerTestCallResponse'},
    {'1': 'TriggerTestStreamCall', '2': '.llm.observability.v1.TriggerTestStreamCallRequest', '3': '.llm.observability.v1.TriggerTestStreamCallResponse'},
    {'1': 'CountTokens', '2': '.llm.observability.v1.CountTokensRequest', '3': '.llm.observability.v1.CountTokensResponse'},
    {'1': 'ScanPiiInjection', '2': '.llm.observability.v1.ScanPiiInjectionRequest', '3': '.llm.observability.v1.ScanPiiInjectionResponse'},
    {'1': 'InitMetrics', '2': '.llm.observability.v1.InitMetricsRequest', '3': '.llm.observability.v1.InitMetricsResponse'},
    {'1': 'GetMetricsHealth', '2': '.llm.observability.v1.GetMetricsHealthRequest', '3': '.llm.observability.v1.GetMetricsHealthResponse'},
    {'1': 'RecordMetrics', '2': '.llm.observability.v1.RecordMetricsRequest', '3': '.llm.observability.v1.RecordMetricsResponse'},
    {'1': 'RecordMetricsBatch', '2': '.llm.observability.v1.RecordMetricsBatchRequest', '3': '.llm.observability.v1.RecordMetricsBatchResponse'},
  ],
};

@$core.Deprecated('Use instrumentationControlServiceDescriptor instead')
const $core.Map<$core.String, $core.Map<$core.String, $core.dynamic>> InstrumentationControlServiceBase$messageJson = {
  '.llm.observability.v1.InitInstrumentationRequest': InitInstrumentationRequest$json,
  '.llm.observability.v1.InitInstrumentationResponse': InitInstrumentationResponse$json,
  '.llm.observability.v1.DisableInstrumentationRequest': DisableInstrumentationRequest$json,
  '.llm.observability.v1.DisableInstrumentationResponse': DisableInstrumentationResponse$json,
  '.llm.observability.v1.GetStatusRequest': GetStatusRequest$json,
  '.llm.observability.v1.GetStatusResponse': GetStatusResponse$json,
  '.llm.observability.v1.DetectProviderRequest': DetectProviderRequest$json,
  '.llm.observability.v1.DetectProviderResponse': DetectProviderResponse$json,
  '.llm.observability.v1.TriggerTestCallRequest': TriggerTestCallRequest$json,
  '.llm.observability.v1.TriggerTestCallResponse': TriggerTestCallResponse$json,
  '.llm.observability.v1.TriggerTestStreamCallRequest': TriggerTestStreamCallRequest$json,
  '.llm.observability.v1.TriggerTestStreamCallResponse': TriggerTestStreamCallResponse$json,
  '.llm.observability.v1.CountTokensRequest': CountTokensRequest$json,
  '.llm.observability.v1.CountTokensResponse': CountTokensResponse$json,
  '.llm.observability.v1.ScanPiiInjectionRequest': ScanPiiInjectionRequest$json,
  '.llm.observability.v1.ScanPiiInjectionResponse': ScanPiiInjectionResponse$json,
  '.llm.observability.v1.InitMetricsRequest': InitMetricsRequest$json,
  '.llm.observability.v1.InitMetricsResponse': InitMetricsResponse$json,
  '.llm.observability.v1.GetMetricsHealthRequest': GetMetricsHealthRequest$json,
  '.llm.observability.v1.GetMetricsHealthResponse': GetMetricsHealthResponse$json,
  '.llm.observability.v1.RecordMetricsRequest': RecordMetricsRequest$json,
  '.llm.observability.v1.RecordMetricsResponse': RecordMetricsResponse$json,
  '.llm.observability.v1.RecordMetricsBatchRequest': RecordMetricsBatchRequest$json,
  '.llm.observability.v1.RecordMetricsBatchResponse': RecordMetricsBatchResponse$json,
};

/// Descriptor for `InstrumentationControlService`. Decode as a `google.protobuf.ServiceDescriptorProto`.
final $typed_data.Uint8List instrumentationControlServiceDescriptor = $convert.base64Decode(
    'Ch1JbnN0cnVtZW50YXRpb25Db250cm9sU2VydmljZRJ6ChNJbml0SW5zdHJ1bWVudGF0aW9uEj'
    'AubGxtLm9ic2VydmFiaWxpdHkudjEuSW5pdEluc3RydW1lbnRhdGlvblJlcXVlc3QaMS5sbG0u'
    'b2JzZXJ2YWJpbGl0eS52MS5Jbml0SW5zdHJ1bWVudGF0aW9uUmVzcG9uc2USgwEKFkRpc2FibG'
    'VJbnN0cnVtZW50YXRpb24SMy5sbG0ub2JzZXJ2YWJpbGl0eS52MS5EaXNhYmxlSW5zdHJ1bWVu'
    'dGF0aW9uUmVxdWVzdBo0LmxsbS5vYnNlcnZhYmlsaXR5LnYxLkRpc2FibGVJbnN0cnVtZW50YX'
    'Rpb25SZXNwb25zZRJcCglHZXRTdGF0dXMSJi5sbG0ub2JzZXJ2YWJpbGl0eS52MS5HZXRTdGF0'
    'dXNSZXF1ZXN0GicubGxtLm9ic2VydmFiaWxpdHkudjEuR2V0U3RhdHVzUmVzcG9uc2USawoORG'
    'V0ZWN0UHJvdmlkZXISKy5sbG0ub2JzZXJ2YWJpbGl0eS52MS5EZXRlY3RQcm92aWRlclJlcXVl'
    'c3QaLC5sbG0ub2JzZXJ2YWJpbGl0eS52MS5EZXRlY3RQcm92aWRlclJlc3BvbnNlEm4KD1RyaW'
    'dnZXJUZXN0Q2FsbBIsLmxsbS5vYnNlcnZhYmlsaXR5LnYxLlRyaWdnZXJUZXN0Q2FsbFJlcXVl'
    'c3QaLS5sbG0ub2JzZXJ2YWJpbGl0eS52MS5UcmlnZ2VyVGVzdENhbGxSZXNwb25zZRKAAQoVVH'
    'JpZ2dlclRlc3RTdHJlYW1DYWxsEjIubGxtLm9ic2VydmFiaWxpdHkudjEuVHJpZ2dlclRlc3RT'
    'dHJlYW1DYWxsUmVxdWVzdBozLmxsbS5vYnNlcnZhYmlsaXR5LnYxLlRyaWdnZXJUZXN0U3RyZW'
    'FtQ2FsbFJlc3BvbnNlEmIKC0NvdW50VG9rZW5zEigubGxtLm9ic2VydmFiaWxpdHkudjEuQ291'
    'bnRUb2tlbnNSZXF1ZXN0GikubGxtLm9ic2VydmFiaWxpdHkudjEuQ291bnRUb2tlbnNSZXNwb2'
    '5zZRJxChBTY2FuUGlpSW5qZWN0aW9uEi0ubGxtLm9ic2VydmFiaWxpdHkudjEuU2NhblBpaUlu'
    'amVjdGlvblJlcXVlc3QaLi5sbG0ub2JzZXJ2YWJpbGl0eS52MS5TY2FuUGlpSW5qZWN0aW9uUm'
    'VzcG9uc2USYgoLSW5pdE1ldHJpY3MSKC5sbG0ub2JzZXJ2YWJpbGl0eS52MS5Jbml0TWV0cmlj'
    'c1JlcXVlc3QaKS5sbG0ub2JzZXJ2YWJpbGl0eS52MS5Jbml0TWV0cmljc1Jlc3BvbnNlEnEKEE'
    'dldE1ldHJpY3NIZWFsdGgSLS5sbG0ub2JzZXJ2YWJpbGl0eS52MS5HZXRNZXRyaWNzSGVhbHRo'
    'UmVxdWVzdBouLmxsbS5vYnNlcnZhYmlsaXR5LnYxLkdldE1ldHJpY3NIZWFsdGhSZXNwb25zZR'
    'JoCg1SZWNvcmRNZXRyaWNzEioubGxtLm9ic2VydmFiaWxpdHkudjEuUmVjb3JkTWV0cmljc1Jl'
    'cXVlc3QaKy5sbG0ub2JzZXJ2YWJpbGl0eS52MS5SZWNvcmRNZXRyaWNzUmVzcG9uc2USdwoSUm'
    'Vjb3JkTWV0cmljc0JhdGNoEi8ubGxtLm9ic2VydmFiaWxpdHkudjEuUmVjb3JkTWV0cmljc0Jh'
    'dGNoUmVxdWVzdBowLmxsbS5vYnNlcnZhYmlsaXR5LnYxLlJlY29yZE1ldHJpY3NCYXRjaFJlc3'
    'BvbnNl');

