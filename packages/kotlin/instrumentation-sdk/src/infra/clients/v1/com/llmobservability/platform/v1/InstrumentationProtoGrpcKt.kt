package com.llmobservability.platform.v1

import com.llmobservability.platform.v1.InstrumentationControlServiceGrpc.getServiceDescriptor
import io.grpc.CallOptions
import io.grpc.CallOptions.DEFAULT
import io.grpc.Channel
import io.grpc.Metadata
import io.grpc.MethodDescriptor
import io.grpc.ServerServiceDefinition
import io.grpc.ServerServiceDefinition.builder
import io.grpc.ServiceDescriptor
import io.grpc.Status.UNIMPLEMENTED
import io.grpc.StatusException
import io.grpc.kotlin.AbstractCoroutineServerImpl
import io.grpc.kotlin.AbstractCoroutineStub
import io.grpc.kotlin.ClientCalls.unaryRpc
import io.grpc.kotlin.ServerCalls.unaryServerMethodDefinition
import io.grpc.kotlin.StubFor
import kotlin.String
import kotlin.coroutines.CoroutineContext
import kotlin.coroutines.EmptyCoroutineContext
import kotlin.jvm.JvmOverloads
import kotlin.jvm.JvmStatic

/**
 * Holder for Kotlin coroutine-based client and server APIs for
 * llm.observability.v1.InstrumentationControlService.
 */
public object InstrumentationControlServiceGrpcKt {
  public const val SERVICE_NAME: String = InstrumentationControlServiceGrpc.SERVICE_NAME

  @JvmStatic
  public val serviceDescriptor: ServiceDescriptor
    get() = getServiceDescriptor()

  public val initInstrumentationMethod:
      MethodDescriptor<InitInstrumentationRequest, InitInstrumentationResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getInitInstrumentationMethod()

  public val disableInstrumentationMethod:
      MethodDescriptor<DisableInstrumentationRequest, DisableInstrumentationResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getDisableInstrumentationMethod()

  public val getStatusMethod: MethodDescriptor<GetStatusRequest, GetStatusResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getGetStatusMethod()

  public val detectProviderMethod: MethodDescriptor<DetectProviderRequest, DetectProviderResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getDetectProviderMethod()

  public val triggerTestCallMethod:
      MethodDescriptor<TriggerTestCallRequest, TriggerTestCallResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getTriggerTestCallMethod()

  public val triggerTestStreamCallMethod:
      MethodDescriptor<TriggerTestStreamCallRequest, TriggerTestStreamCallResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getTriggerTestStreamCallMethod()

  public val countTokensMethod: MethodDescriptor<CountTokensRequest, CountTokensResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getCountTokensMethod()

  public val scanPiiInjectionMethod:
      MethodDescriptor<ScanPiiInjectionRequest, ScanPiiInjectionResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getScanPiiInjectionMethod()

  public val shouldSampleMethod: MethodDescriptor<ShouldSampleRequest, ShouldSampleResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getShouldSampleMethod()

  public val getEmbeddingMethod: MethodDescriptor<GetEmbeddingRequest, GetEmbeddingResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getGetEmbeddingMethod()

  public val initMetricsMethod: MethodDescriptor<InitMetricsRequest, InitMetricsResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getInitMetricsMethod()

  public val getMetricsHealthMethod:
      MethodDescriptor<GetMetricsHealthRequest, GetMetricsHealthResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getGetMetricsHealthMethod()

  public val recordMetricsMethod: MethodDescriptor<RecordMetricsRequest, RecordMetricsResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getRecordMetricsMethod()

  public val recordMetricsBatchMethod:
      MethodDescriptor<RecordMetricsBatchRequest, RecordMetricsBatchResponse>
    @JvmStatic
    get() = InstrumentationControlServiceGrpc.getRecordMetricsBatchMethod()

  /**
   * A stub for issuing RPCs to a(n) llm.observability.v1.InstrumentationControlService service as
   * suspending coroutines.
   */
  @StubFor(InstrumentationControlServiceGrpc::class)
  public class InstrumentationControlServiceCoroutineStub @JvmOverloads constructor(
    channel: Channel,
    callOptions: CallOptions = DEFAULT,
  ) : AbstractCoroutineStub<InstrumentationControlServiceCoroutineStub>(channel, callOptions) {
    override fun build(channel: Channel, callOptions: CallOptions):
        InstrumentationControlServiceCoroutineStub =
        InstrumentationControlServiceCoroutineStub(channel, callOptions)

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun initInstrumentation(request: InitInstrumentationRequest, headers: Metadata =
        Metadata()): InitInstrumentationResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getInitInstrumentationMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun disableInstrumentation(request: DisableInstrumentationRequest,
        headers: Metadata = Metadata()): DisableInstrumentationResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getDisableInstrumentationMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun getStatus(request: GetStatusRequest, headers: Metadata = Metadata()):
        GetStatusResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getGetStatusMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun detectProvider(request: DetectProviderRequest, headers: Metadata =
        Metadata()): DetectProviderResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getDetectProviderMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun triggerTestCall(request: TriggerTestCallRequest, headers: Metadata =
        Metadata()): TriggerTestCallResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getTriggerTestCallMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun triggerTestStreamCall(request: TriggerTestStreamCallRequest,
        headers: Metadata = Metadata()): TriggerTestStreamCallResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getTriggerTestStreamCallMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun countTokens(request: CountTokensRequest, headers: Metadata = Metadata()):
        CountTokensResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getCountTokensMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun scanPiiInjection(request: ScanPiiInjectionRequest, headers: Metadata =
        Metadata()): ScanPiiInjectionResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getScanPiiInjectionMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun shouldSample(request: ShouldSampleRequest, headers: Metadata = Metadata()):
        ShouldSampleResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getShouldSampleMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun getEmbedding(request: GetEmbeddingRequest, headers: Metadata = Metadata()):
        GetEmbeddingResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getGetEmbeddingMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun initMetrics(request: InitMetricsRequest, headers: Metadata = Metadata()):
        InitMetricsResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getInitMetricsMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun getMetricsHealth(request: GetMetricsHealthRequest, headers: Metadata =
        Metadata()): GetMetricsHealthResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getGetMetricsHealthMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun recordMetrics(request: RecordMetricsRequest, headers: Metadata = Metadata()):
        RecordMetricsResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getRecordMetricsMethod(),
      request,
      callOptions,
      headers
    )

