from typing import List, Dict, Any, Optional

from application.clients.base_client import BaseClient, ClientConfig


class SchemaRegistryClient(BaseClient):
    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.base_path = "/api/v1/schema-registry"
    
    def register_schema(self, subject: str, schema: str, 
                        schema_type: str = "AVRO") -> Dict[str, Any]:
        data = {
            "subject": subject,
            "schema": schema,
            "schema_type": schema_type
        }
        return self.post(f"{self.base_path}/schemas", data)
    
    def get_schema(self, schema_id: int) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/schemas/{schema_id}")
    
    def get_schema_by_subject(self, subject: str, 
                             version: Optional[int] = None) -> Dict[str, Any]:
        if version:
            return self.get(f"{self.base_path}/subjects/{subject}/versions/{version}")
        return self.get(f"{self.base_path}/subjects/{subject}/latest")
    
    def get_latest_schema(self, subject: str) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/subjects/{subject}/latest")
    
    def list_subjects(self) -> List[str]:
        result = self.get(f"{self.base_path}/subjects")
        return result.get("subjects", [])
    
    def list_versions(self, subject: str) -> List[int]:
        result = self.get(f"{self.base_path}/subjects/{subject}/versions")
        return result.get("versions", [])
    
    def delete_subject(self, subject: str) -> Dict[str, bool]:
        return self.delete(f"{self.base_path}/subjects/{subject}")
    
    def check_compatibility(self, subject: str, schema: str, 
                           schema_type: str = "AVRO") -> Dict[str, bool]:
        data = {
            "subject": subject,
            "schema": schema,
            "schema_type": schema_type
        }
        return self.post(f"{self.base_path}/compatibility", data)
    
    def update_compatibility(self, subject: str, 
                            compatibility: str) -> Dict[str, bool]:
        data = {
            "subject": subject,
            "compatibility": compatibility
        }
        return self.put(f"{self.base_path}/subjects/{subject}/compatibility", data)
    
    def serialize(self, subject: str, data: Dict, 
                  schema_id: Optional[int] = None) -> Dict[str, Any]:
        payload = {
            "subject": subject,
            "data": data
        }
        if schema_id:
            payload["schema_id"] = schema_id
        return self.post(f"{self.base_path}/serialize", payload)
    
    def deserialize(self, data: str, schema_id: int) -> Dict[str, Any]:
        payload = {
            "data": data,
            "schema_id": schema_id
        }
        return self.post(f"{self.base_path}/deserialize", payload)
