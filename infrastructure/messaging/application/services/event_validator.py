from dataclasses import dataclass
from application.api.v1.validators import Preconditions, ValidationError
from application.api.v1.error_handler import raise_validation_error


@dataclass
class EventRequestParams:
    topic: str
    partition: int
    offset: int


@dataclass
class QueryParams:
    topic: str
    limit: int
    offset: int


@dataclass
class ConsumerOffsetParams:
    consumer_group: str
    topic: str
    partition: int
    offset: int


class EventValidator:
    def validate_event_request(self, params: EventRequestParams) -> None:
        try:
            Preconditions.validate_non_empty_string(params.topic, "topic")
            Preconditions.validate_non_negative(params.partition, "partition")
            Preconditions.validate_non_negative(params.offset, "offset")
        except ValidationError as e:
            raise_validation_error(str(e))

    def validate_batch_request(self, events: list) -> None:
        try:
            Preconditions.validate_list_size(events, "events", min_size=1, max_size=1000)
            for event in events:
                params = EventRequestParams(event.topic, event.partition, event.offset)
                self.validate_event_request(params)
        except ValidationError as e:
            raise_validation_error(str(e))

    def validate_event_id(self, event_id: str) -> None:
        try:
            Preconditions.validate_non_empty_string(event_id, "event_id")
        except ValidationError as e:
            raise_validation_error(str(e))

    def validate_query_params(self, params: QueryParams) -> None:
        try:
            Preconditions.validate_non_empty_string(params.topic, "topic")
            Preconditions.validate_range(params.limit, "limit", min_val=1, max_val=1000)
            Preconditions.validate_non_negative(params.offset, "offset")
        except ValidationError as e:
            raise_validation_error(str(e))

    def validate_limit(self, limit: int) -> None:
        try:
            Preconditions.validate_range(limit, "limit", min_val=1, max_val=1000)
        except ValidationError as e:
            raise_validation_error(str(e))

    def validate_consumer_offset(self, params: ConsumerOffsetParams) -> None:
        try:
            Preconditions.validate_non_empty_string(params.consumer_group, "consumer_group")
            Preconditions.validate_non_empty_string(params.topic, "topic")
            Preconditions.validate_non_negative(params.partition, "partition")
            Preconditions.validate_non_negative(params.offset, "offset")
        except ValidationError as e:
            raise_validation_error(str(e))
