//
//  Generated code. Do not modify.
//  source: llm/observability/v1/instrumentation.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:core' as $core;

import 'package:protobuf/protobuf.dart' as $pb;

/// InstrumentationStatus represents the current state of auto-instrumentation.
class InstrumentationStatus extends $pb.ProtobufEnum {
  static const InstrumentationStatus INSTRUMENTATION_STATUS_UNSPECIFIED = InstrumentationStatus._(0, _omitEnumNames ? '' : 'INSTRUMENTATION_STATUS_UNSPECIFIED');
  static const InstrumentationStatus INSTRUMENTATION_STATUS_INITIALIZED = InstrumentationStatus._(1, _omitEnumNames ? '' : 'INSTRUMENTATION_STATUS_INITIALIZED');
  static const InstrumentationStatus INSTRUMENTATION_STATUS_DISABLED = InstrumentationStatus._(2, _omitEnumNames ? '' : 'INSTRUMENTATION_STATUS_DISABLED');
  static const InstrumentationStatus INSTRUMENTATION_STATUS_PARTIAL = InstrumentationStatus._(3, _omitEnumNames ? '' : 'INSTRUMENTATION_STATUS_PARTIAL');

  static const $core.List<InstrumentationStatus> values = <InstrumentationStatus> [
    INSTRUMENTATION_STATUS_UNSPECIFIED,
    INSTRUMENTATION_STATUS_INITIALIZED,
    INSTRUMENTATION_STATUS_DISABLED,
    INSTRUMENTATION_STATUS_PARTIAL,
  ];

  static final $core.Map<$core.int, InstrumentationStatus> _byValue = $pb.ProtobufEnum.initByValue(values);
  static InstrumentationStatus? valueOf($core.int value) => _byValue[value];

  const InstrumentationStatus._($core.int v, $core.String n) : super(v, n);
}


const _omitEnumNames = $core.bool.fromEnvironment('protobuf.omit_enum_names');
