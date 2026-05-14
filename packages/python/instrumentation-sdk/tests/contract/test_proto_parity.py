import unittest
import sys
import os

# Add relevant directories to sys.path
sys.path.append(os.path.abspath("packages/python/instrumentation-sdk/src"))
sys.path.append(os.path.abspath("packages/python/instrumentation-sdk/src/infra/clients/v1"))

import uuid
from datetime import datetime, timezone
from google.protobuf import json_format
from features.spans.types import LLMSpan, FinishReason, Environment, TokenCountMethod
import span_pb2

class TestProtoParity(unittest.TestCase):
    def test_pydantic_to_proto_conversion(self):
        """
        Verify that a Pydantic LLMSpan can be converted to a Proto LLMSpan and back,
        handling the enum normalization and UUID/DateTime strings correctly.
        """
        # 1. Create a rich Pydantic model
        span_id = uuid.uuid4()
        trace_id = uuid.uuid4()
        
        pydantic_span = LLMSpan(
            span_id=span_id,
            trace_id=trace_id,
            schema_version=1,
            model="gpt-4o",
            provider="openai",
            service_name="test-service",
            endpoint="/chat",
            environment=Environment.PRODUCTION,
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms_total=150,
            finish_reason=FinishReason.STOP,
            cost_usd_micro=1234,
            price_version="2024-05-13",
            token_count_method=TokenCountMethod.TIKTOKEN,
            is_sampled=True,
            timestamp_utc=datetime.now(timezone.utc),
            prompt_embedding=[0.1] * 384,
            response_embedding=[0.2] * 384
        )

        # 2. Convert Pydantic -> JSON -> Proto
        # We use mode="json" and ensure enums are handled as integers or strings
        # But for Proto, integers are the most robust wire format
        span_dict = pydantic_span.model_dump(mode="json")
        
        # We need to ensure the enums in the dict are integers for ParseDict
        # if we want absolute reliability, OR we map them to the Proto string names.
        # Let's map them to Proto strings to test our string mapping.
        span_dict["environment"] = "ENVIRONMENT_PRODUCTION"
        span_dict["finish_reason"] = "FINISH_REASON_STOP"
        span_dict["token_count_method"] = "TOKEN_COUNT_METHOD_TIKTOKEN"
        
        proto_span = span_pb2.LLMSpan()
        json_format.ParseDict(span_dict, proto_span)

        # 3. Verify Proto values
        self.assertEqual(proto_span.span_id, str(span_id))
        self.assertEqual(proto_span.model, "gpt-4o")
        # Verify enum was mapped correctly (integer 1 for PRODUCTION)
        self.assertEqual(proto_span.environment, span_pb2.ENVIRONMENT_PRODUCTION)
        self.assertEqual(proto_span.finish_reason, span_pb2.FINISH_REASON_STOP)

        # 4. Convert Proto -> JSON -> Pydantic
        # This tests our 'normalize_proto_enums' validator
        # preserving_proto_field_name=True ensures we get snake_case (span_id instead of spanId)
        proto_json = json_format.MessageToJson(
            proto_span, 
            use_integers_for_enums=False, 
            preserving_proto_field_name=True
        )
        
        # Verify the JSON contains the "FINISH_REASON_STOP" string (the hard case)
        self.assertIn("FINISH_REASON_STOP", proto_json)
        self.assertIn("span_id", proto_json) # Verify snake_case
        
        # This should succeed because of our normalize_proto_enums validator!
        pydantic_roundtrip = LLMSpan.model_validate_json(proto_json)
        
        self.assertEqual(pydantic_roundtrip.span_id, span_id)
        self.assertEqual(pydantic_roundtrip.finish_reason, FinishReason.STOP)
        self.assertEqual(pydantic_roundtrip.environment, Environment.PRODUCTION)

if __name__ == "__main__":
    unittest.main()
