<?php
// GENERATED CODE -- DO NOT EDIT!

namespace LlmObservability\Platform\V1;

/**
 * Service definition for direct gRPC ingestion
 */
class SpanIngestionServiceClient extends \Grpc\BaseStub {

    /**
     * @param string $hostname hostname
     * @param array $opts channel options
     * @param \Grpc\Channel $channel (optional) re-use channel object
     */
    public function __construct($hostname, $opts, $channel = null) {
        parent::__construct($hostname, $opts, $channel);
    }

    /**
     * @param \LlmObservability\Platform\V1\LLMSpan $argument input argument
     * @param array $metadata metadata
     * @param array $options call options
     * @return \Grpc\UnaryCall
     */
    public function RecordSpan(\LlmObservability\Platform\V1\LLMSpan $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/llm.observability.v1.SpanIngestionService/RecordSpan',
        $argument,
        ['\LlmObservability\Platform\V1\RecordSpanResponse', 'decode'],
        $metadata, $options);
    }

}
