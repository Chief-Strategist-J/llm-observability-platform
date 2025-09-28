"""Vector point data model."""
from typing import Dict, Any, List, Union
from dataclasses import dataclass

@dataclass
class VectorPoint:
    id: Union[str, int]
    vector: List[float]
    payload: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.payload is None:
            self.payload = {}
