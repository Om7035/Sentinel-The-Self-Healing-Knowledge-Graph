# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6] - 2025-11-30

### Fixed
- **CLI Crash**: Upgraded `typer` to `^0.20.0` to resolve `TypeError: Parameter.make_metavar()` crash caused by incompatibility with `click` 8.x.

## [0.1.5] - 2025-11-30

### Fixed
- **Dependency Ambiguity**: Removed `neo4j` from `extras` to ensure it is always installed as a core dependency.

## [0.1.4] - 2025-11-30

### Fixed
- **Neo4j Dependency**: Moved `neo4j` from optional to required dependencies to prevent `ModuleNotFoundError` on startup.

## [0.1.3] - 2025-11-30

### Fixed
- **Missing Dependencies**: Added `langchain-community` and `langchain-core` to `pyproject.toml` to fix `ModuleNotFoundError`.

## [0.1.2] - 2025-11-30

### Fixed
- **CLI Compatibility**: Updated `typer` dependency to support newer `click` versions.

## [0.1.1] - 2025-11-30

### Fixed
- **Installation**: Fixed permission issues and path warnings during user installation.

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
