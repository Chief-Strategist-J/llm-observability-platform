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
    '5zZQ==');

