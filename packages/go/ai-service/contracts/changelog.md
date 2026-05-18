# Changelog

All notable changes to the AI Service contract will be documented in this file.

## [1.0.0] - 2026-05-18

### Added
- Created the initial v1 OpenAPI REST API contracts.
- Added `GET /api/v1/models` for listing available models.
- Added `POST /api/v1/chat` for standard non-persistent AI inference.
- Added `POST /api/v1/chat/persistent` for persistent, in-memory chat session (15-min TTL) utilizing cosine similarity embeddings for semantic memory.
