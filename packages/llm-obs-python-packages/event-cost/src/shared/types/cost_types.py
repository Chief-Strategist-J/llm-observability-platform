from dataclasses import dataclass


@dataclass(frozen=True)
class PriceEntry:
    model: str
    provider: str
    input_price_per_token_micro: int
    output_price_per_token_micro: int
    version: str


class ProcessingError(Exception):
    pass
