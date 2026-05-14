//
//  Generated code. Do not modify.
//  source: llm/observability/v1/span.proto
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

import 'span.pbenum.dart';

export 'span.pbenum.dart';

/// LLMSpan represents a single, raw observability span for an LLM call.
class LLMSpan extends $pb.GeneratedMessage {
  factory LLMSpan({
    $core.String? spanId,
    $core.String? traceId,
    $core.String? parentSpanId,
    $core.int? schemaVersion,
    $core.String? model,
    $core.String? provider,
    $core.String? serviceName,
    $core.String? endpoint,
    Environment? environment,
    $core.String? userId,
    $core.String? sessionId,
    $core.int? promptTokens,
    $core.int? completionTokens,
    $core.int? latencyMsTtft,
    $core.int? latencyMsTotal,
    FinishReason? finishReason,
    $fixnum.Int64? costUsdMicro,
    $core.String? priceVersion,
    TokenCountMethod? tokenCountMethod,
    $core.bool? isSampled,
    $core.int? retryCount,
    $core.Iterable<$core.String>? attemptedModels,
    $core.bool? piiDetected,
    $core.bool? injectionAttempt,
    $core.String? timestampUtc,
    $core.String? promptHash,
    $core.Iterable<$core.double>? promptEmbedding,
    $core.Iterable<$core.double>? responseEmbedding,
  }) {
    final $result = create();
    if (spanId != null) {
      $result.spanId = spanId;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentSpanId != null) {
      $result.parentSpanId = parentSpanId;
    }
    if (schemaVersion != null) {
      $result.schemaVersion = schemaVersion;
    }
    if (model != null) {
      $result.model = model;
    }
    if (provider != null) {
      $result.provider = provider;
    }
    if (serviceName != null) {
      $result.serviceName = serviceName;
    }
    if (endpoint != null) {
      $result.endpoint = endpoint;
    }
    if (environment != null) {
      $result.environment = environment;
    }
    if (userId != null) {
      $result.userId = userId;
    }
    if (sessionId != null) {
      $result.sessionId = sessionId;
    }
    if (promptTokens != null) {
      $result.promptTokens = promptTokens;
    }
    if (completionTokens != null) {
      $result.completionTokens = completionTokens;
    }
    if (latencyMsTtft != null) {
      $result.latencyMsTtft = latencyMsTtft;
    }
    if (latencyMsTotal != null) {
      $result.latencyMsTotal = latencyMsTotal;
    }
    if (finishReason != null) {
      $result.finishReason = finishReason;
    }
    if (costUsdMicro != null) {
      $result.costUsdMicro = costUsdMicro;
    }
    if (priceVersion != null) {
      $result.priceVersion = priceVersion;
    }
    if (tokenCountMethod != null) {
      $result.tokenCountMethod = tokenCountMethod;
    }
    if (isSampled != null) {
      $result.isSampled = isSampled;
    }
    if (retryCount != null) {
      $result.retryCount = retryCount;
    }
    if (attemptedModels != null) {
      $result.attemptedModels.addAll(attemptedModels);
    }
    if (piiDetected != null) {
      $result.piiDetected = piiDetected;
    }
    if (injectionAttempt != null) {
      $result.injectionAttempt = injectionAttempt;
    }
    if (timestampUtc != null) {
      $result.timestampUtc = timestampUtc;
    }
    if (promptHash != null) {
      $result.promptHash = promptHash;
    }
    if (promptEmbedding != null) {
      $result.promptEmbedding.addAll(promptEmbedding);
    }
    if (responseEmbedding != null) {
      $result.responseEmbedding.addAll(responseEmbedding);
    }
    return $result;
  }
  LLMSpan._() : super();
  factory LLMSpan.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory LLMSpan.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'LLMSpan', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'spanId')
    ..aOS(2, _omitFieldNames ? '' : 'traceId')
    ..aOS(3, _omitFieldNames ? '' : 'parentSpanId')
    ..a<$core.int>(4, _omitFieldNames ? '' : 'schemaVersion', $pb.PbFieldType.O3)
    ..aOS(5, _omitFieldNames ? '' : 'model')
    ..aOS(6, _omitFieldNames ? '' : 'provider')
    ..aOS(7, _omitFieldNames ? '' : 'serviceName')
    ..aOS(8, _omitFieldNames ? '' : 'endpoint')
    ..e<Environment>(9, _omitFieldNames ? '' : 'environment', $pb.PbFieldType.OE, defaultOrMaker: Environment.ENVIRONMENT_UNSPECIFIED, valueOf: Environment.valueOf, enumValues: Environment.values)
    ..aOS(10, _omitFieldNames ? '' : 'userId')
    ..aOS(11, _omitFieldNames ? '' : 'sessionId')
    ..a<$core.int>(12, _omitFieldNames ? '' : 'promptTokens', $pb.PbFieldType.O3)
    ..a<$core.int>(13, _omitFieldNames ? '' : 'completionTokens', $pb.PbFieldType.O3)
    ..a<$core.int>(14, _omitFieldNames ? '' : 'latencyMsTtft', $pb.PbFieldType.O3)
    ..a<$core.int>(15, _omitFieldNames ? '' : 'latencyMsTotal', $pb.PbFieldType.O3)
    ..e<FinishReason>(16, _omitFieldNames ? '' : 'finishReason', $pb.PbFieldType.OE, defaultOrMaker: FinishReason.FINISH_REASON_UNSPECIFIED, valueOf: FinishReason.valueOf, enumValues: FinishReason.values)
    ..aInt64(17, _omitFieldNames ? '' : 'costUsdMicro')
    ..aOS(18, _omitFieldNames ? '' : 'priceVersion')
    ..e<TokenCountMethod>(19, _omitFieldNames ? '' : 'tokenCountMethod', $pb.PbFieldType.OE, defaultOrMaker: TokenCountMethod.TOKEN_COUNT_METHOD_UNSPECIFIED, valueOf: TokenCountMethod.valueOf, enumValues: TokenCountMethod.values)
    ..aOB(20, _omitFieldNames ? '' : 'isSampled')
    ..a<$core.int>(21, _omitFieldNames ? '' : 'retryCount', $pb.PbFieldType.O3)
    ..pPS(22, _omitFieldNames ? '' : 'attemptedModels')
    ..aOB(23, _omitFieldNames ? '' : 'piiDetected')
    ..aOB(24, _omitFieldNames ? '' : 'injectionAttempt')
    ..aOS(25, _omitFieldNames ? '' : 'timestampUtc')
    ..aOS(26, _omitFieldNames ? '' : 'promptHash')
    ..p<$core.double>(27, _omitFieldNames ? '' : 'promptEmbedding', $pb.PbFieldType.KF)
    ..p<$core.double>(28, _omitFieldNames ? '' : 'responseEmbedding', $pb.PbFieldType.KF)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  LLMSpan clone() => LLMSpan()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  LLMSpan copyWith(void Function(LLMSpan) updates) => super.copyWith((message) => updates(message as LLMSpan)) as LLMSpan;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static LLMSpan create() => LLMSpan._();
  LLMSpan createEmptyInstance() => create();
  static $pb.PbList<LLMSpan> createRepeated() => $pb.PbList<LLMSpan>();
  @$core.pragma('dart2js:noInline')
  static LLMSpan getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<LLMSpan>(create);
  static LLMSpan? _defaultInstance;

  /// Generated before API call (UUID v4)
  @$pb.TagNumber(1)
  $core.String get spanId => $_getSZ(0);
  @$pb.TagNumber(1)
  set spanId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSpanId() => $_has(0);
  @$pb.TagNumber(1)
  void clearSpanId() => clearField(1);

  /// Propagated from caller (UUID v4), nullable
  @$pb.TagNumber(2)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(2)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(2)
  void clearTraceId() => clearField(2);

  /// For tool-call chains (UUID v4), nullable
  @$pb.TagNumber(3)
  $core.String get parentSpanId => $_getSZ(2);
  @$pb.TagNumber(3)
  set parentSpanId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasParentSpanId() => $_has(2);
  @$pb.TagNumber(3)
  void clearParentSpanId() => clearField(3);

  /// Bump on breaking change. Hardcoded = 1
  @$pb.TagNumber(4)
  $core.int get schemaVersion => $_getIZ(3);
  @$pb.TagNumber(4)
  set schemaVersion($core.int v) { $_setSignedInt32(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasSchemaVersion() => $_has(3);
  @$pb.TagNumber(4)
  void clearSchemaVersion() => clearField(4);

  /// SDK config ('gpt-4o', etc)
  @$pb.TagNumber(5)
  $core.String get model => $_getSZ(4);
  @$pb.TagNumber(5)
  set model($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasModel() => $_has(4);
  @$pb.TagNumber(5)
  void clearModel() => clearField(5);

  /// SDK config ('openai', 'anthropic', etc)
  @$pb.TagNumber(6)
  $core.String get provider => $_getSZ(5);
  @$pb.TagNumber(6)
  set provider($core.String v) { $_setString(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasProvider() => $_has(5);
  @$pb.TagNumber(6)
  void clearProvider() => clearField(6);

  /// SDK config ('checkout-service')
  @$pb.TagNumber(7)
  $core.String get serviceName => $_getSZ(6);
  @$pb.TagNumber(7)
  set serviceName($core.String v) { $_setString(6, v); }
  @$pb.TagNumber(7)
  $core.bool hasServiceName() => $_has(6);
  @$pb.TagNumber(7)
  void clearServiceName() => clearField(7);

  /// SDK decorator arg ('/api/summarize')
  @$pb.TagNumber(8)
  $core.String get endpoint => $_getSZ(7);
  @$pb.TagNumber(8)
  set endpoint($core.String v) { $_setString(7, v); }
  @$pb.TagNumber(8)
  $core.bool hasEndpoint() => $_has(7);
  @$pb.TagNumber(8)
  void clearEndpoint() => clearField(8);

  /// SDK config
  @$pb.TagNumber(9)
  Environment get environment => $_getN(8);
  @$pb.TagNumber(9)
  set environment(Environment v) { setField(9, v); }
  @$pb.TagNumber(9)
  $core.bool hasEnvironment() => $_has(8);
  @$pb.TagNumber(9)
  void clearEnvironment() => clearField(9);

  /// SDK call arg. Null for anonymous
  @$pb.TagNumber(10)
  $core.String get userId => $_getSZ(9);
  @$pb.TagNumber(10)
  set userId($core.String v) { $_setString(9, v); }
  @$pb.TagNumber(10)
  $core.bool hasUserId() => $_has(9);
  @$pb.TagNumber(10)
  void clearUserId() => clearField(10);

  /// SDK call arg. Null for stateless
  @$pb.TagNumber(11)
  $core.String get sessionId => $_getSZ(10);
  @$pb.TagNumber(11)
  set sessionId($core.String v) { $_setString(10, v); }
  @$pb.TagNumber(11)
  $core.bool hasSessionId() => $_has(10);
  @$pb.TagNumber(11)
  void clearSessionId() => clearField(11);

  /// Exact BPE count, > 0
  @$pb.TagNumber(12)
  $core.int get promptTokens => $_getIZ(11);
  @$pb.TagNumber(12)
  set promptTokens($core.int v) { $_setSignedInt32(11, v); }
  @$pb.TagNumber(12)
  $core.bool hasPromptTokens() => $_has(11);
  @$pb.TagNumber(12)
  void clearPromptTokens() => clearField(12);

  /// Exact BPE count, >= 0
  @$pb.TagNumber(13)
  $core.int get completionTokens => $_getIZ(12);
  @$pb.TagNumber(13)
  set completionTokens($core.int v) { $_setSignedInt32(12, v); }
  @$pb.TagNumber(13)
  $core.bool hasCompletionTokens() => $_has(12);
  @$pb.TagNumber(13)
  void clearCompletionTokens() => clearField(13);

  /// Time to first chunk byte
  @$pb.TagNumber(14)
  $core.int get latencyMsTtft => $_getIZ(13);
  @$pb.TagNumber(14)
  set latencyMsTtft($core.int v) { $_setSignedInt32(13, v); }
  @$pb.TagNumber(14)
  $core.bool hasLatencyMsTtft() => $_has(13);
  @$pb.TagNumber(14)
  void clearLatencyMsTtft() => clearField(14);

  /// Full wall clock, > 0
  @$pb.TagNumber(15)
  $core.int get latencyMsTotal => $_getIZ(14);
  @$pb.TagNumber(15)
  set latencyMsTotal($core.int v) { $_setSignedInt32(14, v); }
  @$pb.TagNumber(15)
  $core.bool hasLatencyMsTotal() => $_has(14);
  @$pb.TagNumber(15)
  void clearLatencyMsTotal() => clearField(15);

  /// Provider response finish reason
  @$pb.TagNumber(16)
  FinishReason get finishReason => $_getN(15);
  @$pb.TagNumber(16)
  set finishReason(FinishReason v) { setField(16, v); }
  @$pb.TagNumber(16)
  $core.bool hasFinishReason() => $_has(15);
  @$pb.TagNumber(16)
  void clearFinishReason() => clearField(16);

  /// SDK computed cost in micro-USD, >= 0
  @$pb.TagNumber(17)
  $fixnum.Int64 get costUsdMicro => $_getI64(16);
  @$pb.TagNumber(17)
  set costUsdMicro($fixnum.Int64 v) { $_setInt64(16, v); }
  @$pb.TagNumber(17)
  $core.bool hasCostUsdMicro() => $_has(16);
  @$pb.TagNumber(17)
  void clearCostUsdMicro() => clearField(17);

  /// SDK config price version date
  @$pb.TagNumber(18)
  $core.String get priceVersion => $_getSZ(17);
  @$pb.TagNumber(18)
  set priceVersion($core.String v) { $_setString(17, v); }
  @$pb.TagNumber(18)
  $core.bool hasPriceVersion() => $_has(17);
  @$pb.TagNumber(18)
  void clearPriceVersion() => clearField(18);

  /// SDK token method
  @$pb.TagNumber(19)
  TokenCountMethod get tokenCountMethod => $_getN(18);
  @$pb.TagNumber(19)
  set tokenCountMethod(TokenCountMethod v) { setField(19, v); }
  @$pb.TagNumber(19)
  $core.bool hasTokenCountMethod() => $_has(18);
  @$pb.TagNumber(19)
  void clearTokenCountMethod() => clearField(19);

  /// TRUE if hash(span_id) % 100 == 0
  @$pb.TagNumber(20)
  $core.bool get isSampled => $_getBF(19);
  @$pb.TagNumber(20)
  set isSampled($core.bool v) { $_setBool(19, v); }
  @$pb.TagNumber(20)
  $core.bool hasIsSampled() => $_has(19);
  @$pb.TagNumber(20)
  void clearIsSampled() => clearField(20);

  /// 0 for first-attempt calls
  @$pb.TagNumber(21)
  $core.int get retryCount => $_getIZ(20);
  @$pb.TagNumber(21)
  set retryCount($core.int v) { $_setSignedInt32(20, v); }
  @$pb.TagNumber(21)
  $core.bool hasRetryCount() => $_has(20);
  @$pb.TagNumber(21)
  void clearRetryCount() => clearField(21);

  /// Fallback chains
  @$pb.TagNumber(22)
  $core.List<$core.String> get attemptedModels => $_getList(21);

  /// Aho-Corasick computed inline before emit
  @$pb.TagNumber(23)
  $core.bool get piiDetected => $_getBF(22);
  @$pb.TagNumber(23)
  set piiDetected($core.bool v) { $_setBool(22, v); }
  @$pb.TagNumber(23)
  $core.bool hasPiiDetected() => $_has(22);
  @$pb.TagNumber(23)
  void clearPiiDetected() => clearField(23);

  /// Aho-Corasick jailbreak/injection pattern matched
  @$pb.TagNumber(24)
  $core.bool get injectionAttempt => $_getBF(23);
  @$pb.TagNumber(24)
  set injectionAttempt($core.bool v) { $_setBool(23, v); }
  @$pb.TagNumber(24)
  $core.bool hasInjectionAttempt() => $_has(23);
  @$pb.TagNumber(24)
  void clearInjectionAttempt() => clearField(24);

  /// SDK (client clock) UTC, ISO 8601 string or Unix nanoseconds.
  @$pb.TagNumber(25)
  $core.String get timestampUtc => $_getSZ(24);
  @$pb.TagNumber(25)
  set timestampUtc($core.String v) { $_setString(24, v); }
  @$pb.TagNumber(25)
  $core.bool hasTimestampUtc() => $_has(24);
  @$pb.TagNumber(25)
  void clearTimestampUtc() => clearField(25);

  /// SAMPLED-ONLY FIELDS
  /// SHA256(prompt_text) 64-char hex. Null if pii_detected.
  @$pb.TagNumber(26)
  $core.String get promptHash => $_getSZ(25);
  @$pb.TagNumber(26)
  set promptHash($core.String v) { $_setString(25, v); }
  @$pb.TagNumber(26)
  $core.bool hasPromptHash() => $_has(25);
  @$pb.TagNumber(26)
  void clearPromptHash() => clearField(26);

  /// MiniLM-L6-v2 384-dim vector. Null if pii_detected.
  @$pb.TagNumber(27)
  $core.List<$core.double> get promptEmbedding => $_getList(26);

  /// MiniLM-L6-v2 384-dim vector. Null if pii_detected.
  @$pb.TagNumber(28)
  $core.List<$core.double> get responseEmbedding => $_getList(27);
}

class RecordSpanRequest extends $pb.GeneratedMessage {
  factory RecordSpanRequest({
    LLMSpan? span,
  }) {
    final $result = create();
    if (span != null) {
      $result.span = span;
    }
    return $result;
  }
  RecordSpanRequest._() : super();
  factory RecordSpanRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory RecordSpanRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'RecordSpanRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOM<LLMSpan>(1, _omitFieldNames ? '' : 'span', subBuilder: LLMSpan.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  RecordSpanRequest clone() => RecordSpanRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  RecordSpanRequest copyWith(void Function(RecordSpanRequest) updates) => super.copyWith((message) => updates(message as RecordSpanRequest)) as RecordSpanRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static RecordSpanRequest create() => RecordSpanRequest._();
  RecordSpanRequest createEmptyInstance() => create();
  static $pb.PbList<RecordSpanRequest> createRepeated() => $pb.PbList<RecordSpanRequest>();
  @$core.pragma('dart2js:noInline')
  static RecordSpanRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<RecordSpanRequest>(create);
  static RecordSpanRequest? _defaultInstance;

  @$pb.TagNumber(1)
  LLMSpan get span => $_getN(0);
  @$pb.TagNumber(1)
  set span(LLMSpan v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasSpan() => $_has(0);
  @$pb.TagNumber(1)
  void clearSpan() => clearField(1);
  @$pb.TagNumber(1)
  LLMSpan ensureSpan() => $_ensure(0);
}

class RecordSpanResponse extends $pb.GeneratedMessage {
  factory RecordSpanResponse({
    $core.bool? success,
    $core.Iterable<$core.String>? spanWarnings,
  }) {
    final $result = create();
    if (success != null) {
      $result.success = success;
    }
    if (spanWarnings != null) {
      $result.spanWarnings.addAll(spanWarnings);
    }
    return $result;
  }
  RecordSpanResponse._() : super();
  factory RecordSpanResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory RecordSpanResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'RecordSpanResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'llm.observability.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'success')
    ..pPS(2, _omitFieldNames ? '' : 'spanWarnings')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  RecordSpanResponse clone() => RecordSpanResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  RecordSpanResponse copyWith(void Function(RecordSpanResponse) updates) => super.copyWith((message) => updates(message as RecordSpanResponse)) as RecordSpanResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static RecordSpanResponse create() => RecordSpanResponse._();
  RecordSpanResponse createEmptyInstance() => create();
  static $pb.PbList<RecordSpanResponse> createRepeated() => $pb.PbList<RecordSpanResponse>();
  @$core.pragma('dart2js:noInline')
  static RecordSpanResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<RecordSpanResponse>(create);
  static RecordSpanResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.bool get success => $_getBF(0);
  @$pb.TagNumber(1)
  set success($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSuccess() => $_has(0);
  @$pb.TagNumber(1)
  void clearSuccess() => clearField(1);

  @$pb.TagNumber(2)
  $core.List<$core.String> get spanWarnings => $_getList(1);
}

class SpanIngestionServiceApi {
  $pb.RpcClient _client;
  SpanIngestionServiceApi(this._client);

  $async.Future<RecordSpanResponse> recordSpan($pb.ClientContext? ctx, RecordSpanRequest request) =>
    _client.invoke<RecordSpanResponse>(ctx, 'SpanIngestionService', 'RecordSpan', request, RecordSpanResponse())
  ;
}


const _omitFieldNames = $core.bool.fromEnvironment('protobuf.omit_field_names');
const _omitMessageNames = $core.bool.fromEnvironment('protobuf.omit_message_names');
