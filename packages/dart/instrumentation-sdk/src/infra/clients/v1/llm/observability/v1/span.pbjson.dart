//
//  Generated code. Do not modify.
//  source: llm/observability/v1/span.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:convert' as $convert;
import 'dart:core' as $core;
import 'dart:typed_data' as $typed_data;

@$core.Deprecated('Use finishReasonDescriptor instead')
const FinishReason$json = {
  '1': 'FinishReason',
  '2': [
    {'1': 'FINISH_REASON_UNSPECIFIED', '2': 0},
    {'1': 'FINISH_REASON_STOP', '2': 1},
    {'1': 'FINISH_REASON_LENGTH', '2': 2},
    {'1': 'FINISH_REASON_CONTENT_FILTER', '2': 3},
    {'1': 'FINISH_REASON_TIMEOUT', '2': 4},
    {'1': 'FINISH_REASON_TOOL_CALLS', '2': 5},
    {'1': 'FINISH_REASON_CACHE_HIT', '2': 6},
    {'1': 'FINISH_REASON_CLIENT_DISCONNECT', '2': 7},
  ],
};

/// Descriptor for `FinishReason`. Decode as a `google.protobuf.EnumDescriptorProto`.
final $typed_data.Uint8List finishReasonDescriptor = $convert.base64Decode(
    'CgxGaW5pc2hSZWFzb24SHQoZRklOSVNIX1JFQVNPTl9VTlNQRUNJRklFRBAAEhYKEkZJTklTSF'
    '9SRUFTT05fU1RPUBABEhgKFEZJTklTSF9SRUFTT05fTEVOR1RIEAISIAocRklOSVNIX1JFQVNP'
    'Tl9DT05URU5UX0ZJTFRFUhADEhkKFUZJTklTSF9SRUFTT05fVElNRU9VVBAEEhwKGEZJTklTSF'
    '9SRUFTT05fVE9PTF9DQUxMUxAFEhsKF0ZJTklTSF9SRUFTT05fQ0FDSEVfSElUEAYSIwofRklO'
    'SVNIX1JFQVNPTl9DTElFTlRfRElTQ09OTkVDVBAH');

@$core.Deprecated('Use tokenCountMethodDescriptor instead')
const TokenCountMethod$json = {
  '1': 'TokenCountMethod',
  '2': [
    {'1': 'TOKEN_COUNT_METHOD_UNSPECIFIED', '2': 0},
    {'1': 'TOKEN_COUNT_METHOD_TIKTOKEN', '2': 1},
    {'1': 'TOKEN_COUNT_METHOD_ESTIMATED', '2': 2},
  ],
};

/// Descriptor for `TokenCountMethod`. Decode as a `google.protobuf.EnumDescriptorProto`.
final $typed_data.Uint8List tokenCountMethodDescriptor = $convert.base64Decode(
    'ChBUb2tlbkNvdW50TWV0aG9kEiIKHlRPS0VOX0NPVU5UX01FVEhPRF9VTlNQRUNJRklFRBAAEh'
    '8KG1RPS0VOX0NPVU5UX01FVEhPRF9USUtUT0tFThABEiAKHFRPS0VOX0NPVU5UX01FVEhPRF9F'
    'U1RJTUFURUQQAg==');

@$core.Deprecated('Use environmentDescriptor instead')
const Environment$json = {
  '1': 'Environment',
  '2': [
    {'1': 'ENVIRONMENT_UNSPECIFIED', '2': 0},
    {'1': 'ENVIRONMENT_PRODUCTION', '2': 1},
    {'1': 'ENVIRONMENT_STAGING', '2': 2},
    {'1': 'ENVIRONMENT_DEV', '2': 3},
  ],
};

/// Descriptor for `Environment`. Decode as a `google.protobuf.EnumDescriptorProto`.
final $typed_data.Uint8List environmentDescriptor = $convert.base64Decode(
    'CgtFbnZpcm9ubWVudBIbChdFTlZJUk9OTUVOVF9VTlNQRUNJRklFRBAAEhoKFkVOVklST05NRU'
    '5UX1BST0RVQ1RJT04QARIXChNFTlZJUk9OTUVOVF9TVEFHSU5HEAISEwoPRU5WSVJPTk1FTlRf'
    'REVWEAM=');

