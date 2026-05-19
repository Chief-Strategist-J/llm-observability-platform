//
//  Generated code. Do not modify.
//  source: llm/observability/v1/instrumentation.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names
// ignore_for_file: deprecated_member_use_from_same_package, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:async' as $async;
import 'dart:core' as $core;

import 'package:protobuf/protobuf.dart' as $pb;

import 'instrumentation.pb.dart' as $0;
import 'instrumentation.pbjson.dart';

export 'instrumentation.pb.dart';

abstract class InstrumentationControlServiceBase extends $pb.GeneratedService {
  $async.Future<$0.InitInstrumentationResponse> initInstrumentation($pb.ServerContext ctx, $0.InitInstrumentationRequest request);
  $async.Future<$0.DisableInstrumentationResponse> disableInstrumentation($pb.ServerContext ctx, $0.DisableInstrumentationRequest request);
  $async.Future<$0.GetStatusResponse> getStatus($pb.ServerContext ctx, $0.GetStatusRequest request);
  $async.Future<$0.DetectProviderResponse> detectProvider($pb.ServerContext ctx, $0.DetectProviderRequest request);
  $async.Future<$0.TriggerTestCallResponse> triggerTestCall($pb.ServerContext ctx, $0.TriggerTestCallRequest request);
  $async.Future<$0.TriggerTestStreamCallResponse> triggerTestStreamCall($pb.ServerContext ctx, $0.TriggerTestStreamCallRequest request);
  $async.Future<$0.CountTokensResponse> countTokens($pb.ServerContext ctx, $0.CountTokensRequest request);
  $async.Future<$0.ScanPiiInjectionResponse> scanPiiInjection($pb.ServerContext ctx, $0.ScanPiiInjectionRequest request);

  $pb.GeneratedMessage createRequest($core.String methodName) {
    switch (methodName) {
      case 'InitInstrumentation': return $0.InitInstrumentationRequest();
      case 'DisableInstrumentation': return $0.DisableInstrumentationRequest();
      case 'GetStatus': return $0.GetStatusRequest();
      case 'DetectProvider': return $0.DetectProviderRequest();
      case 'TriggerTestCall': return $0.TriggerTestCallRequest();
      case 'TriggerTestStreamCall': return $0.TriggerTestStreamCallRequest();
      case 'CountTokens': return $0.CountTokensRequest();
      case 'ScanPiiInjection': return $0.ScanPiiInjectionRequest();
      default: throw $core.ArgumentError('Unknown method: $methodName');
    }
  }

  $async.Future<$pb.GeneratedMessage> handleCall($pb.ServerContext ctx, $core.String methodName, $pb.GeneratedMessage request) {
    switch (methodName) {
      case 'InitInstrumentation': return this.initInstrumentation(ctx, request as $0.InitInstrumentationRequest);
      case 'DisableInstrumentation': return this.disableInstrumentation(ctx, request as $0.DisableInstrumentationRequest);
      case 'GetStatus': return this.getStatus(ctx, request as $0.GetStatusRequest);
      case 'DetectProvider': return this.detectProvider(ctx, request as $0.DetectProviderRequest);
      case 'TriggerTestCall': return this.triggerTestCall(ctx, request as $0.TriggerTestCallRequest);
      case 'TriggerTestStreamCall': return this.triggerTestStreamCall(ctx, request as $0.TriggerTestStreamCallRequest);
      case 'CountTokens': return this.countTokens(ctx, request as $0.CountTokensRequest);
      case 'ScanPiiInjection': return this.scanPiiInjection(ctx, request as $0.ScanPiiInjectionRequest);
      default: throw $core.ArgumentError('Unknown method: $methodName');
    }
  }

  $core.Map<$core.String, $core.dynamic> get $json => InstrumentationControlServiceBase$json;
  $core.Map<$core.String, $core.Map<$core.String, $core.dynamic>> get $messageJson => InstrumentationControlServiceBase$messageJson;
}

