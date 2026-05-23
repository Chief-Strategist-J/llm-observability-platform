// @generated
/// Generated client implementations.
pub mod instrumentation_control_service_client {
    #![allow(unused_variables, dead_code, missing_docs, clippy::let_unit_value)]
    use tonic::codegen::*;
    use tonic::codegen::http::Uri;
    #[derive(Debug, Clone)]
    pub struct InstrumentationControlServiceClient<T> {
        inner: tonic::client::Grpc<T>,
    }
    impl InstrumentationControlServiceClient<tonic::transport::Channel> {
        /// Attempt to create a new client by connecting to a given endpoint.
        pub async fn connect<D>(dst: D) -> Result<Self, tonic::transport::Error>
        where
            D: TryInto<tonic::transport::Endpoint>,
            D::Error: Into<StdError>,
        {
            let conn = tonic::transport::Endpoint::new(dst)?.connect().await?;
            Ok(Self::new(conn))
        }
    }
    impl<T> InstrumentationControlServiceClient<T>
    where
        T: tonic::client::GrpcService<tonic::body::BoxBody>,
        T::Error: Into<StdError>,
        T::ResponseBody: Body<Data = Bytes> + Send + 'static,
        <T::ResponseBody as Body>::Error: Into<StdError> + Send,
    {
        pub fn new(inner: T) -> Self {
            let inner = tonic::client::Grpc::new(inner);
            Self { inner }
        }
        pub fn with_origin(inner: T, origin: Uri) -> Self {
            let inner = tonic::client::Grpc::with_origin(inner, origin);
            Self { inner }
        }
        pub fn with_interceptor<F>(
            inner: T,
            interceptor: F,
        ) -> InstrumentationControlServiceClient<InterceptedService<T, F>>
        where
            F: tonic::service::Interceptor,
            T::ResponseBody: Default,
            T: tonic::codegen::Service<
                http::Request<tonic::body::BoxBody>,
                Response = http::Response<
                    <T as tonic::client::GrpcService<tonic::body::BoxBody>>::ResponseBody,
                >,
            >,
            <T as tonic::codegen::Service<
                http::Request<tonic::body::BoxBody>,
            >>::Error: Into<StdError> + Send + Sync,
        {
            InstrumentationControlServiceClient::new(
                InterceptedService::new(inner, interceptor),
            )
        }
        /// Compress requests with the given encoding.
        ///
        /// This requires the server to support it otherwise it might respond with an
        /// error.
        #[must_use]
        pub fn send_compressed(mut self, encoding: CompressionEncoding) -> Self {
            self.inner = self.inner.send_compressed(encoding);
            self
        }
        /// Enable decompressing responses.
        #[must_use]
        pub fn accept_compressed(mut self, encoding: CompressionEncoding) -> Self {
            self.inner = self.inner.accept_compressed(encoding);
            self
        }
        /// Limits the maximum size of a decoded message.
        ///
        /// Default: `4MB`
        #[must_use]
        pub fn max_decoding_message_size(mut self, limit: usize) -> Self {
            self.inner = self.inner.max_decoding_message_size(limit);
            self
        }
        /// Limits the maximum size of an encoded message.
        ///
        /// Default: `usize::MAX`
        #[must_use]
        pub fn max_encoding_message_size(mut self, limit: usize) -> Self {
            self.inner = self.inner.max_encoding_message_size(limit);
            self
        }
        pub async fn init_instrumentation(
            &mut self,
            request: impl tonic::IntoRequest<super::InitInstrumentationRequest>,
        ) -> std::result::Result<
            tonic::Response<super::InitInstrumentationResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/InitInstrumentation",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "InitInstrumentation",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn disable_instrumentation(
            &mut self,
            request: impl tonic::IntoRequest<super::DisableInstrumentationRequest>,
        ) -> std::result::Result<
            tonic::Response<super::DisableInstrumentationResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/DisableInstrumentation",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "DisableInstrumentation",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn get_status(
            &mut self,
            request: impl tonic::IntoRequest<super::GetStatusRequest>,
        ) -> std::result::Result<
            tonic::Response<super::GetStatusResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/GetStatus",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "GetStatus",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn detect_provider(
            &mut self,
            request: impl tonic::IntoRequest<super::DetectProviderRequest>,
        ) -> std::result::Result<
            tonic::Response<super::DetectProviderResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/DetectProvider",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "DetectProvider",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn trigger_test_call(
            &mut self,
            request: impl tonic::IntoRequest<super::TriggerTestCallRequest>,
        ) -> std::result::Result<
            tonic::Response<super::TriggerTestCallResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/TriggerTestCall",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "TriggerTestCall",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn trigger_test_stream_call(
            &mut self,
            request: impl tonic::IntoRequest<super::TriggerTestStreamCallRequest>,
        ) -> std::result::Result<
            tonic::Response<super::TriggerTestStreamCallResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/TriggerTestStreamCall",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "TriggerTestStreamCall",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn count_tokens(
            &mut self,
            request: impl tonic::IntoRequest<super::CountTokensRequest>,
        ) -> std::result::Result<
            tonic::Response<super::CountTokensResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/CountTokens",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "CountTokens",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn scan_pii_injection(
            &mut self,
            request: impl tonic::IntoRequest<super::ScanPiiInjectionRequest>,
        ) -> std::result::Result<
            tonic::Response<super::ScanPiiInjectionResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/ScanPiiInjection",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "ScanPiiInjection",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn should_sample(
            &mut self,
            request: impl tonic::IntoRequest<super::ShouldSampleRequest>,
        ) -> std::result::Result<
            tonic::Response<super::ShouldSampleResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/ShouldSample",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "ShouldSample",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn get_embedding(
            &mut self,
            request: impl tonic::IntoRequest<super::GetEmbeddingRequest>,
        ) -> std::result::Result<
            tonic::Response<super::GetEmbeddingResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/GetEmbedding",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "GetEmbedding",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn track_fallback(
            &mut self,
            request: impl tonic::IntoRequest<super::TrackFallbackRequest>,
        ) -> std::result::Result<
            tonic::Response<super::TrackFallbackResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/TrackFallback",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "TrackFallback",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn clear_fallback_tracker(
            &mut self,
            request: impl tonic::IntoRequest<super::ClearFallbackTrackerRequest>,
        ) -> std::result::Result<
            tonic::Response<super::ClearFallbackTrackerResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/ClearFallbackTracker",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "ClearFallbackTracker",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn init_metrics(
            &mut self,
            request: impl tonic::IntoRequest<super::InitMetricsRequest>,
        ) -> std::result::Result<
            tonic::Response<super::InitMetricsResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/InitMetrics",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "InitMetrics",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn get_metrics_health(
            &mut self,
            request: impl tonic::IntoRequest<super::GetMetricsHealthRequest>,
        ) -> std::result::Result<
            tonic::Response<super::GetMetricsHealthResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/GetMetricsHealth",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "GetMetricsHealth",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn record_metrics(
            &mut self,
            request: impl tonic::IntoRequest<super::RecordMetricsRequest>,
        ) -> std::result::Result<
            tonic::Response<super::RecordMetricsResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/RecordMetrics",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "RecordMetrics",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
        pub async fn record_metrics_batch(
            &mut self,
            request: impl tonic::IntoRequest<super::RecordMetricsBatchRequest>,
        ) -> std::result::Result<
            tonic::Response<super::RecordMetricsBatchResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.InstrumentationControlService/RecordMetricsBatch",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.InstrumentationControlService",
                        "RecordMetricsBatch",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
    }
}
/// Generated server implementations.
pub mod instrumentation_control_service_server {
    #![allow(unused_variables, dead_code, missing_docs, clippy::let_unit_value)]
    use tonic::codegen::*;
    /// Generated trait containing gRPC methods that should be implemented for use with InstrumentationControlServiceServer.
    #[async_trait]
    pub trait InstrumentationControlService: Send + Sync + 'static {
        async fn init_instrumentation(
            &self,
            request: tonic::Request<super::InitInstrumentationRequest>,
        ) -> std::result::Result<
            tonic::Response<super::InitInstrumentationResponse>,
            tonic::Status,
        >;
        async fn disable_instrumentation(
            &self,
            request: tonic::Request<super::DisableInstrumentationRequest>,
        ) -> std::result::Result<
            tonic::Response<super::DisableInstrumentationResponse>,
            tonic::Status,
        >;
        async fn get_status(
            &self,
            request: tonic::Request<super::GetStatusRequest>,
        ) -> std::result::Result<
            tonic::Response<super::GetStatusResponse>,
            tonic::Status,
        >;
        async fn detect_provider(
            &self,
            request: tonic::Request<super::DetectProviderRequest>,
        ) -> std::result::Result<
            tonic::Response<super::DetectProviderResponse>,
            tonic::Status,
        >;
        async fn trigger_test_call(
            &self,
            request: tonic::Request<super::TriggerTestCallRequest>,
        ) -> std::result::Result<
            tonic::Response<super::TriggerTestCallResponse>,
            tonic::Status,
        >;
        async fn trigger_test_stream_call(
            &self,
            request: tonic::Request<super::TriggerTestStreamCallRequest>,
        ) -> std::result::Result<
            tonic::Response<super::TriggerTestStreamCallResponse>,
            tonic::Status,
        >;
        async fn count_tokens(
            &self,
            request: tonic::Request<super::CountTokensRequest>,
        ) -> std::result::Result<
            tonic::Response<super::CountTokensResponse>,
            tonic::Status,
        >;
        async fn scan_pii_injection(
            &self,
            request: tonic::Request<super::ScanPiiInjectionRequest>,
        ) -> std::result::Result<
            tonic::Response<super::ScanPiiInjectionResponse>,
            tonic::Status,
        >;
        async fn should_sample(
            &self,
            request: tonic::Request<super::ShouldSampleRequest>,
        ) -> std::result::Result<
            tonic::Response<super::ShouldSampleResponse>,
            tonic::Status,
        >;
        async fn get_embedding(
            &self,
            request: tonic::Request<super::GetEmbeddingRequest>,
        ) -> std::result::Result<
            tonic::Response<super::GetEmbeddingResponse>,
            tonic::Status,
        >;
        async fn track_fallback(
            &self,
            request: tonic::Request<super::TrackFallbackRequest>,
        ) -> std::result::Result<
            tonic::Response<super::TrackFallbackResponse>,
            tonic::Status,
        >;
        async fn clear_fallback_tracker(
            &self,
            request: tonic::Request<super::ClearFallbackTrackerRequest>,
        ) -> std::result::Result<
            tonic::Response<super::ClearFallbackTrackerResponse>,
            tonic::Status,
        >;
        async fn init_metrics(
            &self,
            request: tonic::Request<super::InitMetricsRequest>,
        ) -> std::result::Result<
            tonic::Response<super::InitMetricsResponse>,
            tonic::Status,
        >;
        async fn get_metrics_health(
            &self,
            request: tonic::Request<super::GetMetricsHealthRequest>,
        ) -> std::result::Result<
            tonic::Response<super::GetMetricsHealthResponse>,
            tonic::Status,
        >;
        async fn record_metrics(
            &self,
            request: tonic::Request<super::RecordMetricsRequest>,
        ) -> std::result::Result<
            tonic::Response<super::RecordMetricsResponse>,
            tonic::Status,
        >;
        async fn record_metrics_batch(
            &self,
            request: tonic::Request<super::RecordMetricsBatchRequest>,
        ) -> std::result::Result<
            tonic::Response<super::RecordMetricsBatchResponse>,
            tonic::Status,
        >;
    }
    #[derive(Debug)]
    pub struct InstrumentationControlServiceServer<T: InstrumentationControlService> {
        inner: _Inner<T>,
        accept_compression_encodings: EnabledCompressionEncodings,
        send_compression_encodings: EnabledCompressionEncodings,
        max_decoding_message_size: Option<usize>,
        max_encoding_message_size: Option<usize>,
    }
    struct _Inner<T>(Arc<T>);
    impl<T: InstrumentationControlService> InstrumentationControlServiceServer<T> {
        pub fn new(inner: T) -> Self {
            Self::from_arc(Arc::new(inner))
        }
        pub fn from_arc(inner: Arc<T>) -> Self {
            let inner = _Inner(inner);
            Self {
                inner,
                accept_compression_encodings: Default::default(),
                send_compression_encodings: Default::default(),
                max_decoding_message_size: None,
                max_encoding_message_size: None,
            }
        }
        pub fn with_interceptor<F>(
            inner: T,
            interceptor: F,
        ) -> InterceptedService<Self, F>
        where
            F: tonic::service::Interceptor,
        {
            InterceptedService::new(Self::new(inner), interceptor)
        }
        /// Enable decompressing requests with the given encoding.
        #[must_use]
        pub fn accept_compressed(mut self, encoding: CompressionEncoding) -> Self {
            self.accept_compression_encodings.enable(encoding);
            self
        }
        /// Compress responses with the given encoding, if the client supports it.
        #[must_use]
        pub fn send_compressed(mut self, encoding: CompressionEncoding) -> Self {
            self.send_compression_encodings.enable(encoding);
            self
        }
        /// Limits the maximum size of a decoded message.
        ///
        /// Default: `4MB`
        #[must_use]
        pub fn max_decoding_message_size(mut self, limit: usize) -> Self {
            self.max_decoding_message_size = Some(limit);
            self
        }
        /// Limits the maximum size of an encoded message.
        ///
        /// Default: `usize::MAX`
        #[must_use]
        pub fn max_encoding_message_size(mut self, limit: usize) -> Self {
            self.max_encoding_message_size = Some(limit);
            self
        }
    }
    impl<T, B> tonic::codegen::Service<http::Request<B>>
    for InstrumentationControlServiceServer<T>
    where
        T: InstrumentationControlService,
        B: Body + Send + 'static,
        B::Error: Into<StdError> + Send + 'static,
    {
        type Response = http::Response<tonic::body::BoxBody>;
        type Error = std::convert::Infallible;
        type Future = BoxFuture<Self::Response, Self::Error>;
        fn poll_ready(
            &mut self,
            _cx: &mut Context<'_>,
        ) -> Poll<std::result::Result<(), Self::Error>> {
            Poll::Ready(Ok(()))
        }
        fn call(&mut self, req: http::Request<B>) -> Self::Future {
            let inner = self.inner.clone();
            match req.uri().path() {
                "/llm.observability.v1.InstrumentationControlService/InitInstrumentation" => {
                    #[allow(non_camel_case_types)]
                    struct InitInstrumentationSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::InitInstrumentationRequest>
                    for InitInstrumentationSvc<T> {
                        type Response = super::InitInstrumentationResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::InitInstrumentationRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::init_instrumentation(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = InitInstrumentationSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/DisableInstrumentation" => {
                    #[allow(non_camel_case_types)]
                    struct DisableInstrumentationSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::DisableInstrumentationRequest>
                    for DisableInstrumentationSvc<T> {
                        type Response = super::DisableInstrumentationResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::DisableInstrumentationRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::disable_instrumentation(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = DisableInstrumentationSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/GetStatus" => {
                    #[allow(non_camel_case_types)]
                    struct GetStatusSvc<T: InstrumentationControlService>(pub Arc<T>);
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::GetStatusRequest>
                    for GetStatusSvc<T> {
                        type Response = super::GetStatusResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::GetStatusRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::get_status(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = GetStatusSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/DetectProvider" => {
                    #[allow(non_camel_case_types)]
                    struct DetectProviderSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::DetectProviderRequest>
                    for DetectProviderSvc<T> {
                        type Response = super::DetectProviderResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::DetectProviderRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::detect_provider(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = DetectProviderSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/TriggerTestCall" => {
                    #[allow(non_camel_case_types)]
                    struct TriggerTestCallSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::TriggerTestCallRequest>
                    for TriggerTestCallSvc<T> {
                        type Response = super::TriggerTestCallResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::TriggerTestCallRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::trigger_test_call(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = TriggerTestCallSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/TriggerTestStreamCall" => {
                    #[allow(non_camel_case_types)]
                    struct TriggerTestStreamCallSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::TriggerTestStreamCallRequest>
                    for TriggerTestStreamCallSvc<T> {
                        type Response = super::TriggerTestStreamCallResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::TriggerTestStreamCallRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::trigger_test_stream_call(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = TriggerTestStreamCallSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/CountTokens" => {
                    #[allow(non_camel_case_types)]
                    struct CountTokensSvc<T: InstrumentationControlService>(pub Arc<T>);
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::CountTokensRequest>
                    for CountTokensSvc<T> {
                        type Response = super::CountTokensResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::CountTokensRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::count_tokens(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = CountTokensSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/ScanPiiInjection" => {
                    #[allow(non_camel_case_types)]
                    struct ScanPiiInjectionSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::ScanPiiInjectionRequest>
                    for ScanPiiInjectionSvc<T> {
                        type Response = super::ScanPiiInjectionResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::ScanPiiInjectionRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::scan_pii_injection(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = ScanPiiInjectionSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/ShouldSample" => {
                    #[allow(non_camel_case_types)]
                    struct ShouldSampleSvc<T: InstrumentationControlService>(pub Arc<T>);
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::ShouldSampleRequest>
                    for ShouldSampleSvc<T> {
                        type Response = super::ShouldSampleResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::ShouldSampleRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::should_sample(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = ShouldSampleSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/GetEmbedding" => {
                    #[allow(non_camel_case_types)]
                    struct GetEmbeddingSvc<T: InstrumentationControlService>(pub Arc<T>);
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::GetEmbeddingRequest>
                    for GetEmbeddingSvc<T> {
                        type Response = super::GetEmbeddingResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::GetEmbeddingRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::get_embedding(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = GetEmbeddingSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/TrackFallback" => {
                    #[allow(non_camel_case_types)]
                    struct TrackFallbackSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::TrackFallbackRequest>
                    for TrackFallbackSvc<T> {
                        type Response = super::TrackFallbackResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::TrackFallbackRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::track_fallback(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = TrackFallbackSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/ClearFallbackTracker" => {
                    #[allow(non_camel_case_types)]
                    struct ClearFallbackTrackerSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::ClearFallbackTrackerRequest>
                    for ClearFallbackTrackerSvc<T> {
                        type Response = super::ClearFallbackTrackerResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::ClearFallbackTrackerRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::clear_fallback_tracker(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = ClearFallbackTrackerSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/InitMetrics" => {
                    #[allow(non_camel_case_types)]
                    struct InitMetricsSvc<T: InstrumentationControlService>(pub Arc<T>);
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::InitMetricsRequest>
                    for InitMetricsSvc<T> {
                        type Response = super::InitMetricsResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::InitMetricsRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::init_metrics(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = InitMetricsSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/GetMetricsHealth" => {
                    #[allow(non_camel_case_types)]
                    struct GetMetricsHealthSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::GetMetricsHealthRequest>
                    for GetMetricsHealthSvc<T> {
                        type Response = super::GetMetricsHealthResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::GetMetricsHealthRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::get_metrics_health(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = GetMetricsHealthSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/RecordMetrics" => {
                    #[allow(non_camel_case_types)]
                    struct RecordMetricsSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::RecordMetricsRequest>
                    for RecordMetricsSvc<T> {
                        type Response = super::RecordMetricsResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::RecordMetricsRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::record_metrics(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = RecordMetricsSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                "/llm.observability.v1.InstrumentationControlService/RecordMetricsBatch" => {
                    #[allow(non_camel_case_types)]
                    struct RecordMetricsBatchSvc<T: InstrumentationControlService>(
                        pub Arc<T>,
                    );
                    impl<
                        T: InstrumentationControlService,
                    > tonic::server::UnaryService<super::RecordMetricsBatchRequest>
                    for RecordMetricsBatchSvc<T> {
                        type Response = super::RecordMetricsBatchResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::RecordMetricsBatchRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as InstrumentationControlService>::record_metrics_batch(
                                        &inner,
                                        request,
                                    )
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = RecordMetricsBatchSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                _ => {
                    Box::pin(async move {
                        Ok(
                            http::Response::builder()
                                .status(200)
                                .header("grpc-status", "12")
                                .header("content-type", "application/grpc")
                                .body(empty_body())
                                .unwrap(),
                        )
                    })
                }
            }
        }
    }
    impl<T: InstrumentationControlService> Clone
    for InstrumentationControlServiceServer<T> {
        fn clone(&self) -> Self {
            let inner = self.inner.clone();
            Self {
                inner,
                accept_compression_encodings: self.accept_compression_encodings,
                send_compression_encodings: self.send_compression_encodings,
                max_decoding_message_size: self.max_decoding_message_size,
                max_encoding_message_size: self.max_encoding_message_size,
            }
        }
    }
    impl<T: InstrumentationControlService> Clone for _Inner<T> {
        fn clone(&self) -> Self {
            Self(Arc::clone(&self.0))
        }
    }
    impl<T: std::fmt::Debug> std::fmt::Debug for _Inner<T> {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            write!(f, "{:?}", self.0)
        }
    }
    impl<T: InstrumentationControlService> tonic::server::NamedService
    for InstrumentationControlServiceServer<T> {
        const NAME: &'static str = "llm.observability.v1.InstrumentationControlService";
    }
}
/// Generated client implementations.
pub mod span_ingestion_service_client {
    #![allow(unused_variables, dead_code, missing_docs, clippy::let_unit_value)]
    use tonic::codegen::*;
    use tonic::codegen::http::Uri;
    #[derive(Debug, Clone)]
    pub struct SpanIngestionServiceClient<T> {
        inner: tonic::client::Grpc<T>,
    }
    impl SpanIngestionServiceClient<tonic::transport::Channel> {
        /// Attempt to create a new client by connecting to a given endpoint.
        pub async fn connect<D>(dst: D) -> Result<Self, tonic::transport::Error>
        where
            D: TryInto<tonic::transport::Endpoint>,
            D::Error: Into<StdError>,
        {
            let conn = tonic::transport::Endpoint::new(dst)?.connect().await?;
            Ok(Self::new(conn))
        }
    }
    impl<T> SpanIngestionServiceClient<T>
    where
        T: tonic::client::GrpcService<tonic::body::BoxBody>,
        T::Error: Into<StdError>,
        T::ResponseBody: Body<Data = Bytes> + Send + 'static,
        <T::ResponseBody as Body>::Error: Into<StdError> + Send,
    {
        pub fn new(inner: T) -> Self {
            let inner = tonic::client::Grpc::new(inner);
            Self { inner }
        }
        pub fn with_origin(inner: T, origin: Uri) -> Self {
            let inner = tonic::client::Grpc::with_origin(inner, origin);
            Self { inner }
        }
        pub fn with_interceptor<F>(
            inner: T,
            interceptor: F,
        ) -> SpanIngestionServiceClient<InterceptedService<T, F>>
        where
            F: tonic::service::Interceptor,
            T::ResponseBody: Default,
            T: tonic::codegen::Service<
                http::Request<tonic::body::BoxBody>,
                Response = http::Response<
                    <T as tonic::client::GrpcService<tonic::body::BoxBody>>::ResponseBody,
                >,
            >,
            <T as tonic::codegen::Service<
                http::Request<tonic::body::BoxBody>,
            >>::Error: Into<StdError> + Send + Sync,
        {
            SpanIngestionServiceClient::new(InterceptedService::new(inner, interceptor))
        }
        /// Compress requests with the given encoding.
        ///
        /// This requires the server to support it otherwise it might respond with an
        /// error.
        #[must_use]
        pub fn send_compressed(mut self, encoding: CompressionEncoding) -> Self {
            self.inner = self.inner.send_compressed(encoding);
            self
        }
        /// Enable decompressing responses.
        #[must_use]
        pub fn accept_compressed(mut self, encoding: CompressionEncoding) -> Self {
            self.inner = self.inner.accept_compressed(encoding);
            self
        }
        /// Limits the maximum size of a decoded message.
        ///
        /// Default: `4MB`
        #[must_use]
        pub fn max_decoding_message_size(mut self, limit: usize) -> Self {
            self.inner = self.inner.max_decoding_message_size(limit);
            self
        }
        /// Limits the maximum size of an encoded message.
        ///
        /// Default: `usize::MAX`
        #[must_use]
        pub fn max_encoding_message_size(mut self, limit: usize) -> Self {
            self.inner = self.inner.max_encoding_message_size(limit);
            self
        }
        pub async fn record_span(
            &mut self,
            request: impl tonic::IntoRequest<super::RecordSpanRequest>,
        ) -> std::result::Result<
            tonic::Response<super::RecordSpanResponse>,
            tonic::Status,
        > {
            self.inner
                .ready()
                .await
                .map_err(|e| {
                    tonic::Status::new(
                        tonic::Code::Unknown,
                        format!("Service was not ready: {}", e.into()),
                    )
                })?;
            let codec = tonic::codec::ProstCodec::default();
            let path = http::uri::PathAndQuery::from_static(
                "/llm.observability.v1.SpanIngestionService/RecordSpan",
            );
            let mut req = request.into_request();
            req.extensions_mut()
                .insert(
                    GrpcMethod::new(
                        "llm.observability.v1.SpanIngestionService",
                        "RecordSpan",
                    ),
                );
            self.inner.unary(req, path, codec).await
        }
    }
}
/// Generated server implementations.
pub mod span_ingestion_service_server {
    #![allow(unused_variables, dead_code, missing_docs, clippy::let_unit_value)]
    use tonic::codegen::*;
    /// Generated trait containing gRPC methods that should be implemented for use with SpanIngestionServiceServer.
    #[async_trait]
    pub trait SpanIngestionService: Send + Sync + 'static {
        async fn record_span(
            &self,
            request: tonic::Request<super::RecordSpanRequest>,
        ) -> std::result::Result<
            tonic::Response<super::RecordSpanResponse>,
            tonic::Status,
        >;
    }
    #[derive(Debug)]
    pub struct SpanIngestionServiceServer<T: SpanIngestionService> {
        inner: _Inner<T>,
        accept_compression_encodings: EnabledCompressionEncodings,
        send_compression_encodings: EnabledCompressionEncodings,
        max_decoding_message_size: Option<usize>,
        max_encoding_message_size: Option<usize>,
    }
    struct _Inner<T>(Arc<T>);
    impl<T: SpanIngestionService> SpanIngestionServiceServer<T> {
        pub fn new(inner: T) -> Self {
            Self::from_arc(Arc::new(inner))
        }
        pub fn from_arc(inner: Arc<T>) -> Self {
            let inner = _Inner(inner);
            Self {
                inner,
                accept_compression_encodings: Default::default(),
                send_compression_encodings: Default::default(),
                max_decoding_message_size: None,
                max_encoding_message_size: None,
            }
        }
        pub fn with_interceptor<F>(
            inner: T,
            interceptor: F,
        ) -> InterceptedService<Self, F>
        where
            F: tonic::service::Interceptor,
        {
            InterceptedService::new(Self::new(inner), interceptor)
        }
        /// Enable decompressing requests with the given encoding.
        #[must_use]
        pub fn accept_compressed(mut self, encoding: CompressionEncoding) -> Self {
            self.accept_compression_encodings.enable(encoding);
            self
        }
        /// Compress responses with the given encoding, if the client supports it.
        #[must_use]
        pub fn send_compressed(mut self, encoding: CompressionEncoding) -> Self {
            self.send_compression_encodings.enable(encoding);
            self
        }
        /// Limits the maximum size of a decoded message.
        ///
        /// Default: `4MB`
        #[must_use]
        pub fn max_decoding_message_size(mut self, limit: usize) -> Self {
            self.max_decoding_message_size = Some(limit);
            self
        }
        /// Limits the maximum size of an encoded message.
        ///
        /// Default: `usize::MAX`
        #[must_use]
        pub fn max_encoding_message_size(mut self, limit: usize) -> Self {
            self.max_encoding_message_size = Some(limit);
            self
        }
    }
    impl<T, B> tonic::codegen::Service<http::Request<B>>
    for SpanIngestionServiceServer<T>
    where
        T: SpanIngestionService,
        B: Body + Send + 'static,
        B::Error: Into<StdError> + Send + 'static,
    {
        type Response = http::Response<tonic::body::BoxBody>;
        type Error = std::convert::Infallible;
        type Future = BoxFuture<Self::Response, Self::Error>;
        fn poll_ready(
            &mut self,
            _cx: &mut Context<'_>,
        ) -> Poll<std::result::Result<(), Self::Error>> {
            Poll::Ready(Ok(()))
        }
        fn call(&mut self, req: http::Request<B>) -> Self::Future {
            let inner = self.inner.clone();
            match req.uri().path() {
                "/llm.observability.v1.SpanIngestionService/RecordSpan" => {
                    #[allow(non_camel_case_types)]
                    struct RecordSpanSvc<T: SpanIngestionService>(pub Arc<T>);
                    impl<
                        T: SpanIngestionService,
                    > tonic::server::UnaryService<super::RecordSpanRequest>
                    for RecordSpanSvc<T> {
                        type Response = super::RecordSpanResponse;
                        type Future = BoxFuture<
                            tonic::Response<Self::Response>,
                            tonic::Status,
                        >;
                        fn call(
                            &mut self,
                            request: tonic::Request<super::RecordSpanRequest>,
                        ) -> Self::Future {
                            let inner = Arc::clone(&self.0);
                            let fut = async move {
                                <T as SpanIngestionService>::record_span(&inner, request)
                                    .await
                            };
                            Box::pin(fut)
                        }
                    }
                    let accept_compression_encodings = self.accept_compression_encodings;
                    let send_compression_encodings = self.send_compression_encodings;
                    let max_decoding_message_size = self.max_decoding_message_size;
                    let max_encoding_message_size = self.max_encoding_message_size;
                    let inner = self.inner.clone();
                    let fut = async move {
                        let inner = inner.0;
                        let method = RecordSpanSvc(inner);
                        let codec = tonic::codec::ProstCodec::default();
                        let mut grpc = tonic::server::Grpc::new(codec)
                            .apply_compression_config(
                                accept_compression_encodings,
                                send_compression_encodings,
                            )
                            .apply_max_message_size_config(
                                max_decoding_message_size,
                                max_encoding_message_size,
                            );
                        let res = grpc.unary(method, req).await;
                        Ok(res)
                    };
                    Box::pin(fut)
                }
                _ => {
                    Box::pin(async move {
                        Ok(
                            http::Response::builder()
                                .status(200)
                                .header("grpc-status", "12")
                                .header("content-type", "application/grpc")
                                .body(empty_body())
                                .unwrap(),
                        )
                    })
                }
            }
        }
    }
    impl<T: SpanIngestionService> Clone for SpanIngestionServiceServer<T> {
        fn clone(&self) -> Self {
            let inner = self.inner.clone();
            Self {
                inner,
                accept_compression_encodings: self.accept_compression_encodings,
                send_compression_encodings: self.send_compression_encodings,
                max_decoding_message_size: self.max_decoding_message_size,
                max_encoding_message_size: self.max_encoding_message_size,
            }
        }
    }
    impl<T: SpanIngestionService> Clone for _Inner<T> {
        fn clone(&self) -> Self {
            Self(Arc::clone(&self.0))
        }
    }
    impl<T: std::fmt::Debug> std::fmt::Debug for _Inner<T> {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            write!(f, "{:?}", self.0)
        }
    }
    impl<T: SpanIngestionService> tonic::server::NamedService
    for SpanIngestionServiceServer<T> {
        const NAME: &'static str = "llm.observability.v1.SpanIngestionService";
    }
}
