# Changelog

All notable changes to Kortex Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-alpha4] - 2025-12-08

### Fixed
- **start.sh Startup** — Backend now runs from project root with correct PYTHONPATH for fully qualified imports

---

## [1.0.0-alpha3] - 2025-12-08

### Added

#### Security Infrastructure
- **CodeQL Workflow** — Custom `.github/workflows/codeql.yml` with Python & JavaScript analysis
- **CodeQL Config** — `.github/codeql/codeql-config.yml` with query filters for false positives
- **Bandit Integration** — Local security scanning via `scripts/security_check.sh`
- **Security Policy** — `SECURITY.md` with vulnerability reporting guidelines

#### CI/CD Improvements
- **Dependabot** — Automated dependency updates for pip, npm, and GitHub Actions
- **Build Optimization** — Docker images now only built on version tags (saves CI minutes)

### Changed

#### Security Hardening
- **Path Traversal Protection** — `validate_filename()` and `build_safe_conv_path()` with strict character allowlists
- **Input Sanitization** — `validate_chat_id()` with explicit string reconstruction
- **Safe Logging** — `safe_str()` helper to prevent sensitive data in logs
- **Generic Error Messages** — Exception handlers now return static messages, not `str(e)`

#### Backend
- **Docker Structure** — Fixed `backend/Dockerfile` to preserve directory structure for imports
- **Workflow Permissions** — Added explicit permissions blocks to CI jobs

### Fixed
- **Docker Startup Crash** — Backend container failing due to flattened directory structure
- **Import Errors** — Standardized to fully qualified imports (`from backend.errors import ...`)

---

## [1.0.0-alpha2] - 2025-12-08

### Added

#### Testing & Quality
- **Comprehensive Test Suite** — 39 tests (unit + integration)
- **pytest Configuration** — `pytest.ini` with proper settings
- **Shared Test Fixtures** — `conftest.py` with isolated temp directories
- **Type Hints** — Full type annotations in `kortex/` modules

#### Infrastructure
- **Docker Health Check** — Backend health endpoint with container health monitoring
- **Dependency Pinning** — All Python dependencies pinned to exact versions

#### Logging
- **Centralized Logging** — `kortex/logging.py` with colored console output
- **Emoji Prefixes** — Visual log level indicators (✨ INFO, ⚠️ WARNING, ❌ ERROR)

### Changed

#### Backend Architecture
- **Modular Routes** — Refactored `routes.py` (800+ lines) into 7 focused modules:
  - `routes/health.py`, `chat.py`, `history.py`, `data.py`, `config.py`, `backup.py`, `council.py`
- **Centralized Errors** — `errors.py` with custom exceptions and decorators
- **Standardized Responses** — `success_response()` and `error_response()` helpers

#### Frontend Architecture  
- **SettingsModal Refactored** — Split into 5 focused components (462 → ~100 lines each)
- **Chat Tracking** — Council modes now properly return and track `chat_id`

#### AI Behavior
- **Improved System Prompt** — AI now actually answers questions instead of deflecting
- **All-Domain Helpfulness** — Covers tech, health, projects, emotions, finances
- **Anti-Pattern Rules** — Explicit rules against "kerro lisää", "miten voin auttaa?"

### Fixed

- **Council Chat Duplicates** — Fixed missing `chat_id` in council route responses
- **Conversation Tracking** — Frontend now properly tracks council conversation IDs
- **Deprecated datetime** — Fixed `datetime.utcnow()` deprecation warning

---

## [1.0.0-alpha] - 2025-12-05

### Added

#### Core Features
- **Multi-Provider AI Support** — Google Gemini, OpenAI, Anthropic
- **11 AI Models** — Including Gemini 2.5/3, GPT-5 series, Claude Haiku series
- **Multimodal Input** — Images, videos, audio, PDFs

#### Council LLM Modes
- **Elite Mode** — 3 raw LLMs collaborate without personas
- **Hive Mode** — 6 DeepSeek personas with specialized roles
- **MEGA Mode** — Elite + Hive battle with voting system

#### Data Management
- **Scribe** — Background agent auto-updates data from conversations
- **Function Calling** — Native tool use for data operations
- **Auto-Initialization** — Data files created automatically on first run

#### User Experience
- **React Frontend** — Modern chat interface with file previews
- **Live Context Sidebar** — Energy, location, focus display
- **Settings Modal** — Configure models, API keys, edit data
- **Backup & Restore** — Export/import all data as ZIP

#### Infrastructure
- **Docker Support** — docker-compose for easy deployment
- **start.sh** — One-command startup script

### Documentation
- README.md with full feature documentation
- QUICKSTART.md for quick setup
- AGENTS.md for AI coding assistants
- Example data files in `data.example/`

---

## Future Releases

### Planned for 1.1.0
- Streaming responses
- Token usage tracking
- Cost estimation per provider
- Mobile-optimized UI
