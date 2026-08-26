//
//  Generated code. Do not modify.
//  source: llm/observability/v1/span.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:core' as $core;

import 'package:protobuf/protobuf.dart' as $pb;

/// FinishReasonEnum captures the possible ways an LLM generation can complete.
class FinishReason extends $pb.ProtobufEnum {
  static const FinishReason FINISH_REASON_UNSPECIFIED = FinishReason._(0, _omitEnumNames ? '' : 'FINISH_REASON_UNSPECIFIED');
  static const FinishReason FINISH_REASON_STOP = FinishReason._(1, _omitEnumNames ? '' : 'FINISH_REASON_STOP');
  static const FinishReason FINISH_REASON_LENGTH = FinishReason._(2, _omitEnumNames ? '' : 'FINISH_REASON_LENGTH');
  static const FinishReason FINISH_REASON_CONTENT_FILTER = FinishReason._(3, _omitEnumNames ? '' : 'FINISH_REASON_CONTENT_FILTER');
  static const FinishReason FINISH_REASON_TIMEOUT = FinishReason._(4, _omitEnumNames ? '' : 'FINISH_REASON_TIMEOUT');
  static const FinishReason FINISH_REASON_TOOL_CALLS = FinishReason._(5, _omitEnumNames ? '' : 'FINISH_REASON_TOOL_CALLS');
  static const FinishReason FINISH_REASON_CACHE_HIT = FinishReason._(6, _omitEnumNames ? '' : 'FINISH_REASON_CACHE_HIT');
  static const FinishReason FINISH_REASON_CLIENT_DISCONNECT = FinishReason._(7, _omitEnumNames ? '' : 'FINISH_REASON_CLIENT_DISCONNECT');

  static const $core.List<FinishReason> values = <FinishReason> [
    FINISH_REASON_UNSPECIFIED,
    FINISH_REASON_STOP,
    FINISH_REASON_LENGTH,
    FINISH_REASON_CONTENT_FILTER,
    FINISH_REASON_TIMEOUT,
    FINISH_REASON_TOOL_CALLS,
    FINISH_REASON_CACHE_HIT,
    FINISH_REASON_CLIENT_DISCONNECT,
  ];

  static final $core.Map<$core.int, FinishReason> _byValue = $pb.ProtobufEnum.initByValue(values);
  static FinishReason? valueOf($core.int value) => _byValue[value];

  const FinishReason._($core.int v, $core.String n) : super(v, n);
}

/// TokenCountMethod captures how the token counts were determined.
class TokenCountMethod extends $pb.ProtobufEnum {
  static const TokenCountMethod TOKEN_COUNT_METHOD_UNSPECIFIED = TokenCountMethod._(0, _omitEnumNames ? '' : 'TOKEN_COUNT_METHOD_UNSPECIFIED');
  static const TokenCountMethod TOKEN_COUNT_METHOD_TIKTOKEN = TokenCountMethod._(1, _omitEnumNames ? '' : 'TOKEN_COUNT_METHOD_TIKTOKEN');
  static const TokenCountMethod TOKEN_COUNT_METHOD_ESTIMATED = TokenCountMethod._(2, _omitEnumNames ? '' : 'TOKEN_COUNT_METHOD_ESTIMATED');

  static const $core.List<TokenCountMethod> values = <TokenCountMethod> [
    TOKEN_COUNT_METHOD_UNSPECIFIED,
    TOKEN_COUNT_METHOD_TIKTOKEN,
    TOKEN_COUNT_METHOD_ESTIMATED,
  ];

  static final $core.Map<$core.int, TokenCountMethod> _byValue = $pb.ProtobufEnum.initByValue(values);
  static TokenCountMethod? valueOf($core.int value) => _byValue[value];

  const TokenCountMethod._($core.int v, $core.String n) : super(v, n);
}

/// Environment Enum captures the deployment environment.
class Environment extends $pb.ProtobufEnum {
  static const Environment ENVIRONMENT_UNSPECIFIED = Environment._(0, _omitEnumNames ? '' : 'ENVIRONMENT_UNSPECIFIED');
  static const Environment ENVIRONMENT_PRODUCTION = Environment._(1, _omitEnumNames ? '' : 'ENVIRONMENT_PRODUCTION');
  static const Environment ENVIRONMENT_STAGING = Environment._(2, _omitEnumNames ? '' : 'ENVIRONMENT_STAGING');
  static const Environment ENVIRONMENT_DEV = Environment._(3, _omitEnumNames ? '' : 'ENVIRONMENT_DEV');

  static const $core.List<Environment> values = <Environment> [
    ENVIRONMENT_UNSPECIFIED,
    ENVIRONMENT_PRODUCTION,
    ENVIRONMENT_STAGING,
    ENVIRONMENT_DEV,
  ];

  static final $core.Map<$core.int, Environment> _byValue = $pb.ProtobufEnum.initByValue(values);
  static Environment? valueOf($core.int value) => _byValue[value];

  const Environment._($core.int v, $core.String n) : super(v, n);
}


const _omitEnumNames = $core.bool.fromEnvironment('protobuf.omit_enum_names');