@$core.Deprecated('Use lLMSpanDescriptor instead')
const LLMSpan$json = {
  '1': 'LLMSpan',
  '2': [
    {'1': 'span_id', '3': 1, '4': 1, '5': 9, '10': 'spanId'},
    {'1': 'trace_id', '3': 2, '4': 1, '5': 9, '9': 0, '10': 'traceId', '17': true},
    {'1': 'parent_span_id', '3': 3, '4': 1, '5': 9, '9': 1, '10': 'parentSpanId', '17': true},
    {'1': 'schema_version', '3': 4, '4': 1, '5': 5, '10': 'schemaVersion'},
    {'1': 'model', '3': 5, '4': 1, '5': 9, '10': 'model'},
    {'1': 'provider', '3': 6, '4': 1, '5': 9, '10': 'provider'},
    {'1': 'service_name', '3': 7, '4': 1, '5': 9, '10': 'serviceName'},
    {'1': 'endpoint', '3': 8, '4': 1, '5': 9, '10': 'endpoint'},
    {'1': 'environment', '3': 9, '4': 1, '5': 14, '6': '.llm.observability.v1.Environment', '10': 'environment'},
    {'1': 'user_id', '3': 10, '4': 1, '5': 9, '9': 2, '10': 'userId', '17': true},
    {'1': 'session_id', '3': 11, '4': 1, '5': 9, '9': 3, '10': 'sessionId', '17': true},
    {'1': 'prompt_tokens', '3': 12, '4': 1, '5': 5, '10': 'promptTokens'},
    {'1': 'completion_tokens', '3': 13, '4': 1, '5': 5, '10': 'completionTokens'},
    {'1': 'latency_ms_ttft', '3': 14, '4': 1, '5': 5, '9': 4, '10': 'latencyMsTtft', '17': true},
    {'1': 'latency_ms_total', '3': 15, '4': 1, '5': 5, '10': 'latencyMsTotal'},
    {'1': 'finish_reason', '3': 16, '4': 1, '5': 14, '6': '.llm.observability.v1.FinishReason', '10': 'finishReason'},
    {'1': 'cost_usd_micro', '3': 17, '4': 1, '5': 3, '10': 'costUsdMicro'},
    {'1': 'price_version', '3': 18, '4': 1, '5': 9, '10': 'priceVersion'},
    {'1': 'token_count_method', '3': 19, '4': 1, '5': 14, '6': '.llm.observability.v1.TokenCountMethod', '10': 'tokenCountMethod'},
    {'1': 'is_sampled', '3': 20, '4': 1, '5': 8, '10': 'isSampled'},
    {'1': 'retry_count', '3': 21, '4': 1, '5': 5, '10': 'retryCount'},
    {'1': 'attempted_models', '3': 22, '4': 3, '5': 9, '10': 'attemptedModels'},
    {'1': 'pii_detected', '3': 23, '4': 1, '5': 8, '10': 'piiDetected'},
    {'1': 'injection_attempt', '3': 24, '4': 1, '5': 8, '10': 'injectionAttempt'},
    {'1': 'timestamp_utc', '3': 25, '4': 1, '5': 9, '10': 'timestampUtc'},
    {'1': 'prompt_hash', '3': 26, '4': 1, '5': 9, '9': 5, '10': 'promptHash', '17': true},
    {'1': 'prompt_embedding', '3': 27, '4': 3, '5': 2, '10': 'promptEmbedding'},
    {'1': 'response_embedding', '3': 28, '4': 3, '5': 2, '10': 'responseEmbedding'},
  ],
  '8': [
    {'1': '_trace_id'},
    {'1': '_parent_span_id'},
    {'1': '_user_id'},
    {'1': '_session_id'},
    {'1': '_latency_ms_ttft'},
    {'1': '_prompt_hash'},
  ],
};

