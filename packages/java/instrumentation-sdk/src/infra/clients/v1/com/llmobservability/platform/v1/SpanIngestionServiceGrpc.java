package com.llmobservability.platform.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 * <pre>
 * Service definition for direct gRPC ingestion
 * </pre>
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.60.0)",
    comments = "Source: span.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class SpanIngestionServiceGrpc {

  private SpanIngestionServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "llm.observability.v1.SpanIngestionService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.llmobservability.platform.v1.LLMSpan,
      com.llmobservability.platform.v1.RecordSpanResponse> getRecordSpanMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "RecordSpan",
      requestType = com.llmobservability.platform.v1.LLMSpan.class,
      responseType = com.llmobservability.platform.v1.RecordSpanResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.llmobservability.platform.v1.LLMSpan,
      com.llmobservability.platform.v1.RecordSpanResponse> getRecordSpanMethod() {
    io.grpc.MethodDescriptor<com.llmobservability.platform.v1.LLMSpan, com.llmobservability.platform.v1.RecordSpanResponse> getRecordSpanMethod;
    if ((getRecordSpanMethod = SpanIngestionServiceGrpc.getRecordSpanMethod) == null) {
      synchronized (SpanIngestionServiceGrpc.class) {
        if ((getRecordSpanMethod = SpanIngestionServiceGrpc.getRecordSpanMethod) == null) {
          SpanIngestionServiceGrpc.getRecordSpanMethod = getRecordSpanMethod =
              io.grpc.MethodDescriptor.<com.llmobservability.platform.v1.LLMSpan, com.llmobservability.platform.v1.RecordSpanResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "RecordSpan"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.LLMSpan.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.llmobservability.platform.v1.RecordSpanResponse.getDefaultInstance()))
              .setSchemaDescriptor(new SpanIngestionServiceMethodDescriptorSupplier("RecordSpan"))
              .build();
        }
      }
    }
    return getRecordSpanMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static SpanIngestionServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<SpanIngestionServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<SpanIngestionServiceStub>() {
        @java.lang.Override
        public SpanIngestionServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new SpanIngestionServiceStub(channel, callOptions);
        }
      };
    return SpanIngestionServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static SpanIngestionServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<SpanIngestionServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<SpanIngestionServiceBlockingStub>() {
        @java.lang.Override
        public SpanIngestionServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new SpanIngestionServiceBlockingStub(channel, callOptions);
        }
      };
    return SpanIngestionServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static SpanIngestionServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<SpanIngestionServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<SpanIngestionServiceFutureStub>() {
        @java.lang.Override
        public SpanIngestionServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new SpanIngestionServiceFutureStub(channel, callOptions);
        }
      };
    return SpanIngestionServiceFutureStub.newStub(factory, channel);
  }

  /**
   * <pre>
   * Service definition for direct gRPC ingestion
   * </pre>
   */
  public interface AsyncService {

    /**
     */
    default void recordSpan(com.llmobservability.platform.v1.LLMSpan request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordSpanResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getRecordSpanMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service SpanIngestionService.
   * <pre>
   * Service definition for direct gRPC ingestion
   * </pre>
   */
  public static abstract class SpanIngestionServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return SpanIngestionServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service SpanIngestionService.
   * <pre>
   * Service definition for direct gRPC ingestion
   * </pre>
   */
  public static final class SpanIngestionServiceStub
      extends io.grpc.stub.AbstractAsyncStub<SpanIngestionServiceStub> {
    private SpanIngestionServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected SpanIngestionServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new SpanIngestionServiceStub(channel, callOptions);
    }

    /**
     */
    public void recordSpan(com.llmobservability.platform.v1.LLMSpan request,
        io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordSpanResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getRecordSpanMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service SpanIngestionService.
   * <pre>
   * Service definition for direct gRPC ingestion
   * </pre>
   */
  public static final class SpanIngestionServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<SpanIngestionServiceBlockingStub> {
    private SpanIngestionServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected SpanIngestionServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new SpanIngestionServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.llmobservability.platform.v1.RecordSpanResponse recordSpan(com.llmobservability.platform.v1.LLMSpan request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getRecordSpanMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service SpanIngestionService.
   * <pre>
   * Service definition for direct gRPC ingestion
   * </pre>
   */
  public static final class SpanIngestionServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<SpanIngestionServiceFutureStub> {
    private SpanIngestionServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected SpanIngestionServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new SpanIngestionServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.llmobservability.platform.v1.RecordSpanResponse> recordSpan(
        com.llmobservability.platform.v1.LLMSpan request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getRecordSpanMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_RECORD_SPAN = 0;

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
        case METHODID_RECORD_SPAN:
          serviceImpl.recordSpan((com.llmobservability.platform.v1.LLMSpan) request,
              (io.grpc.stub.StreamObserver<com.llmobservability.platform.v1.RecordSpanResponse>) responseObserver);
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
          getRecordSpanMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.llmobservability.platform.v1.LLMSpan,
              com.llmobservability.platform.v1.RecordSpanResponse>(
                service, METHODID_RECORD_SPAN)))
        .build();
  }

  private static abstract class SpanIngestionServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    SpanIngestionServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.llmobservability.platform.v1.SpanProto.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("SpanIngestionService");
    }
  }

  private static final class SpanIngestionServiceFileDescriptorSupplier
      extends SpanIngestionServiceBaseDescriptorSupplier {
    SpanIngestionServiceFileDescriptorSupplier() {}
  }

  private static final class SpanIngestionServiceMethodDescriptorSupplier
      extends SpanIngestionServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    SpanIngestionServiceMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (SpanIngestionServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new SpanIngestionServiceFileDescriptorSupplier())
              .addMethod(getRecordSpanMethod())
              .build();
        }
      }
    }
    return result;
  }
}
