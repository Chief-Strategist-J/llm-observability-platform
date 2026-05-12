# OpenAPI v1 Changelog

## v1.0.0 - Initial Release
**Date:** 2025-01-11

### Added
- Database Operations API
  - `POST /api/v1/database/events` - Store single event
  - `GET /api/v1/database/events` - Query events with filtering
  - `POST /api/v1/database/events/batch` - Store multiple events
  - `GET /api/v1/database/offsets` - Get consumer offsets
  - `POST /api/v1/database/offsets` - Update consumer offset

- Schema Registry API
  - `POST /api/v1/schema-registry/schemas` - Register new schema
  - `GET /api/v1/schema-registry/schemas` - List all subjects
  - `GET /api/v1/schema-registry/schemas/{subject}` - Get schema by subject
  - `POST /api/v1/schema-registry/compatibility` - Check schema compatibility
  - `PUT /api/v1/schema-registry/compatibility/{subject}` - Update compatibility level
  - `POST /api/v1/schema-registry/serialize` - Serialize data
  - `POST /api/v1/schema-registry/deserialize` - Deserialize data

- Event Handler API
  - `POST /api/v1/event-handler/process` - Process single event
  - `POST /api/v1/event-handler/process/batch` - Process multiple events

- Health Endpoints
  - `GET /health` - Health check
  - `GET /` - API information

### Features
- Bearer token authentication
- Rate limiting (100 requests/minute)
- CORS support
- OpenAPI 3.0.3 specification
- Comprehensive error responses
- Request/response validation
- Batch processing support

### Schema Types Supported
- AVRO
- JSON
- PROTOBUF

### Compatibility Levels
- BACKWARD
- FORWARD
- FULL
- NONE

### Breaking Changes
- None (initial release)

### Security
- All endpoints require Bearer token authentication except health endpoints
- Rate limiting applied to all endpoints
- Input validation on all requests

### Notes
- Maximum batch size: 1000 events
- Maximum query limit: 1000 events
- All timestamps use ISO 8601 format
- Serialized data is base64 encoded
