"""Vector point data model."""
from typing import Dict, Any, List, Union
from dataclasses import dataclass, field

@dataclass
class VectorPoint:
    """Represents a vector point with metadata."""
    id: Union[str, int]
    vector: List[float]
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate vector point after initialization."""
        if not isinstance(self.id, (str, int)):
            raise ValueError("ID must be string or integer")
        if not isinstance(self.vector, list) or not all(isinstance(x, (int, float)) for x in self.vector):
            raise ValueError("Vector must be list of numbers")
        if not isinstance(self.payload, dict):
            raise ValueError("Payload must be dictionary")