/// Descriptor for `LLMSpan`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List lLMSpanDescriptor = $convert.base64Decode(
    'CgdMTE1TcGFuEhcKB3NwYW5faWQYASABKAlSBnNwYW5JZBIeCgh0cmFjZV9pZBgCIAEoCUgAUg'
    'd0cmFjZUlkiAEBEikKDnBhcmVudF9zcGFuX2lkGAMgASgJSAFSDHBhcmVudFNwYW5JZIgBARIl'
    'Cg5zY2hlbWFfdmVyc2lvbhgEIAEoBVINc2NoZW1hVmVyc2lvbhIUCgVtb2RlbBgFIAEoCVIFbW'
    '9kZWwSGgoIcHJvdmlkZXIYBiABKAlSCHByb3ZpZGVyEiEKDHNlcnZpY2VfbmFtZRgHIAEoCVIL'
    'c2VydmljZU5hbWUSGgoIZW5kcG9pbnQYCCABKAlSCGVuZHBvaW50EkMKC2Vudmlyb25tZW50GA'
    'kgASgOMiEubGxtLm9ic2VydmFiaWxpdHkudjEuRW52aXJvbm1lbnRSC2Vudmlyb25tZW50EhwK'
    'B3VzZXJfaWQYCiABKAlIAlIGdXNlcklkiAEBEiIKCnNlc3Npb25faWQYCyABKAlIA1IJc2Vzc2'
    'lvbklkiAEBEiMKDXByb21wdF90b2tlbnMYDCABKAVSDHByb21wdFRva2VucxIrChFjb21wbGV0'
    'aW9uX3Rva2VucxgNIAEoBVIQY29tcGxldGlvblRva2VucxIrCg9sYXRlbmN5X21zX3R0ZnQYDi'
    'ABKAVIBFINbGF0ZW5jeU1zVHRmdIgBARIoChBsYXRlbmN5X21zX3RvdGFsGA8gASgFUg5sYXRl'
    'bmN5TXNUb3RhbBJHCg1maW5pc2hfcmVhc29uGBAgASgOMiIubGxtLm9ic2VydmFiaWxpdHkudj'
    'EuRmluaXNoUmVhc29uUgxmaW5pc2hSZWFzb24SJAoOY29zdF91c2RfbWljcm8YESABKANSDGNv'
    'c3RVc2RNaWNybxIjCg1wcmljZV92ZXJzaW9uGBIgASgJUgxwcmljZVZlcnNpb24SVAoSdG9rZW'
    '5fY291bnRfbWV0aG9kGBMgASgOMiYubGxtLm9ic2VydmFiaWxpdHkudjEuVG9rZW5Db3VudE1l'
    'dGhvZFIQdG9rZW5Db3VudE1ldGhvZBIdCgppc19zYW1wbGVkGBQgASgIUglpc1NhbXBsZWQSHw'
    'oLcmV0cnlfY291bnQYFSABKAVSCnJldHJ5Q291bnQSKQoQYXR0ZW1wdGVkX21vZGVscxgWIAMo'
    'CVIPYXR0ZW1wdGVkTW9kZWxzEiEKDHBpaV9kZXRlY3RlZBgXIAEoCFILcGlpRGV0ZWN0ZWQSKw'
    'oRaW5qZWN0aW9uX2F0dGVtcHQYGCABKAhSEGluamVjdGlvbkF0dGVtcHQSIwoNdGltZXN0YW1w'
    'X3V0YxgZIAEoCVIMdGltZXN0YW1wVXRjEiQKC3Byb21wdF9oYXNoGBogASgJSAVSCnByb21wdE'
    'hhc2iIAQESKQoQcHJvbXB0X2VtYmVkZGluZxgbIAMoAlIPcHJvbXB0RW1iZWRkaW5nEi0KEnJl'
    'c3BvbnNlX2VtYmVkZGluZxgcIAMoAlIRcmVzcG9uc2VFbWJlZGRpbmdCCwoJX3RyYWNlX2lkQh'
    'EKD19wYXJlbnRfc3Bhbl9pZEIKCghfdXNlcl9pZEINCgtfc2Vzc2lvbl9pZEISChBfbGF0ZW5j'
    'eV9tc190dGZ0Qg4KDF9wcm9tcHRfaGFzaA==');

@$core.Deprecated('Use recordSpanRequestDescriptor instead')
const RecordSpanRequest$json = {
  '1': 'RecordSpanRequest',
  '2': [
    {'1': 'span', '3': 1, '4': 1, '5': 11, '6': '.llm.observability.v1.LLMSpan', '10': 'span'},
  ],
};

/// Descriptor for `RecordSpanRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List recordSpanRequestDescriptor = $convert.base64Decode(
    'ChFSZWNvcmRTcGFuUmVxdWVzdBIxCgRzcGFuGAEgASgLMh0ubGxtLm9ic2VydmFiaWxpdHkudj'
    'EuTExNU3BhblIEc3Bhbg==');

@$core.Deprecated('Use recordSpanResponseDescriptor instead')
const RecordSpanResponse$json = {
  '1': 'RecordSpanResponse',
  '2': [
    {'1': 'success', '3': 1, '4': 1, '5': 8, '10': 'success'},
    {'1': 'span_warnings', '3': 2, '4': 3, '5': 9, '10': 'spanWarnings'},
  ],
};

/// Descriptor for `RecordSpanResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List recordSpanResponseDescriptor = $convert.base64Decode(
    'ChJSZWNvcmRTcGFuUmVzcG9uc2USGAoHc3VjY2VzcxgBIAEoCFIHc3VjY2VzcxIjCg1zcGFuX3'
    'dhcm5pbmdzGAIgAygJUgxzcGFuV2FybmluZ3M=');

const $core.Map<$core.String, $core.dynamic> SpanIngestionServiceBase$json = {
  '1': 'SpanIngestionService',
  '2': [
    {'1': 'RecordSpan', '2': '.llm.observability.v1.RecordSpanRequest', '3': '.llm.observability.v1.RecordSpanResponse'},
  ],
};

@$core.Deprecated('Use spanIngestionServiceDescriptor instead')
const $core.Map<$core.String, $core.Map<$core.String, $core.dynamic>> SpanIngestionServiceBase$messageJson = {
  '.llm.observability.v1.RecordSpanRequest': RecordSpanRequest$json,
  '.llm.observability.v1.LLMSpan': LLMSpan$json,
  '.llm.observability.v1.RecordSpanResponse': RecordSpanResponse$json,
};

/// Descriptor for `SpanIngestionService`. Decode as a `google.protobuf.ServiceDescriptorProto`.
final $typed_data.Uint8List spanIngestionServiceDescriptor = $convert.base64Decode(
    'ChRTcGFuSW5nZXN0aW9uU2VydmljZRJfCgpSZWNvcmRTcGFuEicubGxtLm9ic2VydmFiaWxpdH'
    'kudjEuUmVjb3JkU3BhblJlcXVlc3QaKC5sbG0ub2JzZXJ2YWJpbGl0eS52MS5SZWNvcmRTcGFu'
    'UmVzcG9uc2U=');

