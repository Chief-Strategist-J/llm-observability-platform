from enum import Enum


class SchemaType(str, Enum):
    """Supported schema types"""
    AVRO = "AVRO"
    PROTOBUF = "PROTOBUF"
    JSON = "JSON"


class SchemaInfo:
    """Domain entity representing schema information"""
    
    def __init__(
        self,
        subject: str,
        schema_id: int,
        schema_type: SchemaType,
        schema: str,
        version: int,
        compatibility: Optional[str] = None
    ):
        self.subject = subject
        self.schema_id = schema_id
        self.schema_type = schema_type
        self.schema = schema
        self.version = version
        self.compatibility = compatibility
