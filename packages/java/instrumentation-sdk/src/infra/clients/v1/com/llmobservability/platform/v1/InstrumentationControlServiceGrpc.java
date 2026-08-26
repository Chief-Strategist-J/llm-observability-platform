package com.llmobservability.platform.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 * <pre>
 * Service definition for remote instrumentation control
 * </pre>
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.60.0)",
    comments = "Source: llm/observability/v1/instrumentation.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class InstrumentationControlServiceGrpc {

  private InstrumentationControlServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "llm.observability.v1.InstrumentationControlService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.InitInstrumentationRequest,
      com.llmobservability.platform.v1.InitInstrumentationResponse> getInitInstrumentationMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "InitInstrumentation",
      requestType = com.llmobservability.platform.v1.InitInstrumentationRequest.class,
      responseType = com.llmobservability.platform.v1.InitInstrumentationResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.InitInstrumentationRequest,
      com.llmobservability.platform.v1.InitInstrumentationResponse> getInitInstrumentationMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.InitInstrumentationRequest, com.llmobservability.platform.v1.InitInstrumentationResponse> getInitInstrumentationMethod;
    if ((getInitInstrumentationMethod = InstrumentationControlServiceGrpc.getInitInstrumentationMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getInitInstrumentationMethod = InstrumentationControlServiceGrpc.getInitInstrumentationMethod) == null) {
          InstrumentationControlServiceGrpc.getInitInstrumentationMethod = getInitInstrumentationMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.InitInstrumentationRequest, com.llmobservability.platform.v1.InitInstrumentationResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "InitInstrumentation"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.InitInstrumentationRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.InitInstrumentationResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("InitInstrumentation"))
              .build();
        }
      }
    }
    return getInitInstrumentationMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.DisableInstrumentationRequest,
      com.llmobservability.platform.v1.DisableInstrumentationResponse> getDisableInstrumentationMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "DisableInstrumentation",
      requestType = com.llmobservability.platform.v1.DisableInstrumentationRequest.class,
      responseType = com.llmobservability.platform.v1.DisableInstrumentationResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.DisableInstrumentationRequest,
      com.llmobservability.platform.v1.DisableInstrumentationResponse> getDisableInstrumentationMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.DisableInstrumentationRequest, com.llmobservability.platform.v1.DisableInstrumentationResponse> getDisableInstrumentationMethod;
    if ((getDisableInstrumentationMethod = InstrumentationControlServiceGrpc.getDisableInstrumentationMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getDisableInstrumentationMethod = InstrumentationControlServiceGrpc.getDisableInstrumentationMethod) == null) {
          InstrumentationControlServiceGrpc.getDisableInstrumentationMethod = getDisableInstrumentationMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.DisableInstrumentationRequest, com.llmobservability.platform.v1.DisableInstrumentationResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "DisableInstrumentation"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.DisableInstrumentationRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.DisableInstrumentationResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("DisableInstrumentation"))
              .build();
        }
      }
    }
    return getDisableInstrumentationMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetStatusRequest,
      com.llmobservability.platform.v1.GetStatusResponse> getGetStatusMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetStatus",
      requestType = com.llmobservability.platform.v1.GetStatusRequest.class,
      responseType = com.llmobservability.platform.v1.GetStatusResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetStatusRequest,
      com.llmobservability.platform.v1.GetStatusResponse> getGetStatusMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetStatusRequest, com.llmobservability.platform.v1.GetStatusResponse> getGetStatusMethod;
    if ((getGetStatusMethod = InstrumentationControlServiceGrpc.getGetStatusMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getGetStatusMethod = InstrumentationControlServiceGrpc.getGetStatusMethod) == null) {
          InstrumentationControlServiceGrpc.getGetStatusMethod = getGetStatusMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.GetStatusRequest, com.llmobservability.platform.v1.GetStatusResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetStatus"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.GetStatusRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.GetStatusResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("GetStatus"))
              .build();
        }
      }
    }
    return getGetStatusMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.DetectProviderRequest,
      com.llmobservability.platform.v1.DetectProviderResponse> getDetectProviderMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "DetectProvider",
      requestType = com.llmobservability.platform.v1.DetectProviderRequest.class,
      responseType = com.llmobservability.platform.v1.DetectProviderResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.DetectProviderRequest,
      com.llmobservability.platform.v1.DetectProviderResponse> getDetectProviderMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.DetectProviderRequest, com.llmobservability.platform.v1.DetectProviderResponse> getDetectProviderMethod;
    if ((getDetectProviderMethod = InstrumentationControlServiceGrpc.getDetectProviderMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getDetectProviderMethod = InstrumentationControlServiceGrpc.getDetectProviderMethod) == null) {
          InstrumentationControlServiceGrpc.getDetectProviderMethod = getDetectProviderMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.DetectProviderRequest, com.llmobservability.platform.v1.DetectProviderResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "DetectProvider"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.DetectProviderRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.DetectProviderResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("DetectProvider"))
              .build();
        }
      }
    }
    return getDetectProviderMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TriggerTestCallRequest,
      com.llmobservability.platform.v1.TriggerTestCallResponse> getTriggerTestCallMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "TriggerTestCall",
      requestType = com.llmobservability.platform.v1.TriggerTestCallRequest.class,
      responseType = com.llmobservability.platform.v1.TriggerTestCallResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TriggerTestCallRequest,
      com.llmobservability.platform.v1.TriggerTestCallResponse> getTriggerTestCallMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TriggerTestCallRequest, com.llmobservability.platform.v1.TriggerTestCallResponse> getTriggerTestCallMethod;
    if ((getTriggerTestCallMethod = InstrumentationControlServiceGrpc.getTriggerTestCallMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getTriggerTestCallMethod = InstrumentationControlServiceGrpc.getTriggerTestCallMethod) == null) {
          InstrumentationControlServiceGrpc.getTriggerTestCallMethod = getTriggerTestCallMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.TriggerTestCallRequest, com.llmobservability.platform.v1.TriggerTestCallResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "TriggerTestCall"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.TriggerTestCallRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.TriggerTestCallResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("TriggerTestCall"))
              .build();
        }
      }
    }
    return getTriggerTestCallMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TriggerTestStreamCallRequest,
      com.llmobservability.platform.v1.TriggerTestStreamCallResponse> getTriggerTestStreamCallMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "TriggerTestStreamCall",
      requestType = com.llmobservability.platform.v1.TriggerTestStreamCallRequest.class,
      responseType = com.llmobservability.platform.v1.TriggerTestStreamCallResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TriggerTestStreamCallRequest,
      com.llmobservability.platform.v1.TriggerTestStreamCallResponse> getTriggerTestStreamCallMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TriggerTestStreamCallRequest, com.llmobservability.platform.v1.TriggerTestStreamCallResponse> getTriggerTestStreamCallMethod;
    if ((getTriggerTestStreamCallMethod = InstrumentationControlServiceGrpc.getTriggerTestStreamCallMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getTriggerTestStreamCallMethod = InstrumentationControlServiceGrpc.getTriggerTestStreamCallMethod) == null) {
          InstrumentationControlServiceGrpc.getTriggerTestStreamCallMethod = getTriggerTestStreamCallMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.TriggerTestStreamCallRequest, com.llmobservability.platform.v1.TriggerTestStreamCallResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "TriggerTestStreamCall"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.TriggerTestStreamCallRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.TriggerTestStreamCallResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("TriggerTestStreamCall"))
              .build();
        }
      }
    }
    return getTriggerTestStreamCallMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.CountTokensRequest,
      com.llmobservability.platform.v1.CountTokensResponse> getCountTokensMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CountTokens",
      requestType = com.llmobservability.platform.v1.CountTokensRequest.class,
      responseType = com.llmobservability.platform.v1.CountTokensResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.CountTokensRequest,
      com.llmobservability.platform.v1.CountTokensResponse> getCountTokensMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.CountTokensRequest, com.llmobservability.platform.v1.CountTokensResponse> getCountTokensMethod;
    if ((getCountTokensMethod = InstrumentationControlServiceGrpc.getCountTokensMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getCountTokensMethod = InstrumentationControlServiceGrpc.getCountTokensMethod) == null) {
          InstrumentationControlServiceGrpc.getCountTokensMethod = getCountTokensMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.CountTokensRequest, com.llmobservability.platform.v1.CountTokensResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CountTokens"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.CountTokensRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.CountTokensResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("CountTokens"))
              .build();
        }
      }
    }
    return getCountTokensMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ScanPiiInjectionRequest,
      com.llmobservability.platform.v1.ScanPiiInjectionResponse> getScanPiiInjectionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ScanPiiInjection",
      requestType = com.llmobservability.platform.v1.ScanPiiInjectionRequest.class,
      responseType = com.llmobservability.platform.v1.ScanPiiInjectionResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ScanPiiInjectionRequest,
      com.llmobservability.platform.v1.ScanPiiInjectionResponse> getScanPiiInjectionMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ScanPiiInjectionRequest, com.llmobservability.platform.v1.ScanPiiInjectionResponse> getScanPiiInjectionMethod;
    if ((getScanPiiInjectionMethod = InstrumentationControlServiceGrpc.getScanPiiInjectionMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getScanPiiInjectionMethod = InstrumentationControlServiceGrpc.getScanPiiInjectionMethod) == null) {
          InstrumentationControlServiceGrpc.getScanPiiInjectionMethod = getScanPiiInjectionMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.ScanPiiInjectionRequest, com.llmobservability.platform.v1.ScanPiiInjectionResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ScanPiiInjection"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ScanPiiInjectionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ScanPiiInjectionResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("ScanPiiInjection"))
              .build();
        }
      }
    }
    return getScanPiiInjectionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ShouldSampleRequest,
      com.llmobservability.platform.v1.ShouldSampleResponse> getShouldSampleMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ShouldSample",
      requestType = com.llmobservability.platform.v1.ShouldSampleRequest.class,
      responseType = com.llmobservability.platform.v1.ShouldSampleResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ShouldSampleRequest,
      com.llmobservability.platform.v1.ShouldSampleResponse> getShouldSampleMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ShouldSampleRequest, com.llmobservability.platform.v1.ShouldSampleResponse> getShouldSampleMethod;
    if ((getShouldSampleMethod = InstrumentationControlServiceGrpc.getShouldSampleMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getShouldSampleMethod = InstrumentationControlServiceGrpc.getShouldSampleMethod) == null) {
          InstrumentationControlServiceGrpc.getShouldSampleMethod = getShouldSampleMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.ShouldSampleRequest, com.llmobservability.platform.v1.ShouldSampleResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ShouldSample"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ShouldSampleRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ShouldSampleResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("ShouldSample"))
              .build();
        }
      }
    }
    return getShouldSampleMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetEmbeddingRequest,
      com.llmobservability.platform.v1.GetEmbeddingResponse> getGetEmbeddingMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetEmbedding",
      requestType = com.llmobservability.platform.v1.GetEmbeddingRequest.class,
      responseType = com.llmobservability.platform.v1.GetEmbeddingResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetEmbeddingRequest,
      com.llmobservability.platform.v1.GetEmbeddingResponse> getGetEmbeddingMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetEmbeddingRequest, com.llmobservability.platform.v1.GetEmbeddingResponse> getGetEmbeddingMethod;
    if ((getGetEmbeddingMethod = InstrumentationControlServiceGrpc.getGetEmbeddingMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getGetEmbeddingMethod = InstrumentationControlServiceGrpc.getGetEmbeddingMethod) == null) {
          InstrumentationControlServiceGrpc.getGetEmbeddingMethod = getGetEmbeddingMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.GetEmbeddingRequest, com.llmobservability.platform.v1.GetEmbeddingResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetEmbedding"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.GetEmbeddingRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.GetEmbeddingResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("GetEmbedding"))
              .build();
        }
      }
    }
    return getGetEmbeddingMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TrackFallbackRequest,
      com.llmobservability.platform.v1.TrackFallbackResponse> getTrackFallbackMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "TrackFallback",
      requestType = com.llmobservability.platform.v1.TrackFallbackRequest.class,
      responseType = com.llmobservability.platform.v1.TrackFallbackResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TrackFallbackRequest,
      com.llmobservability.platform.v1.TrackFallbackResponse> getTrackFallbackMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TrackFallbackRequest, com.llmobservability.platform.v1.TrackFallbackResponse> getTrackFallbackMethod;
    if ((getTrackFallbackMethod = InstrumentationControlServiceGrpc.getTrackFallbackMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getTrackFallbackMethod = InstrumentationControlServiceGrpc.getTrackFallbackMethod) == null) {
          InstrumentationControlServiceGrpc.getTrackFallbackMethod = getTrackFallbackMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.TrackFallbackRequest, com.llmobservability.platform.v1.TrackFallbackResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "TrackFallback"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.TrackFallbackRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.TrackFallbackResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("TrackFallback"))
              .build();
        }
      }
    }
    return getTrackFallbackMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ClearFallbackTrackerRequest,
      com.llmobservability.platform.v1.ClearFallbackTrackerResponse> getClearFallbackTrackerMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ClearFallbackTracker",
      requestType = com.llmobservability.platform.v1.ClearFallbackTrackerRequest.class,
      responseType = com.llmobservability.platform.v1.ClearFallbackTrackerResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ClearFallbackTrackerRequest,
      com.llmobservability.platform.v1.ClearFallbackTrackerResponse> getClearFallbackTrackerMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ClearFallbackTrackerRequest, com.llmobservability.platform.v1.ClearFallbackTrackerResponse> getClearFallbackTrackerMethod;
    if ((getClearFallbackTrackerMethod = InstrumentationControlServiceGrpc.getClearFallbackTrackerMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getClearFallbackTrackerMethod = InstrumentationControlServiceGrpc.getClearFallbackTrackerMethod) == null) {
          InstrumentationControlServiceGrpc.getClearFallbackTrackerMethod = getClearFallbackTrackerMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.ClearFallbackTrackerRequest, com.llmobservability.platform.v1.ClearFallbackTrackerResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ClearFallbackTracker"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ClearFallbackTrackerRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ClearFallbackTrackerResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("ClearFallbackTracker"))
              .build();
        }
      }
    }
    return getClearFallbackTrackerMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TrackToolCallRequest,
      com.llmobservability.platform.v1.TrackToolCallResponse> getTrackToolCallMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "TrackToolCall",
      requestType = com.llmobservability.platform.v1.TrackToolCallRequest.class,
      responseType = com.llmobservability.platform.v1.TrackToolCallResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TrackToolCallRequest,
      com.llmobservability.platform.v1.TrackToolCallResponse> getTrackToolCallMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.TrackToolCallRequest, com.llmobservability.platform.v1.TrackToolCallResponse> getTrackToolCallMethod;
    if ((getTrackToolCallMethod = InstrumentationControlServiceGrpc.getTrackToolCallMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getTrackToolCallMethod = InstrumentationControlServiceGrpc.getTrackToolCallMethod) == null) {
          InstrumentationControlServiceGrpc.getTrackToolCallMethod = getTrackToolCallMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.TrackToolCallRequest, com.llmobservability.platform.v1.TrackToolCallResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "TrackToolCall"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.TrackToolCallRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.TrackToolCallResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("TrackToolCall"))
              .build();
        }
      }
    }
    return getTrackToolCallMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ClearToolCallTrackerRequest,
      com.llmobservability.platform.v1.ClearToolCallTrackerResponse> getClearToolCallTrackerMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ClearToolCallTracker",
      requestType = com.llmobservability.platform.v1.ClearToolCallTrackerRequest.class,
      responseType = com.llmobservability.platform.v1.ClearToolCallTrackerResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ClearToolCallTrackerRequest,
      com.llmobservability.platform.v1.ClearToolCallTrackerResponse> getClearToolCallTrackerMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ClearToolCallTrackerRequest, com.llmobservability.platform.v1.ClearToolCallTrackerResponse> getClearToolCallTrackerMethod;
    if ((getClearToolCallTrackerMethod = InstrumentationControlServiceGrpc.getClearToolCallTrackerMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getClearToolCallTrackerMethod = InstrumentationControlServiceGrpc.getClearToolCallTrackerMethod) == null) {
          InstrumentationControlServiceGrpc.getClearToolCallTrackerMethod = getClearToolCallTrackerMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.ClearToolCallTrackerRequest, com.llmobservability.platform.v1.ClearToolCallTrackerResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ClearToolCallTracker"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ClearToolCallTrackerRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ClearToolCallTrackerResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("ClearToolCallTracker"))
              .build();
        }
      }
    }
    return getClearToolCallTrackerMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.InitMetricsRequest,
      com.llmobservability.platform.v1.InitMetricsResponse> getInitMetricsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "InitMetrics",
      requestType = com.llmobservability.platform.v1.InitMetricsRequest.class,
      responseType = com.llmobservability.platform.v1.InitMetricsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.InitMetricsRequest,
      com.llmobservability.platform.v1.InitMetricsResponse> getInitMetricsMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.InitMetricsRequest, com.llmobservability.platform.v1.InitMetricsResponse> getInitMetricsMethod;
    if ((getInitMetricsMethod = InstrumentationControlServiceGrpc.getInitMetricsMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getInitMetricsMethod = InstrumentationControlServiceGrpc.getInitMetricsMethod) == null) {
          InstrumentationControlServiceGrpc.getInitMetricsMethod = getInitMetricsMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.InitMetricsRequest, com.llmobservability.platform.v1.InitMetricsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "InitMetrics"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.InitMetricsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.InitMetricsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("InitMetrics"))
              .build();
        }
      }
    }
    return getInitMetricsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetMetricsHealthRequest,
      com.llmobservability.platform.v1.GetMetricsHealthResponse> getGetMetricsHealthMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetMetricsHealth",
      requestType = com.llmobservability.platform.v1.GetMetricsHealthRequest.class,
      responseType = com.llmobservability.platform.v1.GetMetricsHealthResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetMetricsHealthRequest,
      com.llmobservability.platform.v1.GetMetricsHealthResponse> getGetMetricsHealthMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetMetricsHealthRequest, com.llmobservability.platform.v1.GetMetricsHealthResponse> getGetMetricsHealthMethod;
    if ((getGetMetricsHealthMethod = InstrumentationControlServiceGrpc.getGetMetricsHealthMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getGetMetricsHealthMethod = InstrumentationControlServiceGrpc.getGetMetricsHealthMethod) == null) {
          InstrumentationControlServiceGrpc.getGetMetricsHealthMethod = getGetMetricsHealthMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.GetMetricsHealthRequest, com.llmobservability.platform.v1.GetMetricsHealthResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetMetricsHealth"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.GetMetricsHealthRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.GetMetricsHealthResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("GetMetricsHealth"))
              .build();
        }
      }
    }
    return getGetMetricsHealthMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.RecordMetricsRequest,
      com.llmobservability.platform.v1.RecordMetricsResponse> getRecordMetricsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "RecordMetrics",
      requestType = com.llmobservability.platform.v1.RecordMetricsRequest.class,
      responseType = com.llmobservability.platform.v1.RecordMetricsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.RecordMetricsRequest,
      com.llmobservability.platform.v1.RecordMetricsResponse> getRecordMetricsMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.RecordMetricsRequest, com.llmobservability.platform.v1.RecordMetricsResponse> getRecordMetricsMethod;
    if ((getRecordMetricsMethod = InstrumentationControlServiceGrpc.getRecordMetricsMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getRecordMetricsMethod = InstrumentationControlServiceGrpc.getRecordMetricsMethod) == null) {
          InstrumentationControlServiceGrpc.getRecordMetricsMethod = getRecordMetricsMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.RecordMetricsRequest, com.llmobservability.platform.v1.RecordMetricsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "RecordMetrics"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.RecordMetricsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.RecordMetricsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("RecordMetrics"))
              .build();
        }
      }
    }
    return getRecordMetricsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.RecordMetricsBatchRequest,
      com.llmobservability.platform.v1.RecordMetricsBatchResponse> getRecordMetricsBatchMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "RecordMetricsBatch",
      requestType = com.llmobservability.platform.v1.RecordMetricsBatchRequest.class,
      responseType = com.llmobservability.platform.v1.RecordMetricsBatchResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.RecordMetricsBatchRequest,
      com.llmobservability.platform.v1.RecordMetricsBatchResponse> getRecordMetricsBatchMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.RecordMetricsBatchRequest, com.llmobservability.platform.v1.RecordMetricsBatchResponse> getRecordMetricsBatchMethod;
    if ((getRecordMetricsBatchMethod = InstrumentationControlServiceGrpc.getRecordMetricsBatchMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getRecordMetricsBatchMethod = InstrumentationControlServiceGrpc.getRecordMetricsBatchMethod) == null) {
          InstrumentationControlServiceGrpc.getRecordMetricsBatchMethod = getRecordMetricsBatchMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.RecordMetricsBatchRequest, com.llmobservability.platform.v1.RecordMetricsBatchResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "RecordMetricsBatch"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.RecordMetricsBatchRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.RecordMetricsBatchResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("RecordMetricsBatch"))
              .build();
        }
      }
    }
    return getRecordMetricsBatchMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetModelPricesRequest,
      com.llmobservability.platform.v1.GetModelPricesResponse> getGetModelPricesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetModelPrices",
      requestType = com.llmobservability.platform.v1.GetModelPricesRequest.class,
      responseType = com.llmobservability.platform.v1.GetModelPricesResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetModelPricesRequest,
      com.llmobservability.platform.v1.GetModelPricesResponse> getGetModelPricesMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.GetModelPricesRequest, com.llmobservability.platform.v1.GetModelPricesResponse> getGetModelPricesMethod;
    if ((getGetModelPricesMethod = InstrumentationControlServiceGrpc.getGetModelPricesMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getGetModelPricesMethod = InstrumentationControlServiceGrpc.getGetModelPricesMethod) == null) {
          InstrumentationControlServiceGrpc.getGetModelPricesMethod = getGetModelPricesMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.GetModelPricesRequest, com.llmobservability.platform.v1.GetModelPricesResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetModelPrices"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.GetModelPricesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.GetModelPricesResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("GetModelPrices"))
              .build();
        }
      }
    }
    return getGetModelPricesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ReloadModelPricesRequest,
      com.llmobservability.platform.v1.ReloadModelPricesResponse> getReloadModelPricesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ReloadModelPrices",
      requestType = com.llmobservability.platform.v1.ReloadModelPricesRequest.class,
      responseType = com.llmobservability.platform.v1.ReloadModelPricesResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ReloadModelPricesRequest,
      com.llmobservability.platform.v1.ReloadModelPricesResponse> getReloadModelPricesMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.ReloadModelPricesRequest, com.llmobservability.platform.v1.ReloadModelPricesResponse> getReloadModelPricesMethod;
    if ((getReloadModelPricesMethod = InstrumentationControlServiceGrpc.getReloadModelPricesMethod) == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        if ((getReloadModelPricesMethod = InstrumentationControlServiceGrpc.getReloadModelPricesMethod) == null) {
          InstrumentationControlServiceGrpc.getReloadModelPricesMethod = getReloadModelPricesMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.ReloadModelPricesRequest, com.llmobservability.platform.v1.ReloadModelPricesResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ReloadModelPrices"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ReloadModelPricesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.ReloadModelPricesResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InstrumentationControlServiceMethodDescriptorSupplier("ReloadModelPrices"))
              .build();
        }
      }
    }
    return getReloadModelPricesMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static InstrumentationControlServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InstrumentationControlServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InstrumentationControlServiceStub>() {
        @java.lang.Override
        public InstrumentationControlServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InstrumentationControlServiceStub(channel, callOptions);
        }
      };
    return InstrumentationControlServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static InstrumentationControlServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InstrumentationControlServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InstrumentationControlServiceBlockingStub>() {
        @java.lang.Override
        public InstrumentationControlServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InstrumentationControlServiceBlockingStub(channel, callOptions);
        }
      };
    return InstrumentationControlServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static InstrumentationControlServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InstrumentationControlServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InstrumentationControlServiceFutureStub>() {
        @java.lang.Override
        public InstrumentationControlServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InstrumentationControlServiceFutureStub(channel, callOptions);
        }
      };
    return InstrumentationControlServiceFutureStub.newStub(factory, channel);
  }

  /**
   * <pre>
   * Service definition for remote instrumentation control
   * </pre>
   */
  public interface AsyncService {

    /**
     */
    default void initInstrumentation(com.llmobservability.platform.v1.InitInstrumentationRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.InitInstrumentationResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getInitInstrumentationMethod(), responseObserver);
    }

    /**
     */
    default void disableInstrumentation(com.llmobservability.platform.v1.DisableInstrumentationRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.DisableInstrumentationResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getDisableInstrumentationMethod(), responseObserver);
    }

    /**
     */
    default void getStatus(com.llmobservability.platform.v1.GetStatusRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetStatusResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetStatusMethod(), responseObserver);
    }

    /**
     */
    default void detectProvider(com.llmobservability.platform.v1.DetectProviderRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.DetectProviderResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getDetectProviderMethod(), responseObserver);
    }

    /**
     */
    default void triggerTestCall(com.llmobservability.platform.v1.TriggerTestCallRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TriggerTestCallResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getTriggerTestCallMethod(), responseObserver);
    }

    /**
     */
    default void triggerTestStreamCall(com.llmobservability.platform.v1.TriggerTestStreamCallRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TriggerTestStreamCallResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getTriggerTestStreamCallMethod(), responseObserver);
    }

    /**
     */
    default void countTokens(com.llmobservability.platform.v1.CountTokensRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.CountTokensResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCountTokensMethod(), responseObserver);
    }

    /**
     */
    default void scanPiiInjection(com.llmobservability.platform.v1.ScanPiiInjectionRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ScanPiiInjectionResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getScanPiiInjectionMethod(), responseObserver);
    }

    /**
     */
    default void shouldSample(com.llmobservability.platform.v1.ShouldSampleRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ShouldSampleResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getShouldSampleMethod(), responseObserver);
    }

    /**
     */
    default void getEmbedding(com.llmobservability.platform.v1.GetEmbeddingRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetEmbeddingResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetEmbeddingMethod(), responseObserver);
    }

    /**
     */
    default void trackFallback(com.llmobservability.platform.v1.TrackFallbackRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TrackFallbackResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getTrackFallbackMethod(), responseObserver);
    }

    /**
     */
    default void clearFallbackTracker(com.llmobservability.platform.v1.ClearFallbackTrackerRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ClearFallbackTrackerResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getClearFallbackTrackerMethod(), responseObserver);
    }

    /**
     */
    default void trackToolCall(com.llmobservability.platform.v1.TrackToolCallRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TrackToolCallResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getTrackToolCallMethod(), responseObserver);
    }

    /**
     */
    default void clearToolCallTracker(com.llmobservability.platform.v1.ClearToolCallTrackerRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ClearToolCallTrackerResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getClearToolCallTrackerMethod(), responseObserver);
    }

    /**
     */
    default void initMetrics(com.llmobservability.platform.v1.InitMetricsRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.InitMetricsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getInitMetricsMethod(), responseObserver);
    }

    /**
     */
    default void getMetricsHealth(com.llmobservability.platform.v1.GetMetricsHealthRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetMetricsHealthResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetMetricsHealthMethod(), responseObserver);
    }

    /**
     */
    default void recordMetrics(com.llmobservability.platform.v1.RecordMetricsRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordMetricsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getRecordMetricsMethod(), responseObserver);
    }

    /**
     */
    default void recordMetricsBatch(com.llmobservability.platform.v1.RecordMetricsBatchRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordMetricsBatchResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getRecordMetricsBatchMethod(), responseObserver);
    }

    /**
     */
    default void getModelPrices(com.llmobservability.platform.v1.GetModelPricesRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetModelPricesResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetModelPricesMethod(), responseObserver);
    }

    /**
     */
    default void reloadModelPrices(com.llmobservability.platform.v1.ReloadModelPricesRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ReloadModelPricesResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getReloadModelPricesMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service InstrumentationControlService.
   * <pre>
   * Service definition for remote instrumentation control
   * </pre>
   */
  public static abstract class InstrumentationControlServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return InstrumentationControlServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service InstrumentationControlService.
   * <pre>
   * Service definition for remote instrumentation control
   * </pre>
   */
  public static final class InstrumentationControlServiceStub
      extends io.grpc.stub.AbstractAsyncStub<InstrumentationControlServiceStub> {
    private InstrumentationControlServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InstrumentationControlServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InstrumentationControlServiceStub(channel, callOptions);
    }

    /**
     */
    public void initInstrumentation(com.llmobservability.platform.v1.InitInstrumentationRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.InitInstrumentationResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getInitInstrumentationMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void disableInstrumentation(com.llmobservability.platform.v1.DisableInstrumentationRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.DisableInstrumentationResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getDisableInstrumentationMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getStatus(com.llmobservability.platform.v1.GetStatusRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetStatusResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetStatusMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void detectProvider(com.llmobservability.platform.v1.DetectProviderRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.DetectProviderResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getDetectProviderMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void triggerTestCall(com.llmobservability.platform.v1.TriggerTestCallRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TriggerTestCallResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getTriggerTestCallMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void triggerTestStreamCall(com.llmobservability.platform.v1.TriggerTestStreamCallRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TriggerTestStreamCallResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getTriggerTestStreamCallMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void countTokens(com.llmobservability.platform.v1.CountTokensRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.CountTokensResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCountTokensMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void scanPiiInjection(com.llmobservability.platform.v1.ScanPiiInjectionRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ScanPiiInjectionResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getScanPiiInjectionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void shouldSample(com.llmobservability.platform.v1.ShouldSampleRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ShouldSampleResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getShouldSampleMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getEmbedding(com.llmobservability.platform.v1.GetEmbeddingRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetEmbeddingResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetEmbeddingMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void trackFallback(com.llmobservability.platform.v1.TrackFallbackRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TrackFallbackResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getTrackFallbackMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void clearFallbackTracker(com.llmobservability.platform.v1.ClearFallbackTrackerRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ClearFallbackTrackerResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getClearFallbackTrackerMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void trackToolCall(com.llmobservability.platform.v1.TrackToolCallRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TrackToolCallResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getTrackToolCallMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void clearToolCallTracker(com.llmobservability.platform.v1.ClearToolCallTrackerRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ClearToolCallTrackerResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getClearToolCallTrackerMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void initMetrics(com.llmobservability.platform.v1.InitMetricsRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.InitMetricsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getInitMetricsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getMetricsHealth(com.llmobservability.platform.v1.GetMetricsHealthRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetMetricsHealthResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetMetricsHealthMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void recordMetrics(com.llmobservability.platform.v1.RecordMetricsRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordMetricsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getRecordMetricsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void recordMetricsBatch(com.llmobservability.platform.v1.RecordMetricsBatchRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordMetricsBatchResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getRecordMetricsBatchMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getModelPrices(com.llmobservability.platform.v1.GetModelPricesRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetModelPricesResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetModelPricesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void reloadModelPrices(com.llmobservability.platform.v1.ReloadModelPricesRequest request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ReloadModelPricesResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getReloadModelPricesMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service InstrumentationControlService.
   * <pre>
   * Service definition for remote instrumentation control
   * </pre>
   */
  public static final class InstrumentationControlServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<InstrumentationControlServiceBlockingStub> {
    private InstrumentationControlServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InstrumentationControlServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InstrumentationControlServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.llmobservability.platform.v1.InitInstrumentationResponse initInstrumentation(com.llmobservability.platform.v1.InitInstrumentationRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getInitInstrumentationMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.DisableInstrumentationResponse disableInstrumentation(com.llmobservability.platform.v1.DisableInstrumentationRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getDisableInstrumentationMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.GetStatusResponse getStatus(com.llmobservability.platform.v1.GetStatusRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetStatusMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.DetectProviderResponse detectProvider(com.llmobservability.platform.v1.DetectProviderRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getDetectProviderMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.TriggerTestCallResponse triggerTestCall(com.llmobservability.platform.v1.TriggerTestCallRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getTriggerTestCallMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.TriggerTestStreamCallResponse triggerTestStreamCall(com.llmobservability.platform.v1.TriggerTestStreamCallRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getTriggerTestStreamCallMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.CountTokensResponse countTokens(com.llmobservability.platform.v1.CountTokensRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCountTokensMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.ScanPiiInjectionResponse scanPiiInjection(com.llmobservability.platform.v1.ScanPiiInjectionRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getScanPiiInjectionMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.ShouldSampleResponse shouldSample(com.llmobservability.platform.v1.ShouldSampleRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getShouldSampleMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.GetEmbeddingResponse getEmbedding(com.llmobservability.platform.v1.GetEmbeddingRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetEmbeddingMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.TrackFallbackResponse trackFallback(com.llmobservability.platform.v1.TrackFallbackRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getTrackFallbackMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.ClearFallbackTrackerResponse clearFallbackTracker(com.llmobservability.platform.v1.ClearFallbackTrackerRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getClearFallbackTrackerMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.TrackToolCallResponse trackToolCall(com.llmobservability.platform.v1.TrackToolCallRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getTrackToolCallMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.ClearToolCallTrackerResponse clearToolCallTracker(com.llmobservability.platform.v1.ClearToolCallTrackerRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getClearToolCallTrackerMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.InitMetricsResponse initMetrics(com.llmobservability.platform.v1.InitMetricsRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getInitMetricsMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.GetMetricsHealthResponse getMetricsHealth(com.llmobservability.platform.v1.GetMetricsHealthRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetMetricsHealthMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.RecordMetricsResponse recordMetrics(com.llmobservability.platform.v1.RecordMetricsRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getRecordMetricsMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.RecordMetricsBatchResponse recordMetricsBatch(com.llmobservability.platform.v1.RecordMetricsBatchRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getRecordMetricsBatchMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.GetModelPricesResponse getModelPrices(com.llmobservability.platform.v1.GetModelPricesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetModelPricesMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.llmobservability.platform.v1.ReloadModelPricesResponse reloadModelPrices(com.llmobservability.platform.v1.ReloadModelPricesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getReloadModelPricesMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service InstrumentationControlService.
   * <pre>
   * Service definition for remote instrumentation control
   * </pre>
   */
  public static final class InstrumentationControlServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<InstrumentationControlServiceFutureStub> {
    private InstrumentationControlServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InstrumentationControlServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InstrumentationControlServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.InitInstrumentationResponse> initInstrumentation(
        com.llmobservability.platform.v1.InitInstrumentationRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getInitInstrumentationMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.DisableInstrumentationResponse> disableInstrumentation(
        com.llmobservability.platform.v1.DisableInstrumentationRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getDisableInstrumentationMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.GetStatusResponse> getStatus(
        com.llmobservability.platform.v1.GetStatusRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetStatusMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.DetectProviderResponse> detectProvider(
        com.llmobservability.platform.v1.DetectProviderRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getDetectProviderMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.TriggerTestCallResponse> triggerTestCall(
        com.llmobservability.platform.v1.TriggerTestCallRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getTriggerTestCallMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.TriggerTestStreamCallResponse> triggerTestStreamCall(
        com.llmobservability.platform.v1.TriggerTestStreamCallRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getTriggerTestStreamCallMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.CountTokensResponse> countTokens(
        com.llmobservability.platform.v1.CountTokensRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCountTokensMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.ScanPiiInjectionResponse> scanPiiInjection(
        com.llmobservability.platform.v1.ScanPiiInjectionRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getScanPiiInjectionMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.ShouldSampleResponse> shouldSample(
        com.llmobservability.platform.v1.ShouldSampleRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getShouldSampleMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.GetEmbeddingResponse> getEmbedding(
        com.llmobservability.platform.v1.GetEmbeddingRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetEmbeddingMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.TrackFallbackResponse> trackFallback(
        com.llmobservability.platform.v1.TrackFallbackRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getTrackFallbackMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.ClearFallbackTrackerResponse> clearFallbackTracker(
        com.llmobservability.platform.v1.ClearFallbackTrackerRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getClearFallbackTrackerMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.TrackToolCallResponse> trackToolCall(
        com.llmobservability.platform.v1.TrackToolCallRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getTrackToolCallMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.ClearToolCallTrackerResponse> clearToolCallTracker(
        com.llmobservability.platform.v1.ClearToolCallTrackerRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getClearToolCallTrackerMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.InitMetricsResponse> initMetrics(
        com.llmobservability.platform.v1.InitMetricsRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getInitMetricsMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.GetMetricsHealthResponse> getMetricsHealth(
        com.llmobservability.platform.v1.GetMetricsHealthRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetMetricsHealthMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.RecordMetricsResponse> recordMetrics(
        com.llmobservability.platform.v1.RecordMetricsRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getRecordMetricsMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.RecordMetricsBatchResponse> recordMetricsBatch(
        com.llmobservability.platform.v1.RecordMetricsBatchRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getRecordMetricsBatchMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.GetModelPricesResponse> getModelPrices(
        com.llmobservability.platform.v1.GetModelPricesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetModelPricesMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.ReloadModelPricesResponse> reloadModelPrices(
        com.llmobservability.platform.v1.ReloadModelPricesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getReloadModelPricesMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_INIT_INSTRUMENTATION = 0;
  private static final int METHODID_DISABLE_INSTRUMENTATION = 1;
  private static final int METHODID_GET_STATUS = 2;
  private static final int METHODID_DETECT_PROVIDER = 3;
  private static final int METHODID_TRIGGER_TEST_CALL = 4;
  private static final int METHODID_TRIGGER_TEST_STREAM_CALL = 5;
  private static final int METHODID_COUNT_TOKENS = 6;
  private static final int METHODID_SCAN_PII_INJECTION = 7;
  private static final int METHODID_SHOULD_SAMPLE = 8;
  private static final int METHODID_GET_EMBEDDING = 9;
  private static final int METHODID_TRACK_FALLBACK = 10;
  private static final int METHODID_CLEAR_FALLBACK_TRACKER = 11;
  private static final int METHODID_TRACK_TOOL_CALL = 12;
  private static final int METHODID_CLEAR_TOOL_CALL_TRACKER = 13;
  private static final int METHODID_INIT_METRICS = 14;
  private static final int METHODID_GET_METRICS_HEALTH = 15;
  private static final int METHODID_RECORD_METRICS = 16;
  private static final int METHODID_RECORD_METRICS_BATCH = 17;
  private static final int METHODID_GET_MODEL_PRICES = 18;
  private static final int METHODID_RELOAD_MODEL_PRICES = 19;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_INIT_INSTRUMENTATION:
          serviceImpl.initInstrumentation((com.llmobservability.platform.v1.InitInstrumentationRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.InitInstrumentationResponse>) responseObserver);
          break;
        case METHODID_DISABLE_INSTRUMENTATION:
          serviceImpl.disableInstrumentation((com.llmobservability.platform.v1.DisableInstrumentationRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.DisableInstrumentationResponse>) responseObserver);
          break;
        case METHODID_GET_STATUS:
          serviceImpl.getStatus((com.llmobservability.platform.v1.GetStatusRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetStatusResponse>) responseObserver);
          break;
        case METHODID_DETECT_PROVIDER:
          serviceImpl.detectProvider((com.llmobservability.platform.v1.DetectProviderRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.DetectProviderResponse>) responseObserver);
          break;
        case METHODID_TRIGGER_TEST_CALL:
          serviceImpl.triggerTestCall((com.llmobservability.platform.v1.TriggerTestCallRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TriggerTestCallResponse>) responseObserver);
          break;
        case METHODID_TRIGGER_TEST_STREAM_CALL:
          serviceImpl.triggerTestStreamCall((com.llmobservability.platform.v1.TriggerTestStreamCallRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TriggerTestStreamCallResponse>) responseObserver);
          break;
        case METHODID_COUNT_TOKENS:
          serviceImpl.countTokens((com.llmobservability.platform.v1.CountTokensRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.CountTokensResponse>) responseObserver);
          break;
        case METHODID_SCAN_PII_INJECTION:
          serviceImpl.scanPiiInjection((com.llmobservability.platform.v1.ScanPiiInjectionRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ScanPiiInjectionResponse>) responseObserver);
          break;
        case METHODID_SHOULD_SAMPLE:
          serviceImpl.shouldSample((com.llmobservability.platform.v1.ShouldSampleRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ShouldSampleResponse>) responseObserver);
          break;
        case METHODID_GET_EMBEDDING:
          serviceImpl.getEmbedding((com.llmobservability.platform.v1.GetEmbeddingRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetEmbeddingResponse>) responseObserver);
          break;
        case METHODID_TRACK_FALLBACK:
          serviceImpl.trackFallback((com.llmobservability.platform.v1.TrackFallbackRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TrackFallbackResponse>) responseObserver);
          break;
        case METHODID_CLEAR_FALLBACK_TRACKER:
          serviceImpl.clearFallbackTracker((com.llmobservability.platform.v1.ClearFallbackTrackerRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ClearFallbackTrackerResponse>) responseObserver);
          break;
        case METHODID_TRACK_TOOL_CALL:
          serviceImpl.trackToolCall((com.llmobservability.platform.v1.TrackToolCallRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.TrackToolCallResponse>) responseObserver);
          break;
        case METHODID_CLEAR_TOOL_CALL_TRACKER:
          serviceImpl.clearToolCallTracker((com.llmobservability.platform.v1.ClearToolCallTrackerRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ClearToolCallTrackerResponse>) responseObserver);
          break;
        case METHODID_INIT_METRICS:
          serviceImpl.initMetrics((com.llmobservability.platform.v1.InitMetricsRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.InitMetricsResponse>) responseObserver);
          break;
        case METHODID_GET_METRICS_HEALTH:
          serviceImpl.getMetricsHealth((com.llmobservability.platform.v1.GetMetricsHealthRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetMetricsHealthResponse>) responseObserver);
          break;
        case METHODID_RECORD_METRICS:
          serviceImpl.recordMetrics((com.llmobservability.platform.v1.RecordMetricsRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordMetricsResponse>) responseObserver);
          break;
        case METHODID_RECORD_METRICS_BATCH:
          serviceImpl.recordMetricsBatch((com.llmobservability.platform.v1.RecordMetricsBatchRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordMetricsBatchResponse>) responseObserver);
          break;
        case METHODID_GET_MODEL_PRICES:
          serviceImpl.getModelPrices((com.llmobservability.platform.v1.GetModelPricesRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.GetModelPricesResponse>) responseObserver);
          break;
        case METHODID_RELOAD_MODEL_PRICES:
          serviceImpl.reloadModelPrices((com.llmobservability.platform.v1.ReloadModelPricesRequest) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.ReloadModelPricesResponse>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getInitInstrumentationMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.InitInstrumentationRequest,
              com.llmobservability.platform.v1.InitInstrumentationResponse>(
                service, METHODID_INIT_INSTRUMENTATION)))
        .addMethod(
          getDisableInstrumentationMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.DisableInstrumentationRequest,
              com.llmobservability.platform.v1.DisableInstrumentationResponse>(
                service, METHODID_DISABLE_INSTRUMENTATION)))
        .addMethod(
          getGetStatusMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.GetStatusRequest,
              com.llmobservability.platform.v1.GetStatusResponse>(
                service, METHODID_GET_STATUS)))
        .addMethod(
          getDetectProviderMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.DetectProviderRequest,
              com.llmobservability.platform.v1.DetectProviderResponse>(
                service, METHODID_DETECT_PROVIDER)))
        .addMethod(
          getTriggerTestCallMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.TriggerTestCallRequest,
              com.llmobservability.platform.v1.TriggerTestCallResponse>(
                service, METHODID_TRIGGER_TEST_CALL)))
        .addMethod(
          getTriggerTestStreamCallMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.TriggerTestStreamCallRequest,
              com.llmobservability.platform.v1.TriggerTestStreamCallResponse>(
                service, METHODID_TRIGGER_TEST_STREAM_CALL)))
        .addMethod(
          getCountTokensMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.CountTokensRequest,
              com.llmobservability.platform.v1.CountTokensResponse>(
                service, METHODID_COUNT_TOKENS)))
        .addMethod(
          getScanPiiInjectionMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.ScanPiiInjectionRequest,
              com.llmobservability.platform.v1.ScanPiiInjectionResponse>(
                service, METHODID_SCAN_PII_INJECTION)))
        .addMethod(
          getShouldSampleMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.ShouldSampleRequest,
              com.llmobservability.platform.v1.ShouldSampleResponse>(
                service, METHODID_SHOULD_SAMPLE)))
        .addMethod(
          getGetEmbeddingMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.GetEmbeddingRequest,
              com.llmobservability.platform.v1.GetEmbeddingResponse>(
                service, METHODID_GET_EMBEDDING)))
        .addMethod(
          getTrackFallbackMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.TrackFallbackRequest,
              com.llmobservability.platform.v1.TrackFallbackResponse>(
                service, METHODID_TRACK_FALLBACK)))
        .addMethod(
          getClearFallbackTrackerMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.ClearFallbackTrackerRequest,
              com.llmobservability.platform.v1.ClearFallbackTrackerResponse>(
                service, METHODID_CLEAR_FALLBACK_TRACKER)))
        .addMethod(
          getTrackToolCallMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.TrackToolCallRequest,
              com.llmobservability.platform.v1.TrackToolCallResponse>(
                service, METHODID_TRACK_TOOL_CALL)))
        .addMethod(
          getClearToolCallTrackerMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.ClearToolCallTrackerRequest,
              com.llmobservability.platform.v1.ClearToolCallTrackerResponse>(
                service, METHODID_CLEAR_TOOL_CALL_TRACKER)))
        .addMethod(
          getInitMetricsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.InitMetricsRequest,
              com.llmobservability.platform.v1.InitMetricsResponse>(
                service, METHODID_INIT_METRICS)))
        .addMethod(
          getGetMetricsHealthMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.GetMetricsHealthRequest,
              com.llmobservability.platform.v1.GetMetricsHealthResponse>(
                service, METHODID_GET_METRICS_HEALTH)))
        .addMethod(
          getRecordMetricsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.RecordMetricsRequest,
              com.llmobservability.platform.v1.RecordMetricsResponse>(
                service, METHODID_RECORD_METRICS)))
        .addMethod(
          getRecordMetricsBatchMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.RecordMetricsBatchRequest,
              com.llmobservability.platform.v1.RecordMetricsBatchResponse>(
                service, METHODID_RECORD_METRICS_BATCH)))
        .addMethod(
          getGetModelPricesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.GetModelPricesRequest,
              com.llmobservability.platform.v1.GetModelPricesResponse>(
                service, METHODID_GET_MODEL_PRICES)))
        .addMethod(
          getReloadModelPricesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.ReloadModelPricesRequest,
              com.llmobservability.platform.v1.ReloadModelPricesResponse>(
                service, METHODID_RELOAD_MODEL_PRICES)))
        .build();
  }

  private static abstract class InstrumentationControlServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    InstrumentationControlServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.llmobservability.platform.v1.InstrumentationProto.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("InstrumentationControlService");
    }
  }

  private static final class InstrumentationControlServiceFileDescriptorSupplier
      extends InstrumentationControlServiceBaseDescriptorSupplier {
    InstrumentationControlServiceFileDescriptorSupplier() {}
  }

  private static final class InstrumentationControlServiceMethodDescriptorSupplier
      extends InstrumentationControlServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    InstrumentationControlServiceMethodDescriptorSupplier(java.lang.String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (InstrumentationControlServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new InstrumentationControlServiceFileDescriptorSupplier())
              .addMethod(getInitInstrumentationMethod())
              .addMethod(getDisableInstrumentationMethod())
              .addMethod(getGetStatusMethod())
              .addMethod(getDetectProviderMethod())
              .addMethod(getTriggerTestCallMethod())
              .addMethod(getTriggerTestStreamCallMethod())
              .addMethod(getCountTokensMethod())
              .addMethod(getScanPiiInjectionMethod())
              .addMethod(getShouldSampleMethod())
              .addMethod(getGetEmbeddingMethod())
              .addMethod(getTrackFallbackMethod())
              .addMethod(getClearFallbackTrackerMethod())
              .addMethod(getTrackToolCallMethod())
              .addMethod(getClearToolCallTrackerMethod())
              .addMethod(getInitMetricsMethod())
              .addMethod(getGetMetricsHealthMethod())
              .addMethod(getRecordMetricsMethod())
              .addMethod(getRecordMetricsBatchMethod())
              .addMethod(getGetModelPricesMethod())
              .addMethod(getReloadModelPricesMethod())
              .build();
        }
      }
    }
    return result;
  }
}
