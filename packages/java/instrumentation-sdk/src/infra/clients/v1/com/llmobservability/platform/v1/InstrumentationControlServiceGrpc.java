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
  }

  private static final int METHODID_INIT_INSTRUMENTATION = 0;
  private static final int METHODID_DISABLE_INSTRUMENTATION = 1;
  private static final int METHODID_GET_STATUS = 2;
  private static final int METHODID_DETECT_PROVIDER = 3;
  private static final int METHODID_TRIGGER_TEST_CALL = 4;
  private static final int METHODID_TRIGGER_TEST_STREAM_CALL = 5;
  private static final int METHODID_COUNT_TOKENS = 6;
  private static final int METHODID_SCAN_PII_INJECTION = 7;

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
              .build();
        }
      }
    }
    return result;
  }
}