    /**
     * Executes this RPC and returns the response message, suspending until the RPC completes
     * with [`Status.OK`][io.grpc.Status].  If the RPC completes with another status, a
     * corresponding
     * [StatusException] is thrown.  If this coroutine is cancelled, the RPC is also cancelled
     * with the corresponding exception as a cause.
     *
     * @param request The request message to send to the server.
     *
     * @param headers Metadata to attach to the request.  Most users will not need this.
     *
     * @return The single response from the server.
     */
    public suspend fun recordMetricsBatch(request: RecordMetricsBatchRequest, headers: Metadata =
        Metadata()): RecordMetricsBatchResponse = unaryRpc(
      channel,
      InstrumentationControlServiceGrpc.getRecordMetricsBatchMethod(),
      request,
      callOptions,
      headers
    )
  }

  /**
   * Skeletal implementation of the llm.observability.v1.InstrumentationControlService service based
   * on Kotlin coroutines.
   */
  public abstract class InstrumentationControlServiceCoroutineImplBase(
    coroutineContext: CoroutineContext = EmptyCoroutineContext,
  ) : AbstractCoroutineServerImpl(coroutineContext) {
    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.InitInstrumentation.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun initInstrumentation(request: InitInstrumentationRequest):
        InitInstrumentationResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.InitInstrumentation is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.DisableInstrumentation.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun disableInstrumentation(request: DisableInstrumentationRequest):
        DisableInstrumentationResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.DisableInstrumentation is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.GetStatus.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun getStatus(request: GetStatusRequest): GetStatusResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.GetStatus is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.DetectProvider.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun detectProvider(request: DetectProviderRequest): DetectProviderResponse =
        throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.DetectProvider is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.TriggerTestCall.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun triggerTestCall(request: TriggerTestCallRequest):
        TriggerTestCallResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.TriggerTestCall is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.TriggerTestStreamCall.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun triggerTestStreamCall(request: TriggerTestStreamCallRequest):
        TriggerTestStreamCallResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.TriggerTestStreamCall is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.CountTokens.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun countTokens(request: CountTokensRequest): CountTokensResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.CountTokens is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.ScanPiiInjection.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun scanPiiInjection(request: ScanPiiInjectionRequest):
        ScanPiiInjectionResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.ScanPiiInjection is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.ShouldSample.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun shouldSample(request: ShouldSampleRequest): ShouldSampleResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.ShouldSample is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.GetEmbedding.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun getEmbedding(request: GetEmbeddingRequest): GetEmbeddingResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.GetEmbedding is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.InitMetrics.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun initMetrics(request: InitMetricsRequest): InitMetricsResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.InitMetrics is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.GetMetricsHealth.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun getMetricsHealth(request: GetMetricsHealthRequest):
        GetMetricsHealthResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.GetMetricsHealth is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.RecordMetrics.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun recordMetrics(request: RecordMetricsRequest): RecordMetricsResponse =
        throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.RecordMetrics is unimplemented"))

    /**
     * Returns the response to an RPC for
     * llm.observability.v1.InstrumentationControlService.RecordMetricsBatch.
     *
     * If this method fails with a [StatusException], the RPC will fail with the corresponding
     * [io.grpc.Status].  If this method fails with a [java.util.concurrent.CancellationException],
     * the RPC will fail
     * with status `Status.CANCELLED`.  If this method fails for any other reason, the RPC will
     * fail with `Status.UNKNOWN` with the exception as a cause.
     *
     * @param request The request from the client.
     */
    public open suspend fun recordMetricsBatch(request: RecordMetricsBatchRequest):
        RecordMetricsBatchResponse = throw
        StatusException(UNIMPLEMENTED.withDescription("Method llm.observability.v1.InstrumentationControlService.RecordMetricsBatch is unimplemented"))

    final override fun bindService(): ServerServiceDefinition = builder(getServiceDescriptor())
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getInitInstrumentationMethod(),
      implementation = ::initInstrumentation
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getDisableInstrumentationMethod(),
      implementation = ::disableInstrumentation
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getGetStatusMethod(),
      implementation = ::getStatus
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getDetectProviderMethod(),
      implementation = ::detectProvider
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getTriggerTestCallMethod(),
      implementation = ::triggerTestCall
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getTriggerTestStreamCallMethod(),
      implementation = ::triggerTestStreamCall
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getCountTokensMethod(),
      implementation = ::countTokens
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getScanPiiInjectionMethod(),
      implementation = ::scanPiiInjection
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getShouldSampleMethod(),
      implementation = ::shouldSample
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getGetEmbeddingMethod(),
      implementation = ::getEmbedding
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getInitMetricsMethod(),
      implementation = ::initMetrics
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getGetMetricsHealthMethod(),
      implementation = ::getMetricsHealth
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getRecordMetricsMethod(),
      implementation = ::recordMetrics
    ))
      .addMethod(unaryServerMethodDefinition(
      context = this.context,
      descriptor = InstrumentationControlServiceGrpc.getRecordMetricsBatchMethod(),
      implementation = ::recordMetricsBatch
    )).build()
  }
}
