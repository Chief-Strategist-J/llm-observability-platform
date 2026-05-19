<?php
// GENERATED CODE -- DO NOT EDIT!

namespace LlmObservability\Platform\V1;

/**
 * Service definition for remote instrumentation control
 */
class InstrumentationControlServiceClient extends \Grpc\BaseStub {

    /**
     * @param string $hostname hostname
     * @param array $opts channel options
     * @param \Grpc\Channel $channel (optional) re-use channel object
     */
    public function __construct($hostname, $opts, $channel = null) {
        parent::__construct($hostname, $opts, $channel);
    }

    /**
     * @param \LlmObservability\Platform\V1\InitInstrumentationRequest $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function InitInstrumentation(\LlmObservability\Platform\V1\InitInstrumentationRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.InstrumentationControlService/InitInstrumentation',
        $argument,
        ['\LlmObservability\Platform\V1\InitInstrumentationResponse', 'decode'],
        $metadata, $options);
    }

    /**
     * @param \LlmObservability\Platform\V1\DisableInstrumentationRequest $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function DisableInstrumentation(\LlmObservability\Platform\V1\DisableInstrumentationRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.InstrumentationControlService/DisableInstrumentation',
        $argument,
        ['\LlmObservability\Platform\V1\DisableInstrumentationResponse', 'decode'],
        $metadata, $options);
    }

    /**
     * @param \LlmObservability\Platform\V1\GetStatusRequest $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function GetStatus(\LlmObservability\Platform\V1\GetStatusRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.InstrumentationControlService/GetStatus',
        $argument,
        ['\LlmObservability\Platform\V1\GetStatusResponse', 'decode'],
        $metadata, $options);
    }

    /**
     * @param \LlmObservability\Platform\V1\DetectProviderRequest $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function DetectProvider(\LlmObservability\Platform\V1\DetectProviderRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.InstrumentationControlService/DetectProvider',
        $argument,
        ['\LlmObservability\Platform\V1\DetectProviderResponse', 'decode'],
        $metadata, $options);
    }

    /**
     * @param \LlmObservability\Platform\V1\TriggerTestCallRequest $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function TriggerTestCall(\LlmObservability\Platform\V1\TriggerTestCallRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.InstrumentationControlService/TriggerTestCall',
        $argument,
        ['\LlmObservability\Platform\V1\TriggerTestCallResponse', 'decode'],
        $metadata, $options);
    }

    /**
     * @param \LlmObservability\Platform\V1\TriggerTestStreamCallRequest $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function TriggerTestStreamCall(\LlmObservability\Platform\V1\TriggerTestStreamCallRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.InstrumentationControlService/TriggerTestStreamCall',
        $argument,
        ['\LlmObservability\Platform\V1\TriggerTestStreamCallResponse', 'decode'],
        $metadata, $options);
    }

    /**
     * @param \LlmObservability\Platform\V1\CountTokensRequest $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function CountTokens(\LlmObservability\Platform\V1\CountTokensRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.InstrumentationControlService/CountTokens',
        $argument,
        ['\LlmObservability\Platform\V1\CountTokensResponse', 'decode'],
        $metadata, $options);
    }

    /**
     * @param \LlmObservability\Platform\V1\ScanPiiInjectionRequest $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function ScanPiiInjection(\LlmObservability\Platform\V1\ScanPiiInjectionRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.InstrumentationControlService/ScanPiiInjection',
        $argument,
        ['\LlmObservability\Platform\V1\ScanPiiInjectionResponse', 'decode'],
        $metadata, $options);
    }

}
