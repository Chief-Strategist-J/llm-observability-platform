//
//  Generated code. Do not modify.
//  source: llm/observability/v1/instrumentation.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:async' as $async;
import 'dart:core' as $core;

import 'package:fixnum/fixnum.dart' as $fixnum;
import 'package:protobuf/protobuf.dart' as $pb;

import 'instrumentation.pbenum.dart';

export 'instrumentation.pbenum.dart';

class InitInstrumentationRequest extends $pb.GeneratedMessage {
  factory InitInstrumentationRequest({
    $core.String? serviceName,
    $core.String? environment,
  }) {
    final $result = create();
    if (serviceName != null) {
      $result.serviceName = serviceName;
    }
    if (environment != null) {
      $result.environment = environment;
    }
    return $result;
  }
  InitInstrumentationRequest._() : super();
  factory InitInstrumentationRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory InitInstrumentationRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'InitInstrumentationRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'serviceName')
    ..aOS(2, _omitFieldNames ? '' : 'environment')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  InitInstrumentationRequest clone() => InitInstrumentationRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  InitInstrumentationRequest copyWith(void Function(InitInstrumentationRequest) updates) => super.copyWith((message) => updates(message as InitInstrumentationRequest)) as InitInstrumentationRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static InitInstrumentationRequest create() => InitInstrumentationRequest._();
  InitInstrumentationRequest createEmptyInstance() => create();
  static $pb.PbList<InitInstrumentationRequest> createRepeated() => $pb.PbList<InitInstrumentationRequest>();
  @$core.pragma('dart2js:noInline')
  static InitInstrumentationRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<InitInstrumentationRequest>(create);
  static InitInstrumentationRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get serviceName => $_getSZ(0);
  @$pb.TagNumber(1)
  set serviceName($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasServiceName() => $_has(0);
  @$pb.TagNumber(1)
  void clearServiceName() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get environment => $_getSZ(1);
  @$pb.TagNumber(2)
  set environment($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasEnvironment() => $_has(1);
  @$pb.TagNumber(2)
  void clearEnvironment() => clearField(2);
}

class DisableInstrumentationRequest extends $pb.GeneratedMessage {
  factory DisableInstrumentationRequest() => create();
  DisableInstrumentationRequest._() : super();
  factory DisableInstrumentationRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory DisableInstrumentationRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'DisableInstrumentationRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  DisableInstrumentationRequest clone() => DisableInstrumentationRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  DisableInstrumentationRequest copyWith(void Function(DisableInstrumentationRequest) updates) => super.copyWith((message) => updates(message as DisableInstrumentationRequest)) as DisableInstrumentationRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static DisableInstrumentationRequest create() => DisableInstrumentationRequest._();
  DisableInstrumentationRequest createEmptyInstance() => create();
  static $pb.PbList<DisableInstrumentationRequest> createRepeated() => $pb.PbList<DisableInstrumentationRequest>();
  @$core.pragma('dart2js:noInline')
  static DisableInstrumentationRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<DisableInstrumentationRequest>(create);
  static DisableInstrumentationRequest? _defaultInstance;
}

class GetStatusRequest extends $pb.GeneratedMessage {
  factory GetStatusRequest() => create();
  GetStatusRequest._() : super();
  factory GetStatusRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetStatusRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetStatusRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetStatusRequest clone() => GetStatusRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetStatusRequest copyWith(void Function(GetStatusRequest) updates) => super.copyWith((message) => updates(message as GetStatusRequest)) as GetStatusRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetStatusRequest create() => GetStatusRequest._();
  GetStatusRequest createEmptyInstance() => create();
  static $pb.PbList<GetStatusRequest> createRepeated() => $pb.PbList<GetStatusRequest>();
  @$core.pragma('dart2js:noInline')
  static GetStatusRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetStatusRequest>(create);
  static GetStatusRequest? _defaultInstance;
}

class DetectProviderRequest extends $pb.GeneratedMessage {
  factory DetectProviderRequest({
    $core.String? url,
    $core.String? body,
  }) {
    final $result = create();
    if (url != null) {
      $result.url = url;
    }
    if (body != null) {
      $result.body = body;
    }
    return $result;
  }
  DetectProviderRequest._() : super();
  factory DetectProviderRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory DetectProviderRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'DetectProviderRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'url')
    ..aOS(2, _omitFieldNames ? '' : 'body')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  DetectProviderRequest clone() => DetectProviderRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  DetectProviderRequest copyWith(void Function(DetectProviderRequest) updates) => super.copyWith((message) => updates(message as DetectProviderRequest)) as DetectProviderRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static DetectProviderRequest create() => DetectProviderRequest._();
  DetectProviderRequest createEmptyInstance() => create();
  static $pb.PbList<DetectProviderRequest> createRepeated() => $pb.PbList<DetectProviderRequest>();
  @$core.pragma('dart2js:noInline')
  static DetectProviderRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<DetectProviderRequest>(create);
  static DetectProviderRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get url => $_getSZ(0);
  @$pb.TagNumber(1)
  set url($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasUrl() => $_has(0);
  @$pb.TagNumber(1)
  void clearUrl() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get body => $_getSZ(1);
  @$pb.TagNumber(2)
  set body($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasBody() => $_has(1);
  @$pb.TagNumber(2)
  void clearBody() => clearField(2);
}

class DetectProviderResponse extends $pb.GeneratedMessage {
  factory DetectProviderResponse({
    $core.String? provider,
    $core.String? model,
  }) {
    final $result = create();
    if (provider != null) {
      $result.provider = provider;
    }
    if (model != null) {
      $result.model = model;
    }
    return $result;
  }
  DetectProviderResponse._() : super();
  factory DetectProviderResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory DetectProviderResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'DetectProviderResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'provider')
    ..aOS(2, _omitFieldNames ? '' : 'model')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  DetectProviderResponse clone() => DetectProviderResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  DetectProviderResponse copyWith(void Function(DetectProviderResponse) updates) => super.copyWith((message) => updates(message as DetectProviderResponse)) as DetectProviderResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static DetectProviderResponse create() => DetectProviderResponse._();
  DetectProviderResponse createEmptyInstance() => create();
  static $pb.PbList<DetectProviderResponse> createRepeated() => $pb.PbList<DetectProviderResponse>();
  @$core.pragma('dart2js:noInline')
  static DetectProviderResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<DetectProviderResponse>(create);
  static DetectProviderResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get provider => $_getSZ(0);
  @$pb.TagNumber(1)
  set provider($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasProvider() => $_has(0);
  @$pb.TagNumber(1)
  void clearProvider() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get model => $_getSZ(1);
  @$pb.TagNumber(2)
  set model($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasModel() => $_has(1);
  @$pb.TagNumber(2)
  void clearModel() => clearField(2);
}

class TriggerTestCallRequest extends $pb.GeneratedMessage {
  factory TriggerTestCallRequest({
    $core.String? method,
    $core.String? provider,
  }) {
    final $result = create();
    if (method != null) {
      $result.method = method;
    }
    if (provider != null) {
      $result.provider = provider;
    }
    return $result;
  }
  TriggerTestCallRequest._() : super();
  factory TriggerTestCallRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory TriggerTestCallRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'TriggerTestCallRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'method')
    ..aOS(2, _omitFieldNames ? '' : 'provider')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  TriggerTestCallRequest clone() => TriggerTestCallRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  TriggerTestCallRequest copyWith(void Function(TriggerTestCallRequest) updates) => super.copyWith((message) => updates(message as TriggerTestCallRequest)) as TriggerTestCallRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static TriggerTestCallRequest create() => TriggerTestCallRequest._();
  TriggerTestCallRequest createEmptyInstance() => create();
  static $pb.PbList<TriggerTestCallRequest> createRepeated() => $pb.PbList<TriggerTestCallRequest>();
  @$core.pragma('dart2js:noInline')
  static TriggerTestCallRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<TriggerTestCallRequest>(create);
  static TriggerTestCallRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get method => $_getSZ(0);
  @$pb.TagNumber(1)
  set method($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasMethod() => $_has(0);
  @$pb.TagNumber(1)
  void clearMethod() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get provider => $_getSZ(1);
  @$pb.TagNumber(2)
  set provider($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasProvider() => $_has(1);
  @$pb.TagNumber(2)
  void clearProvider() => clearField(2);
}

class TriggerTestStreamCallRequest extends $pb.GeneratedMessage {
  factory TriggerTestStreamCallRequest({
    $core.String? provider,
    $core.Iterable<$core.String>? chunks,
  }) {
    final $result = create();
    if (provider != null) {
      $result.provider = provider;
    }
    if (chunks != null) {
      $result.chunks.addAll(chunks);
    }
    return $result;
  }
  TriggerTestStreamCallRequest._() : super();
  factory TriggerTestStreamCallRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory TriggerTestStreamCallRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'TriggerTestStreamCallRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'provider')
    ..pPS(2, _omitFieldNames ? '' : 'chunks')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  TriggerTestStreamCallRequest clone() => TriggerTestStreamCallRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  TriggerTestStreamCallRequest copyWith(void Function(TriggerTestStreamCallRequest) updates) => super.copyWith((message) => updates(message as TriggerTestStreamCallRequest)) as TriggerTestStreamCallRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static TriggerTestStreamCallRequest create() => TriggerTestStreamCallRequest._();
  TriggerTestStreamCallRequest createEmptyInstance() => create();
  static $pb.PbList<TriggerTestStreamCallRequest> createRepeated() => $pb.PbList<TriggerTestStreamCallRequest>();
  @$core.pragma('dart2js:noInline')
  static TriggerTestStreamCallRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<TriggerTestStreamCallRequest>(create);
  static TriggerTestStreamCallRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get provider => $_getSZ(0);
  @$pb.TagNumber(1)
  set provider($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasProvider() => $_has(0);
  @$pb.TagNumber(1)
  void clearProvider() => clearField(1);

  @$pb.TagNumber(2)
  $core.List<$core.String> get chunks => $_getList(1);
}

class InstrumentationResponse extends $pb.GeneratedMessage {
  factory InstrumentationResponse({
    $core.bool? success,
    $core.String? message,
    InstrumentationStatus? status,
  }) {
    final $result = create();
    if (success != null) {
      $result.success = success;
    }
    if (message != null) {
      $result.message = message;
    }
    if (status != null) {
      $result.status = status;
    }
    return $result;
  }
  InstrumentationResponse._() : super();
  factory InstrumentationResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory InstrumentationResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'InstrumentationResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'success')
    ..aOS(2, _omitFieldNames ? '' : 'message')
    ..e<InstrumentationStatus>(3, _omitFieldNames ? '' : 'status', $pb.PbFieldType.OE, defaultOrMaker: InstrumentationStatus.INSTRUMENTATION_STATUS_UNSPECIFIED, valueOf: InstrumentationStatus.valueOf, enumValues: InstrumentationStatus.values)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  InstrumentationResponse clone() => InstrumentationResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  InstrumentationResponse copyWith(void Function(InstrumentationResponse) updates) => super.copyWith((message) => updates(message as InstrumentationResponse)) as InstrumentationResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static InstrumentationResponse create() => InstrumentationResponse._();
  InstrumentationResponse createEmptyInstance() => create();
  static $pb.PbList<InstrumentationResponse> createRepeated() => $pb.PbList<InstrumentationResponse>();
  @$core.pragma('dart2js:noInline')
  static InstrumentationResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<InstrumentationResponse>(create);
  static InstrumentationResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get success => $_getBF(0);
  @$pb.TagNumber(1)
  set success($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSuccess() => $_has(0);
  @$pb.TagNumber(1)
  void clearSuccess() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get message => $_getSZ(1);
  @$pb.TagNumber(2)
  set message($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMessage() => $_has(1);
  @$pb.TagNumber(2)
  void clearMessage() => clearField(2);

  @$pb.TagNumber(3)
  InstrumentationStatus get status => $_getN(2);
  @$pb.TagNumber(3)
  set status(InstrumentationStatus v) { setField(3, v); }
  @$pb.TagNumber(3)
  $core.bool hasStatus() => $_has(2);
  @$pb.TagNumber(3)
  void clearStatus() => clearField(3);
}

class InitInstrumentationResponse extends $pb.GeneratedMessage {
  factory InitInstrumentationResponse({
    $core.bool? success,
    $core.String? message,
    InstrumentationStatus? status,
  }) {
    final $result = create();
    if (success != null) {
      $result.success = success;
    }
    if (message != null) {
      $result.message = message;
    }
    if (status != null) {
      $result.status = status;
    }
    return $result;
  }
  InitInstrumentationResponse._() : super();
  factory InitInstrumentationResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory InitInstrumentationResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'InitInstrumentationResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'success')
    ..aOS(2, _omitFieldNames ? '' : 'message')
    ..e<InstrumentationStatus>(3, _omitFieldNames ? '' : 'status', $pb.PbFieldType.OE, defaultOrMaker: InstrumentationStatus.INSTRUMENTATION_STATUS_UNSPECIFIED, valueOf: InstrumentationStatus.valueOf, enumValues: InstrumentationStatus.values)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  InitInstrumentationResponse clone() => InitInstrumentationResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  InitInstrumentationResponse copyWith(void Function(InitInstrumentationResponse) updates) => super.copyWith((message) => updates(message as InitInstrumentationResponse)) as InitInstrumentationResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static InitInstrumentationResponse create() => InitInstrumentationResponse._();
  InitInstrumentationResponse createEmptyInstance() => create();
  static $pb.PbList<InitInstrumentationResponse> createRepeated() => $pb.PbList<InitInstrumentationResponse>();
  @$core.pragma('dart2js:noInline')
  static InitInstrumentationResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<InitInstrumentationResponse>(create);
  static InitInstrumentationResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get success => $_getBF(0);
  @$pb.TagNumber(1)
  set success($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSuccess() => $_has(0);
  @$pb.TagNumber(1)
  void clearSuccess() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get message => $_getSZ(1);
  @$pb.TagNumber(2)
  set message($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMessage() => $_has(1);
  @$pb.TagNumber(2)
  void clearMessage() => clearField(2);

  @$pb.TagNumber(3)
  InstrumentationStatus get status => $_getN(2);
  @$pb.TagNumber(3)
  set status(InstrumentationStatus v) { setField(3, v); }
  @$pb.TagNumber(3)
  $core.bool hasStatus() => $_has(2);
  @$pb.TagNumber(3)
  void clearStatus() => clearField(3);
}

class DisableInstrumentationResponse extends $pb.GeneratedMessage {
  factory DisableInstrumentationResponse({
    $core.bool? success,
    $core.String? message,
    InstrumentationStatus? status,
  }) {
    final $result = create();
    if (success != null) {
      $result.success = success;
    }
    if (message != null) {
      $result.message = message;
    }
    if (status != null) {
      $result.status = status;
    }
    return $result;
  }
  DisableInstrumentationResponse._() : super();
  factory DisableInstrumentationResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory DisableInstrumentationResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'DisableInstrumentationResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'success')
    ..aOS(2, _omitFieldNames ? '' : 'message')
    ..e<InstrumentationStatus>(3, _omitFieldNames ? '' : 'status', $pb.PbFieldType.OE, defaultOrMaker: InstrumentationStatus.INSTRUMENTATION_STATUS_UNSPECIFIED, valueOf: InstrumentationStatus.valueOf, enumValues: InstrumentationStatus.values)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  DisableInstrumentationResponse clone() => DisableInstrumentationResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  DisableInstrumentationResponse copyWith(void Function(DisableInstrumentationResponse) updates) => super.copyWith((message) => updates(message as DisableInstrumentationResponse)) as DisableInstrumentationResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static DisableInstrumentationResponse create() => DisableInstrumentationResponse._();
  DisableInstrumentationResponse createEmptyInstance() => create();
  static $pb.PbList<DisableInstrumentationResponse> createRepeated() => $pb.PbList<DisableInstrumentationResponse>();
  @$core.pragma('dart2js:noInline')
  static DisableInstrumentationResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<DisableInstrumentationResponse>(create);
  static DisableInstrumentationResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get success => $_getBF(0);
  @$pb.TagNumber(1)
  set success($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSuccess() => $_has(0);
  @$pb.TagNumber(1)
  void clearSuccess() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get message => $_getSZ(1);
  @$pb.TagNumber(2)
  set message($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMessage() => $_has(1);
  @$pb.TagNumber(2)
  void clearMessage() => clearField(2);

  @$pb.TagNumber(3)
  InstrumentationStatus get status => $_getN(2);
  @$pb.TagNumber(3)
  set status(InstrumentationStatus v) { setField(3, v); }
  @$pb.TagNumber(3)
  $core.bool hasStatus() => $_has(2);
  @$pb.TagNumber(3)
  void clearStatus() => clearField(3);
}

class GetStatusResponse extends $pb.GeneratedMessage {
  factory GetStatusResponse({
    $core.bool? success,
    $core.String? message,
    InstrumentationStatus? status,
  }) {
    final $result = create();
    if (success != null) {
      $result.success = success;
    }
    if (message != null) {
      $result.message = message;
    }
    if (status != null) {
      $result.status = status;
    }
    return $result;
  }
  GetStatusResponse._() : super();
  factory GetStatusResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetStatusResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetStatusResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'success')
    ..aOS(2, _omitFieldNames ? '' : 'message')
    ..e<InstrumentationStatus>(3, _omitFieldNames ? '' : 'status', $pb.PbFieldType.OE, defaultOrMaker: InstrumentationStatus.INSTRUMENTATION_STATUS_UNSPECIFIED, valueOf: InstrumentationStatus.valueOf, enumValues: InstrumentationStatus.values)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetStatusResponse clone() => GetStatusResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetStatusResponse copyWith(void Function(GetStatusResponse) updates) => super.copyWith((message) => updates(message as GetStatusResponse)) as GetStatusResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetStatusResponse create() => GetStatusResponse._();
  GetStatusResponse createEmptyInstance() => create();
  static $pb.PbList<GetStatusResponse> createRepeated() => $pb.PbList<GetStatusResponse>();
  @$core.pragma('dart2js:noInline')
  static GetStatusResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetStatusResponse>(create);
  static GetStatusResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get success => $_getBF(0);
  @$pb.TagNumber(1)
  set success($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSuccess() => $_has(0);
  @$pb.TagNumber(1)
  void clearSuccess() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get message => $_getSZ(1);
  @$pb.TagNumber(2)
  set message($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMessage() => $_has(1);
  @$pb.TagNumber(2)
  void clearMessage() => clearField(2);

  @$pb.TagNumber(3)
  InstrumentationStatus get status => $_getN(2);
  @$pb.TagNumber(3)
  set status(InstrumentationStatus v) { setField(3, v); }
  @$pb.TagNumber(3)
  $core.bool hasStatus() => $_has(2);
  @$pb.TagNumber(3)
  void clearStatus() => clearField(3);
}

class TriggerTestCallResponse extends $pb.GeneratedMessage {
  factory TriggerTestCallResponse({
    $core.bool? success,
    $core.String? message,
    InstrumentationStatus? status,
  }) {
    final $result = create();
    if (success != null) {
      $result.success = success;
    }
    if (message != null) {
      $result.message = message;
    }
    if (status != null) {
      $result.status = status;
    }
    return $result;
  }
  TriggerTestCallResponse._() : super();
  factory TriggerTestCallResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory TriggerTestCallResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'TriggerTestCallResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'success')
    ..aOS(2, _omitFieldNames ? '' : 'message')
    ..e<InstrumentationStatus>(3, _omitFieldNames ? '' : 'status', $pb.PbFieldType.OE, defaultOrMaker: InstrumentationStatus.INSTRUMENTATION_STATUS_UNSPECIFIED, valueOf: InstrumentationStatus.valueOf, enumValues: InstrumentationStatus.values)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  TriggerTestCallResponse clone() => TriggerTestCallResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  TriggerTestCallResponse copyWith(void Function(TriggerTestCallResponse) updates) => super.copyWith((message) => updates(message as TriggerTestCallResponse)) as TriggerTestCallResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static TriggerTestCallResponse create() => TriggerTestCallResponse._();
  TriggerTestCallResponse createEmptyInstance() => create();
  static $pb.PbList<TriggerTestCallResponse> createRepeated() => $pb.PbList<TriggerTestCallResponse>();
  @$core.pragma('dart2js:noInline')
  static TriggerTestCallResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<TriggerTestCallResponse>(create);
  static TriggerTestCallResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get success => $_getBF(0);
  @$pb.TagNumber(1)
  set success($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSuccess() => $_has(0);
  @$pb.TagNumber(1)
  void clearSuccess() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get message => $_getSZ(1);
  @$pb.TagNumber(2)
  set message($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMessage() => $_has(1);
  @$pb.TagNumber(2)
  void clearMessage() => clearField(2);

  @$pb.TagNumber(3)
  InstrumentationStatus get status => $_getN(2);
  @$pb.TagNumber(3)
  set status(InstrumentationStatus v) { setField(3, v); }
  @$pb.TagNumber(3)
  $core.bool hasStatus() => $_has(2);
  @$pb.TagNumber(3)
  void clearStatus() => clearField(3);
}

class TriggerTestStreamCallResponse extends $pb.GeneratedMessage {
  factory TriggerTestStreamCallResponse({
    $core.bool? success,
    $core.String? message,
    InstrumentationStatus? status,
  }) {
    final $result = create();
    if (success != null) {
      $result.success = success;
    }
    if (message != null) {
      $result.message = message;
    }
    if (status != null) {
      $result.status = status;
    }
    return $result;
  }
  TriggerTestStreamCallResponse._() : super();
  factory TriggerTestStreamCallResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory TriggerTestStreamCallResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'TriggerTestStreamCallResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'success')
    ..aOS(2, _omitFieldNames ? '' : 'message')
    ..e<InstrumentationStatus>(3, _omitFieldNames ? '' : 'status', $pb.PbFieldType.OE, defaultOrMaker: InstrumentationStatus.INSTRUMENTATION_STATUS_UNSPECIFIED, valueOf: InstrumentationStatus.valueOf, enumValues: InstrumentationStatus.values)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  TriggerTestStreamCallResponse clone() => TriggerTestStreamCallResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  TriggerTestStreamCallResponse copyWith(void Function(TriggerTestStreamCallResponse) updates) => super.copyWith((message) => updates(message as TriggerTestStreamCallResponse)) as TriggerTestStreamCallResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static TriggerTestStreamCallResponse create() => TriggerTestStreamCallResponse._();
  TriggerTestStreamCallResponse createEmptyInstance() => create();
  static $pb.PbList<TriggerTestStreamCallResponse> createRepeated() => $pb.PbList<TriggerTestStreamCallResponse>();
  @$core.pragma('dart2js:noInline')
  static TriggerTestStreamCallResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<TriggerTestStreamCallResponse>(create);
  static TriggerTestStreamCallResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get success => $_getBF(0);
  @$pb.TagNumber(1)
  set success($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSuccess() => $_has(0);
  @$pb.TagNumber(1)
  void clearSuccess() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get message => $_getSZ(1);
  @$pb.TagNumber(2)
  set message($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMessage() => $_has(1);
  @$pb.TagNumber(2)
  void clearMessage() => clearField(2);

  @$pb.TagNumber(3)
  InstrumentationStatus get status => $_getN(2);
  @$pb.TagNumber(3)
  set status(InstrumentationStatus v) { setField(3, v); }
  @$pb.TagNumber(3)
  $core.bool hasStatus() => $_has(2);
  @$pb.TagNumber(3)
  void clearStatus() => clearField(3);
}

/// Event for publishing instrumentation state changes to Kafka
class InstrumentationEvent extends $pb.GeneratedMessage {
  factory InstrumentationEvent({
    $core.String? eventId,
    $core.String? timestampUtc,
    $core.String? serviceName,
    InstrumentationStatus? action,
    $core.String? metadata,
  }) {
    final $result = create();
    if (eventId != null) {
      $result.eventId = eventId;
    }
    if (timestampUtc != null) {
      $result.timestampUtc = timestampUtc;
    }
    if (serviceName != null) {
      $result.serviceName = serviceName;
    }
    if (action != null) {
      $result.action = action;
    }
    if (metadata != null) {
      $result.metadata = metadata;
    }
    return $result;
  }
  InstrumentationEvent._() : super();
  factory InstrumentationEvent.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory InstrumentationEvent.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'InstrumentationEvent', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'eventId')
    ..aOS(2, _omitFieldNames ? '' : 'timestampUtc')
    ..aOS(3, _omitFieldNames ? '' : 'serviceName')
    ..e<InstrumentationStatus>(4, _omitFieldNames ? '' : 'action', $pb.PbFieldType.OE, defaultOrMaker: InstrumentationStatus.INSTRUMENTATION_STATUS_UNSPECIFIED, valueOf: InstrumentationStatus.valueOf, enumValues: InstrumentationStatus.values)
    ..aOS(5, _omitFieldNames ? '' : 'metadata')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  InstrumentationEvent clone() => InstrumentationEvent()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  InstrumentationEvent copyWith(void Function(InstrumentationEvent) updates) => super.copyWith((message) => updates(message as InstrumentationEvent)) as InstrumentationEvent;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static InstrumentationEvent create() => InstrumentationEvent._();
  InstrumentationEvent createEmptyInstance() => create();
  static $pb.PbList<InstrumentationEvent> createRepeated() => $pb.PbList<InstrumentationEvent>();
  @$core.pragma('dart2js:noInline')
  static InstrumentationEvent getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<InstrumentationEvent>(create);
  static InstrumentationEvent? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get eventId => $_getSZ(0);
  @$pb.TagNumber(1)
  set eventId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasEventId() => $_has(0);
  @$pb.TagNumber(1)
  void clearEventId() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get timestampUtc => $_getSZ(1);
  @$pb.TagNumber(2)
  set timestampUtc($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasTimestampUtc() => $_has(1);
  @$pb.TagNumber(2)
  void clearTimestampUtc() => clearField(2);

  @$pb.TagNumber(3)
  $core.String get serviceName => $_getSZ(2);
  @$pb.TagNumber(3)
  set serviceName($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasServiceName() => $_has(2);
  @$pb.TagNumber(3)
  void clearServiceName() => clearField(3);

  @$pb.TagNumber(4)
  InstrumentationStatus get action => $_getN(3);
  @$pb.TagNumber(4)
  set action(InstrumentationStatus v) { setField(4, v); }
  @$pb.TagNumber(4)
  $core.bool hasAction() => $_has(3);
  @$pb.TagNumber(4)
  void clearAction() => clearField(4);

  @$pb.TagNumber(5)
  $core.String get metadata => $_getSZ(4);
  @$pb.TagNumber(5)
  set metadata($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasMetadata() => $_has(4);
  @$pb.TagNumber(5)
  void clearMetadata() => clearField(5);
}

class CountTokensRequest extends $pb.GeneratedMessage {
  factory CountTokensRequest({
    $core.String? prompt,
    $core.String? model,
    $core.String? provider,
  }) {
    final $result = create();
    if (prompt != null) {
      $result.prompt = prompt;
    }
    if (model != null) {
      $result.model = model;
    }
    if (provider != null) {
      $result.provider = provider;
    }
    return $result;
  }
  CountTokensRequest._() : super();
  factory CountTokensRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory CountTokensRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'CountTokensRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'prompt')
    ..aOS(2, _omitFieldNames ? '' : 'model')
    ..aOS(3, _omitFieldNames ? '' : 'provider')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  CountTokensRequest clone() => CountTokensRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  CountTokensRequest copyWith(void Function(CountTokensRequest) updates) => super.copyWith((message) => updates(message as CountTokensRequest)) as CountTokensRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static CountTokensRequest create() => CountTokensRequest._();
  CountTokensRequest createEmptyInstance() => create();
  static $pb.PbList<CountTokensRequest> createRepeated() => $pb.PbList<CountTokensRequest>();
  @$core.pragma('dart2js:noInline')
  static CountTokensRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<CountTokensRequest>(create);
  static CountTokensRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get prompt => $_getSZ(0);
  @$pb.TagNumber(1)
  set prompt($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasPrompt() => $_has(0);
  @$pb.TagNumber(1)
  void clearPrompt() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get model => $_getSZ(1);
  @$pb.TagNumber(2)
  set model($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasModel() => $_has(1);
  @$pb.TagNumber(2)
  void clearModel() => clearField(2);

  @$pb.TagNumber(3)
  $core.String get provider => $_getSZ(2);
  @$pb.TagNumber(3)
  set provider($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasProvider() => $_has(2);
  @$pb.TagNumber(3)
  void clearProvider() => clearField(3);
}

class CountTokensResponse extends $pb.GeneratedMessage {
  factory CountTokensResponse({
    $core.int? tokens,
    $core.String? method,
  }) {
    final $result = create();
    if (tokens != null) {
      $result.tokens = tokens;
    }
    if (method != null) {
      $result.method = method;
    }
    return $result;
  }
  CountTokensResponse._() : super();
  factory CountTokensResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory CountTokensResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'CountTokensResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..a<$core.int>(1, _omitFieldNames ? '' : 'tokens', $pb.PbFieldType.O3)
    ..aOS(2, _omitFieldNames ? '' : 'method')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  CountTokensResponse clone() => CountTokensResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  CountTokensResponse copyWith(void Function(CountTokensResponse) updates) => super.copyWith((message) => updates(message as CountTokensResponse)) as CountTokensResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static CountTokensResponse create() => CountTokensResponse._();
  CountTokensResponse createEmptyInstance() => create();
  static $pb.PbList<CountTokensResponse> createRepeated() => $pb.PbList<CountTokensResponse>();
  @$core.pragma('dart2js:noInline')
  static CountTokensResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<CountTokensResponse>(create);
  static CountTokensResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.int get tokens => $_getIZ(0);
  @$pb.TagNumber(1)
  set tokens($core.int v) { $_setSignedInt32(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasTokens() => $_has(0);
  @$pb.TagNumber(1)
  void clearTokens() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get method => $_getSZ(1);
  @$pb.TagNumber(2)
  set method($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMethod() => $_has(1);
  @$pb.TagNumber(2)
  void clearMethod() => clearField(2);
}

class ScanPiiInjectionRequest extends $pb.GeneratedMessage {
  factory ScanPiiInjectionRequest({
    $core.String? prompt,
  }) {
    final $result = create();
    if (prompt != null) {
      $result.prompt = prompt;
    }
    return $result;
  }
  ScanPiiInjectionRequest._() : super();
  factory ScanPiiInjectionRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ScanPiiInjectionRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ScanPiiInjectionRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'prompt')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ScanPiiInjectionRequest clone() => ScanPiiInjectionRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ScanPiiInjectionRequest copyWith(void Function(ScanPiiInjectionRequest) updates) => super.copyWith((message) => updates(message as ScanPiiInjectionRequest)) as ScanPiiInjectionRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ScanPiiInjectionRequest create() => ScanPiiInjectionRequest._();
  ScanPiiInjectionRequest createEmptyInstance() => create();
  static $pb.PbList<ScanPiiInjectionRequest> createRepeated() => $pb.PbList<ScanPiiInjectionRequest>();
  @$core.pragma('dart2js:noInline')
  static ScanPiiInjectionRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ScanPiiInjectionRequest>(create);
  static ScanPiiInjectionRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get prompt => $_getSZ(0);
  @$pb.TagNumber(1)
  set prompt($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasPrompt() => $_has(0);
  @$pb.TagNumber(1)
  void clearPrompt() => clearField(1);
}

class ScanPiiInjectionResponse extends $pb.GeneratedMessage {
  factory ScanPiiInjectionResponse({
    $core.bool? piiDetected,
    $core.bool? injectionAttempt,
  }) {
    final $result = create();
    if (piiDetected != null) {
      $result.piiDetected = piiDetected;
    }
    if (injectionAttempt != null) {
      $result.injectionAttempt = injectionAttempt;
    }
    return $result;
  }
  ScanPiiInjectionResponse._() : super();
  factory ScanPiiInjectionResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ScanPiiInjectionResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ScanPiiInjectionResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'piiDetected')
    ..aOB(2, _omitFieldNames ? '' : 'injectionAttempt')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ScanPiiInjectionResponse clone() => ScanPiiInjectionResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ScanPiiInjectionResponse copyWith(void Function(ScanPiiInjectionResponse) updates) => super.copyWith((message) => updates(message as ScanPiiInjectionResponse)) as ScanPiiInjectionResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ScanPiiInjectionResponse create() => ScanPiiInjectionResponse._();
  ScanPiiInjectionResponse createEmptyInstance() => create();
  static $pb.PbList<ScanPiiInjectionResponse> createRepeated() => $pb.PbList<ScanPiiInjectionResponse>();
  @$core.pragma('dart2js:noInline')
  static ScanPiiInjectionResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ScanPiiInjectionResponse>(create);
  static ScanPiiInjectionResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get piiDetected => $_getBF(0);
  @$pb.TagNumber(1)
  set piiDetected($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasPiiDetected() => $_has(0);
  @$pb.TagNumber(1)
  void clearPiiDetected() => clearField(1);

  @$pb.TagNumber(2)
  $core.bool get injectionAttempt => $_getBF(1);
  @$pb.TagNumber(2)
  set injectionAttempt($core.bool v) { $_setBool(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasInjectionAttempt() => $_has(1);
  @$pb.TagNumber(2)
  void clearInjectionAttempt() => clearField(2);
}

class ShouldSampleRequest extends $pb.GeneratedMessage {
  factory ShouldSampleRequest({
    $core.String? spanId,
  }) {
    final $result = create();
    if (spanId != null) {
      $result.spanId = spanId;
    }
    return $result;
  }
  ShouldSampleRequest._() : super();
  factory ShouldSampleRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ShouldSampleRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ShouldSampleRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'spanId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ShouldSampleRequest clone() => ShouldSampleRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ShouldSampleRequest copyWith(void Function(ShouldSampleRequest) updates) => super.copyWith((message) => updates(message as ShouldSampleRequest)) as ShouldSampleRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ShouldSampleRequest create() => ShouldSampleRequest._();
  ShouldSampleRequest createEmptyInstance() => create();
  static $pb.PbList<ShouldSampleRequest> createRepeated() => $pb.PbList<ShouldSampleRequest>();
  @$core.pragma('dart2js:noInline')
  static ShouldSampleRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ShouldSampleRequest>(create);
  static ShouldSampleRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get spanId => $_getSZ(0);
  @$pb.TagNumber(1)
  set spanId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSpanId() => $_has(0);
  @$pb.TagNumber(1)
  void clearSpanId() => clearField(1);
}

class ShouldSampleResponse extends $pb.GeneratedMessage {
  factory ShouldSampleResponse({
    $core.bool? isSampled,
  }) {
    final $result = create();
    if (isSampled != null) {
      $result.isSampled = isSampled;
    }
    return $result;
  }
  ShouldSampleResponse._() : super();
  factory ShouldSampleResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ShouldSampleResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ShouldSampleResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'isSampled')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ShouldSampleResponse clone() => ShouldSampleResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ShouldSampleResponse copyWith(void Function(ShouldSampleResponse) updates) => super.copyWith((message) => updates(message as ShouldSampleResponse)) as ShouldSampleResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ShouldSampleResponse create() => ShouldSampleResponse._();
  ShouldSampleResponse createEmptyInstance() => create();
  static $pb.PbList<ShouldSampleResponse> createRepeated() => $pb.PbList<ShouldSampleResponse>();
  @$core.pragma('dart2js:noInline')
  static ShouldSampleResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ShouldSampleResponse>(create);
  static ShouldSampleResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get isSampled => $_getBF(0);
  @$pb.TagNumber(1)
  set isSampled($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasIsSampled() => $_has(0);
  @$pb.TagNumber(1)
  void clearIsSampled() => clearField(1);
}

class InitMetricsRequest extends $pb.GeneratedMessage {
  factory InitMetricsRequest({
    $core.int? port,
  }) {
    final $result = create();
    if (port != null) {
      $result.port = port;
    }
    return $result;
  }
  InitMetricsRequest._() : super();
  factory InitMetricsRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory InitMetricsRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'InitMetricsRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..a<$core.int>(1, _omitFieldNames ? '' : 'port', $pb.PbFieldType.O3)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  InitMetricsRequest clone() => InitMetricsRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  InitMetricsRequest copyWith(void Function(InitMetricsRequest) updates) => super.copyWith((message) => updates(message as InitMetricsRequest)) as InitMetricsRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static InitMetricsRequest create() => InitMetricsRequest._();
  InitMetricsRequest createEmptyInstance() => create();
  static $pb.PbList<InitMetricsRequest> createRepeated() => $pb.PbList<InitMetricsRequest>();
  @$core.pragma('dart2js:noInline')
  static InitMetricsRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<InitMetricsRequest>(create);
  static InitMetricsRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.int get port => $_getIZ(0);
  @$pb.TagNumber(1)
  set port($core.int v) { $_setSignedInt32(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasPort() => $_has(0);
  @$pb.TagNumber(1)
  void clearPort() => clearField(1);
}

class GetMetricsHealthRequest extends $pb.GeneratedMessage {
  factory GetMetricsHealthRequest() => create();
  GetMetricsHealthRequest._() : super();
  factory GetMetricsHealthRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetMetricsHealthRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetMetricsHealthRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetMetricsHealthRequest clone() => GetMetricsHealthRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetMetricsHealthRequest copyWith(void Function(GetMetricsHealthRequest) updates) => super.copyWith((message) => updates(message as GetMetricsHealthRequest)) as GetMetricsHealthRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetMetricsHealthRequest create() => GetMetricsHealthRequest._();
  GetMetricsHealthRequest createEmptyInstance() => create();
  static $pb.PbList<GetMetricsHealthRequest> createRepeated() => $pb.PbList<GetMetricsHealthRequest>();
  @$core.pragma('dart2js:noInline')
  static GetMetricsHealthRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetMetricsHealthRequest>(create);
  static GetMetricsHealthRequest? _defaultInstance;
}

class InitMetricsResponse extends $pb.GeneratedMessage {
  factory InitMetricsResponse({
    $core.bool? initialized,
    $core.String? message,
  }) {
    final $result = create();
    if (initialized != null) {
      $result.initialized = initialized;
    }
    if (message != null) {
      $result.message = message;
    }
    return $result;
  }
  InitMetricsResponse._() : super();
  factory InitMetricsResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory InitMetricsResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'InitMetricsResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'initialized')
    ..aOS(2, _omitFieldNames ? '' : 'message')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  InitMetricsResponse clone() => InitMetricsResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  InitMetricsResponse copyWith(void Function(InitMetricsResponse) updates) => super.copyWith((message) => updates(message as InitMetricsResponse)) as InitMetricsResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static InitMetricsResponse create() => InitMetricsResponse._();
  InitMetricsResponse createEmptyInstance() => create();
  static $pb.PbList<InitMetricsResponse> createRepeated() => $pb.PbList<InitMetricsResponse>();
  @$core.pragma('dart2js:noInline')
  static InitMetricsResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<InitMetricsResponse>(create);
  static InitMetricsResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get initialized => $_getBF(0);
  @$pb.TagNumber(1)
  set initialized($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasInitialized() => $_has(0);
  @$pb.TagNumber(1)
  void clearInitialized() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get message => $_getSZ(1);
  @$pb.TagNumber(2)
  set message($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMessage() => $_has(1);
  @$pb.TagNumber(2)
  void clearMessage() => clearField(2);
}

class GetMetricsHealthResponse extends $pb.GeneratedMessage {
  factory GetMetricsHealthResponse({
    $core.bool? initialized,
    $core.String? message,
  }) {
    final $result = create();
    if (initialized != null) {
      $result.initialized = initialized;
    }
    if (message != null) {
      $result.message = message;
    }
    return $result;
  }
  GetMetricsHealthResponse._() : super();
  factory GetMetricsHealthResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetMetricsHealthResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetMetricsHealthResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'initialized')
    ..aOS(2, _omitFieldNames ? '' : 'message')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetMetricsHealthResponse clone() => GetMetricsHealthResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetMetricsHealthResponse copyWith(void Function(GetMetricsHealthResponse) updates) => super.copyWith((message) => updates(message as GetMetricsHealthResponse)) as GetMetricsHealthResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetMetricsHealthResponse create() => GetMetricsHealthResponse._();
  GetMetricsHealthResponse createEmptyInstance() => create();
  static $pb.PbList<GetMetricsHealthResponse> createRepeated() => $pb.PbList<GetMetricsHealthResponse>();
  @$core.pragma('dart2js:noInline')
  static GetMetricsHealthResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetMetricsHealthResponse>(create);
  static GetMetricsHealthResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get initialized => $_getBF(0);
  @$pb.TagNumber(1)
  set initialized($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasInitialized() => $_has(0);
  @$pb.TagNumber(1)
  void clearInitialized() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get message => $_getSZ(1);
  @$pb.TagNumber(2)
  set message($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMessage() => $_has(1);
  @$pb.TagNumber(2)
  void clearMessage() => clearField(2);
}

class RecordMetricsRequest extends $pb.GeneratedMessage {
  factory RecordMetricsRequest({
    $core.String? model,
    $core.String? provider,
    $core.String? serviceName,
    $core.int? promptTokens,
    $core.int? completionTokens,
    $fixnum.Int64? costUsdMicro,
    $core.int? latencyMsTotal,
    $core.int? latencyMsTtft,
    $core.String? finishReason,
    $core.String? status,
    $core.bool? piiDetected,
    $core.bool? injectionAttempt,
    $core.int? retryCount,
  }) {
    final $result = create();
    if (model != null) {
      $result.model = model;
    }
    if (provider != null) {
      $result.provider = provider;
    }
    if (serviceName != null) {
      $result.serviceName = serviceName;
    }
    if (promptTokens != null) {
      $result.promptTokens = promptTokens;
    }
    if (completionTokens != null) {
      $result.completionTokens = completionTokens;
    }
    if (costUsdMicro != null) {
      $result.costUsdMicro = costUsdMicro;
    }
    if (latencyMsTotal != null) {
      $result.latencyMsTotal = latencyMsTotal;
    }
    if (latencyMsTtft != null) {
      $result.latencyMsTtft = latencyMsTtft;
    }
    if (finishReason != null) {
      $result.finishReason = finishReason;
    }
    if (status != null) {
      $result.status = status;
    }
    if (piiDetected != null) {
      $result.piiDetected = piiDetected;
    }
    if (injectionAttempt != null) {
      $result.injectionAttempt = injectionAttempt;
    }
    if (retryCount != null) {
      $result.retryCount = retryCount;
    }
    return $result;
  }
  RecordMetricsRequest._() : super();
  factory RecordMetricsRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory RecordMetricsRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'RecordMetricsRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'model')
    ..aOS(2, _omitFieldNames ? '' : 'provider')
    ..aOS(3, _omitFieldNames ? '' : 'serviceName')
    ..a<$core.int>(4, _omitFieldNames ? '' : 'promptTokens', $pb.PbFieldType.O3)
    ..a<$core.int>(5, _omitFieldNames ? '' : 'completionTokens', $pb.PbFieldType.O3)
    ..aInt64(6, _omitFieldNames ? '' : 'costUsdMicro')
    ..a<$core.int>(7, _omitFieldNames ? '' : 'latencyMsTotal', $pb.PbFieldType.O3)
    ..a<$core.int>(8, _omitFieldNames ? '' : 'latencyMsTtft', $pb.PbFieldType.O3)
    ..aOS(9, _omitFieldNames ? '' : 'finishReason')
    ..aOS(10, _omitFieldNames ? '' : 'status')
    ..aOB(11, _omitFieldNames ? '' : 'piiDetected')
    ..aOB(12, _omitFieldNames ? '' : 'injectionAttempt')
    ..a<$core.int>(13, _omitFieldNames ? '' : 'retryCount', $pb.PbFieldType.O3)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  RecordMetricsRequest clone() => RecordMetricsRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  RecordMetricsRequest copyWith(void Function(RecordMetricsRequest) updates) => super.copyWith((message) => updates(message as RecordMetricsRequest)) as RecordMetricsRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static RecordMetricsRequest create() => RecordMetricsRequest._();
  RecordMetricsRequest createEmptyInstance() => create();
  static $pb.PbList<RecordMetricsRequest> createRepeated() => $pb.PbList<RecordMetricsRequest>();
  @$core.pragma('dart2js:noInline')
  static RecordMetricsRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<RecordMetricsRequest>(create);
  static RecordMetricsRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get model => $_getSZ(0);
  @$pb.TagNumber(1)
  set model($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasModel() => $_has(0);
  @$pb.TagNumber(1)
  void clearModel() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get provider => $_getSZ(1);
  @$pb.TagNumber(2)
  set provider($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasProvider() => $_has(1);
  @$pb.TagNumber(2)
  void clearProvider() => clearField(2);

  @$pb.TagNumber(3)
  $core.String get serviceName => $_getSZ(2);
  @$pb.TagNumber(3)
  set serviceName($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasServiceName() => $_has(2);
  @$pb.TagNumber(3)
  void clearServiceName() => clearField(3);

  @$pb.TagNumber(4)
  $core.int get promptTokens => $_getIZ(3);
  @$pb.TagNumber(4)
  set promptTokens($core.int v) { $_setSignedInt32(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasPromptTokens() => $_has(3);
  @$pb.TagNumber(4)
  void clearPromptTokens() => clearField(4);

  @$pb.TagNumber(5)
  $core.int get completionTokens => $_getIZ(4);
  @$pb.TagNumber(5)
  set completionTokens($core.int v) { $_setSignedInt32(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasCompletionTokens() => $_has(4);
  @$pb.TagNumber(5)
  void clearCompletionTokens() => clearField(5);

  @$pb.TagNumber(6)
  $fixnum.Int64 get costUsdMicro => $_getI64(5);
  @$pb.TagNumber(6)
  set costUsdMicro($fixnum.Int64 v) { $_setInt64(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasCostUsdMicro() => $_has(5);
  @$pb.TagNumber(6)
  void clearCostUsdMicro() => clearField(6);

  @$pb.TagNumber(7)
  $core.int get latencyMsTotal => $_getIZ(6);
  @$pb.TagNumber(7)
  set latencyMsTotal($core.int v) { $_setSignedInt32(6, v); }
  @$pb.TagNumber(7)
  $core.bool hasLatencyMsTotal() => $_has(6);
  @$pb.TagNumber(7)
  void clearLatencyMsTotal() => clearField(7);

  @$pb.TagNumber(8)
  $core.int get latencyMsTtft => $_getIZ(7);
  @$pb.TagNumber(8)
  set latencyMsTtft($core.int v) { $_setSignedInt32(7, v); }
  @$pb.TagNumber(8)
  $core.bool hasLatencyMsTtft() => $_has(7);
  @$pb.TagNumber(8)
  void clearLatencyMsTtft() => clearField(8);

  @$pb.TagNumber(9)
  $core.String get finishReason => $_getSZ(8);
  @$pb.TagNumber(9)
  set finishReason($core.String v) { $_setString(8, v); }
  @$pb.TagNumber(9)
  $core.bool hasFinishReason() => $_has(8);
  @$pb.TagNumber(9)
  void clearFinishReason() => clearField(9);

  @$pb.TagNumber(10)
  $core.String get status => $_getSZ(9);
  @$pb.TagNumber(10)
  set status($core.String v) { $_setString(9, v); }
  @$pb.TagNumber(10)
  $core.bool hasStatus() => $_has(9);
  @$pb.TagNumber(10)
  void clearStatus() => clearField(10);

  @$pb.TagNumber(11)
  $core.bool get piiDetected => $_getBF(10);
  @$pb.TagNumber(11)
  set piiDetected($core.bool v) { $_setBool(10, v); }
  @$pb.TagNumber(11)
  $core.bool hasPiiDetected() => $_has(10);
  @$pb.TagNumber(11)
  void clearPiiDetected() => clearField(11);

  @$pb.TagNumber(12)
  $core.bool get injectionAttempt => $_getBF(11);
  @$pb.TagNumber(12)
  set injectionAttempt($core.bool v) { $_setBool(11, v); }
  @$pb.TagNumber(12)
  $core.bool hasInjectionAttempt() => $_has(11);
  @$pb.TagNumber(12)
  void clearInjectionAttempt() => clearField(12);

  @$pb.TagNumber(13)
  $core.int get retryCount => $_getIZ(12);
  @$pb.TagNumber(13)
  set retryCount($core.int v) { $_setSignedInt32(12, v); }
  @$pb.TagNumber(13)
  $core.bool hasRetryCount() => $_has(12);
  @$pb.TagNumber(13)
  void clearRetryCount() => clearField(13);
}

class RecordMetricsResponse extends $pb.GeneratedMessage {
  factory RecordMetricsResponse({
    $core.bool? recorded,
    $fixnum.Int64? costUsdMicro,
    $core.String? priceVersion,
  }) {
    final $result = create();
    if (recorded != null) {
      $result.recorded = recorded;
    }
    if (costUsdMicro != null) {
      $result.costUsdMicro = costUsdMicro;
    }
    if (priceVersion != null) {
      $result.priceVersion = priceVersion;
    }
    return $result;
  }
  RecordMetricsResponse._() : super();
  factory RecordMetricsResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory RecordMetricsResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'RecordMetricsResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'recorded')
    ..aInt64(2, _omitFieldNames ? '' : 'costUsdMicro')
    ..aOS(3, _omitFieldNames ? '' : 'priceVersion')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  RecordMetricsResponse clone() => RecordMetricsResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  RecordMetricsResponse copyWith(void Function(RecordMetricsResponse) updates) => super.copyWith((message) => updates(message as RecordMetricsResponse)) as RecordMetricsResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static RecordMetricsResponse create() => RecordMetricsResponse._();
  RecordMetricsResponse createEmptyInstance() => create();
  static $pb.PbList<RecordMetricsResponse> createRepeated() => $pb.PbList<RecordMetricsResponse>();
  @$core.pragma('dart2js:noInline')
  static RecordMetricsResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<RecordMetricsResponse>(create);
  static RecordMetricsResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get recorded => $_getBF(0);
  @$pb.TagNumber(1)
  set recorded($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRecorded() => $_has(0);
  @$pb.TagNumber(1)
  void clearRecorded() => clearField(1);

  @$pb.TagNumber(2)
  $fixnum.Int64 get costUsdMicro => $_getI64(1);
  @$pb.TagNumber(2)
  set costUsdMicro($fixnum.Int64 v) { $_setInt64(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasCostUsdMicro() => $_has(1);
  @$pb.TagNumber(2)
  void clearCostUsdMicro() => clearField(2);

  @$pb.TagNumber(3)
  $core.String get priceVersion => $_getSZ(2);
  @$pb.TagNumber(3)
  set priceVersion($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPriceVersion() => $_has(2);
  @$pb.TagNumber(3)
  void clearPriceVersion() => clearField(3);
}

class RecordMetricsBatchRequest extends $pb.GeneratedMessage {
  factory RecordMetricsBatchRequest({
    $core.Iterable<RecordMetricsRequest>? spans,
  }) {
    final $result = create();
    if (spans != null) {
      $result.spans.addAll(spans);
    }
    return $result;
  }
  RecordMetricsBatchRequest._() : super();
  factory RecordMetricsBatchRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory RecordMetricsBatchRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'RecordMetricsBatchRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..pc<RecordMetricsRequest>(1, _omitFieldNames ? '' : 'spans', $pb.PbFieldType.PM, subBuilder: RecordMetricsRequest.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  RecordMetricsBatchRequest clone() => RecordMetricsBatchRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  RecordMetricsBatchRequest copyWith(void Function(RecordMetricsBatchRequest) updates) => super.copyWith((message) => updates(message as RecordMetricsBatchRequest)) as RecordMetricsBatchRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static RecordMetricsBatchRequest create() => RecordMetricsBatchRequest._();
  RecordMetricsBatchRequest createEmptyInstance() => create();
  static $pb.PbList<RecordMetricsBatchRequest> createRepeated() => $pb.PbList<RecordMetricsBatchRequest>();
  @$core.pragma('dart2js:noInline')
  static RecordMetricsBatchRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<RecordMetricsBatchRequest>(create);
  static RecordMetricsBatchRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<RecordMetricsRequest> get spans => $_getList(0);
}

class RecordMetricsBatchResponse extends $pb.GeneratedMessage {
  factory RecordMetricsBatchResponse({
    $core.int? recordedCount,
  }) {
    final $result = create();
    if (recordedCount != null) {
      $result.recordedCount = recordedCount;
    }
    return $result;
  }
  RecordMetricsBatchResponse._() : super();
  factory RecordMetricsBatchResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory RecordMetricsBatchResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'RecordMetricsBatchResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..a<$core.int>(1, _omitFieldNames ? '' : 'recordedCount', $pb.PbFieldType.O3)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  RecordMetricsBatchResponse clone() => RecordMetricsBatchResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  RecordMetricsBatchResponse copyWith(void Function(RecordMetricsBatchResponse) updates) => super.copyWith((message) => updates(message as RecordMetricsBatchResponse)) as RecordMetricsBatchResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static RecordMetricsBatchResponse create() => RecordMetricsBatchResponse._();
  RecordMetricsBatchResponse createEmptyInstance() => create();
  static $pb.PbList<RecordMetricsBatchResponse> createRepeated() => $pb.PbList<RecordMetricsBatchResponse>();
  @$core.pragma('dart2js:noInline')
  static RecordMetricsBatchResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<RecordMetricsBatchResponse>(create);
  static RecordMetricsBatchResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.int get recordedCount => $_getIZ(0);
  @$pb.TagNumber(1)
  set recordedCount($core.int v) { $_setSignedInt32(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRecordedCount() => $_has(0);
  @$pb.TagNumber(1)
  void clearRecordedCount() => clearField(1);
}

class GetEmbeddingRequest extends $pb.GeneratedMessage {
  factory GetEmbeddingRequest({
    $core.String? text,
  }) {
    final $result = create();
    if (text != null) {
      $result.text = text;
    }
    return $result;
  }
  GetEmbeddingRequest._() : super();
  factory GetEmbeddingRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetEmbeddingRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetEmbeddingRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'text')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetEmbeddingRequest clone() => GetEmbeddingRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetEmbeddingRequest copyWith(void Function(GetEmbeddingRequest) updates) => super.copyWith((message) => updates(message as GetEmbeddingRequest)) as GetEmbeddingRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetEmbeddingRequest create() => GetEmbeddingRequest._();
  GetEmbeddingRequest createEmptyInstance() => create();
  static $pb.PbList<GetEmbeddingRequest> createRepeated() => $pb.PbList<GetEmbeddingRequest>();
  @$core.pragma('dart2js:noInline')
  static GetEmbeddingRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetEmbeddingRequest>(create);
  static GetEmbeddingRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get text => $_getSZ(0);
  @$pb.TagNumber(1)
  set text($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasText() => $_has(0);
  @$pb.TagNumber(1)
  void clearText() => clearField(1);
}

class GetEmbeddingResponse extends $pb.GeneratedMessage {
  factory GetEmbeddingResponse({
    $core.Iterable<$core.double>? embedding,
  }) {
    final $result = create();
    if (embedding != null) {
      $result.embedding.addAll(embedding);
    }
    return $result;
  }
  GetEmbeddingResponse._() : super();
  factory GetEmbeddingResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetEmbeddingResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetEmbeddingResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..p<$core.double>(1, _omitFieldNames ? '' : 'embedding', $pb.PbFieldType.KF)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetEmbeddingResponse clone() => GetEmbeddingResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetEmbeddingResponse copyWith(void Function(GetEmbeddingResponse) updates) => super.copyWith((message) => updates(message as GetEmbeddingResponse)) as GetEmbeddingResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetEmbeddingResponse create() => GetEmbeddingResponse._();
  GetEmbeddingResponse createEmptyInstance() => create();
  static $pb.PbList<GetEmbeddingResponse> createRepeated() => $pb.PbList<GetEmbeddingResponse>();
  @$core.pragma('dart2js:noInline')
  static GetEmbeddingResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetEmbeddingResponse>(create);
  static GetEmbeddingResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<$core.double> get embedding => $_getList(0);
}

class InstrumentationControlServiceApi {
  $pb.RpcClient _client;
  InstrumentationControlServiceApi(this._client);

  $async.Future<InitInstrumentationResponse> initInstrumentation($pb.ClientContext? ctx, InitInstrumentationRequest request) =>
    _client.invoke<InitInstrumentationResponse>(ctx, 'InstrumentationControlService', 'InitInstrumentation', request, InitInstrumentationResponse())
  ;
  $async.Future<DisableInstrumentationResponse> disableInstrumentation($pb.ClientContext? ctx, DisableInstrumentationRequest request) =>
    _client.invoke<DisableInstrumentationResponse>(ctx, 'InstrumentationControlService', 'DisableInstrumentation', request, DisableInstrumentationResponse())
  ;
  $async.Future<GetStatusResponse> getStatus($pb.ClientContext? ctx, GetStatusRequest request) =>
    _client.invoke<GetStatusResponse>(ctx, 'InstrumentationControlService', 'GetStatus', request, GetStatusResponse())
  ;
  $async.Future<DetectProviderResponse> detectProvider($pb.ClientContext? ctx, DetectProviderRequest request) =>
    _client.invoke<DetectProviderResponse>(ctx, 'InstrumentationControlService', 'DetectProvider', request, DetectProviderResponse())
  ;
  $async.Future<TriggerTestCallResponse> triggerTestCall($pb.ClientContext? ctx, TriggerTestCallRequest request) =>
    _client.invoke<TriggerTestCallResponse>(ctx, 'InstrumentationControlService', 'TriggerTestCall', request, TriggerTestCallResponse())
  ;
  $async.Future<TriggerTestStreamCallResponse> triggerTestStreamCall($pb.ClientContext? ctx, TriggerTestStreamCallRequest request) =>
    _client.invoke<TriggerTestStreamCallResponse>(ctx, 'InstrumentationControlService', 'TriggerTestStreamCall', request, TriggerTestStreamCallResponse())
  ;
  $async.Future<CountTokensResponse> countTokens($pb.ClientContext? ctx, CountTokensRequest request) =>
    _client.invoke<CountTokensResponse>(ctx, 'InstrumentationControlService', 'CountTokens', request, CountTokensResponse())
  ;
  $async.Future<ScanPiiInjectionResponse> scanPiiInjection($pb.ClientContext? ctx, ScanPiiInjectionRequest request) =>
    _client.invoke<ScanPiiInjectionResponse>(ctx, 'InstrumentationControlService', 'ScanPiiInjection', request, ScanPiiInjectionResponse())
  ;
  $async.Future<ShouldSampleResponse> shouldSample($pb.ClientContext? ctx, ShouldSampleRequest request) =>
    _client.invoke<ShouldSampleResponse>(ctx, 'InstrumentationControlService', 'ShouldSample', request, ShouldSampleResponse())
  ;
  $async.Future<GetEmbeddingResponse> getEmbedding($pb.ClientContext? ctx, GetEmbeddingRequest request) =>
    _client.invoke<GetEmbeddingResponse>(ctx, 'InstrumentationControlService', 'GetEmbedding', request, GetEmbeddingResponse())
  ;
  $async.Future<InitMetricsResponse> initMetrics($pb.ClientContext? ctx, InitMetricsRequest request) =>
    _client.invoke<InitMetricsResponse>(ctx, 'InstrumentationControlService', 'InitMetrics', request, InitMetricsResponse())
  ;
  $async.Future<GetMetricsHealthResponse> getMetricsHealth($pb.ClientContext? ctx, GetMetricsHealthRequest request) =>
    _client.invoke<GetMetricsHealthResponse>(ctx, 'InstrumentationControlService', 'GetMetricsHealth', request, GetMetricsHealthResponse())
  ;
  $async.Future<RecordMetricsResponse> recordMetrics($pb.ClientContext? ctx, RecordMetricsRequest request) =>
    _client.invoke<RecordMetricsResponse>(ctx, 'InstrumentationControlService', 'RecordMetrics', request, RecordMetricsResponse())
  ;
  $async.Future<RecordMetricsBatchResponse> recordMetricsBatch($pb.ClientContext? ctx, RecordMetricsBatchRequest request) =>
    _client.invoke<RecordMetricsBatchResponse>(ctx, 'InstrumentationControlService', 'RecordMetricsBatch', request, RecordMetricsBatchResponse())
  ;
}


const _omitFieldNames = $core.bool.fromEnvironment('protobuf.omit_field_names');
const _omitMessageNames = $core.bool.fromEnvironment('protobuf.omit_message_names');
