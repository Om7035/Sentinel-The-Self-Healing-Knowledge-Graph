# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-30

### Added
- **Core Library**: `sentinel_core` package with GraphManager, GraphExtractor, and Sentinel orchestrator.
- **CLI Tool**: `sentinel_cli.py` standalone script for easy management.
  - `init`: Interactive setup wizard.
  - `watch`: Process URLs and extract knowledge.
  - `heal`: Autonomous self-healing cycles.
  - `status`: System health monitoring.
- **Temporal Graph**: Neo4j implementation with `valid_from` and `valid_to` tracking.
- **Scraper Engine**: Hybrid system supporting Firecrawl (API) and Local (BeautifulSoup) scraping.
- **LLM Integration**: Support for Ollama (local) and OpenAI models via LiteLLM.
- **API Server**: FastAPI backend with endpoints for ingestion and status.
- **Web UI**: Next.js frontend with 3D force-directed graph visualization.

### Fixed
- Resolved circular import issues in CLI by implementing lazy loading.
- Fixed `instructor` library compatibility issues by pinning version `^1.13.0`.
- Fixed Windows encoding issues in CLI output.

### Security
- Implemented `.env` file handling for secure API key storage.
- Added connection verification for database and LLM services.
