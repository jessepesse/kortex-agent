# Changelog

All notable changes to Kortex Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-alpha7] - 2026-03-04

### Changed
#### Model Updates
- **Google:** Replaced `gemini-2.5-flash` with `gemini-3-flash-preview` across the system core and frontend UI.
- **Google:** Replaced `gemini-2.5-flash-lite` with `gemini-3.1-flash-lite-preview` for Scout intelligence, titles, and background data management.

### Fixed
- **pypdf** 6.7.4 → 6.7.5 — Fixes ASCIIHexDecode streams RAM exhaustion vulnerability (Dependabot issue #47)

---

## [1.0.0-alpha6-hotfix2] - 2026-02-28

### Fixed
- **setup.py** — Updated dependency constraints (`flask>=3.1.3`, `flask-cors>=6.0.2`, `google-genai>=1.0.0`, `openai>=2.21.0`) to resolve 6 Flask/Flask-CORS security advisories relating to CORS handling, regex, log injection, and session vary headers.

---

## [1.0.0-alpha6-hotfix] - 2026-02-28

### Fixed
- **pypdf** 6.7.3 → 6.7.4 — Fixes RunLengthDecode RAM exhaustion vulnerability ([CVE](https://github.com/py-pdf/pypdf/security/advisories/GHSA-41))
- **handler.py** — Fixed `__import__('base64')` anti-pattern in Gemini multimodal handler

---

## [1.0.0-alpha6] - 2026-02-28

### Changed

#### SDK Migration
- **Google GenAI SDK** — Migrated from deprecated `google-generativeai` to new `google-genai` SDK
  - New `Client()` + `client.models.generate_content()` pattern
  - Uses `system_instruction` config instead of prompt prepending
  - Removed `convert_to_dict()` helpers (new SDK uses native dicts)
  - **Breaking:** API key env var is now `GEMINI_API_KEY` (was `GOOGLE_API_KEY`)

#### Model Updates
- **Google:** `gemini-2.5-pro` → `gemini-3.1-pro-preview`
- **Anthropic:** Added `claude-opus-4.6` and `claude-sonnet-4.6`
- **Anthropic:** Removed `claude-haiku-3.5`, `claude-haiku-3`, `claude-3-5-sonnet-20241022`

#### Dependencies Updated
- **Python:**
  - `openai` 2.11.0 → 2.21.0
  - `google-generativeai` 0.8.6 → `google-genai` ≥1.0.0
  - `bandit` 1.9.2 → 1.9.3
  - `aiohttp` 3.13.2 → 3.13.3
  - `pypdf` 6.4.2 → 6.7.3
  - `Flask` 3.1.2 → 3.1.3
- **Transitive deps pinned:** `werkzeug` ≥3.1.6, `protobuf` ≥5.29.6, `pyasn1` ≥0.6.2, `urllib3` ≥2.6.3
- **Frontend:** `axios` ^1.13.5, `react-dom` ^19.2.4, `vite` ^7.3.1, `globals` ^17.3.0, `eslint-plugin-react-refresh` ^0.5.0
- **GitHub Actions:** `actions/checkout` v4 → v6, `github/codeql-action` v3 → v4

### Fixed
- **28 Dependabot Security Alerts** — All resolved via direct and transitive dependency updates

---

## [1.0.0-alpha5-hotfix] - 2025-12-20

### Changed
- **Dependencies Updated**:
  - `openai` 2.9.0 → 2.11.0 (official GPT-5.2 support)
  - `pypdf` 6.4.0 → 6.4.2
  - `bandit` 1.8.0 → 1.9.2
  - `flask-cors` 6.0.1 → 6.0.2
  - `react-dom` 19.2.1 → 19.2.3 (Server Functions security patches)
  - `eslint` 9.39.1 → 9.39.2
  - `@eslint/js` 9.39.1 → 9.39.2
  - `eslint-plugin-react-refresh` 0.4.24 → 0.4.25
- **README Updated** — Providers, models, Web Search, and Thinking toggle now documented

### Added
- **Universal PDF Support** — All models now support PDF files via OpenRouter's built-in PDF processing plugin (previously only Gemini)

## [1.0.0-alpha5] - 2025-12-20

### Added

#### Web Search with Scout Intelligence
- **Web Search Pipeline** — New 3-stage architecture for intelligent web searches:
  1. **Scout** (Gemini 2.5 Flash-Lite) — Analyzes query, decides if search needed
  2. **Specialist** (Grok or Perplexity) — Performs the actual web search
  3. **Synthesizer** (User's model) — Generates final response using search data
- **Scout Decisions**:
  - `NO_SEARCH` (0-60%) — No web data needed, respond directly
  - `SUGGEST_SEARCH` (61-99%) — Show card, user chooses search model
  - `FORCE_SEARCH` (100%) — Auto-search for live data (prices, weather, scores)
- **Two Search Specialists**:
  - **Grok 4.1-fast** (NEWS) — Native X/Twitter + web search, fast and cheap
  - **Perplexity Sonar Pro** (RESEARCH) — Deep research with reasoning and authoritative sources
- **Scout Card UI** — Interactive card for `SUGGEST_SEARCH` decisions
  - Shows recommendation with confidence %
  - User can choose: Grok, Perplexity, or Skip
- **Scout Debug Badge** — Shows recommendation vs used model for FORCE searches
- **Quiet Mode** — `NO_SEARCH` and `FORCE_SEARCH` operate silently
- **Budget Protection** — FORCE always uses cheaper Grok regardless of recommendation
- **Manual Toggle** — 🌐 button enables web search, Scout analyzes before sending
- **Source Citations** — Search results include URLs in standardized format

#### New AI Models & Providers
- **X-AI Provider** — New provider with Grok models:
  - **Grok 4** — Full model with native X/web search
  - **Grok 4.1-fast** — Fast variant for quick searches
- **DeepSeek Provider** — New provider:
  - **DeepSeek v3.2 Speciale** — DeepSeek's latest model
- **Claude Opus 4.5** — Added to Anthropic models with thinking support
- **GPT-5.2** — Added to OpenAI models
- **Gemini 3 Flash Preview** — Added to Google models

#### Thinking/Reasoning Toggle
- **Thinking Toggle Button** (🧠) — New UI button to enable extended reasoning
- **Reasoning via OpenRouter** — Uses `extra_body={"reasoning": {"enabled": True}}`
- **30+ Models Supported** — Thinking available for:
  - Google: Gemini 3/2.5 Pro/Flash
  - OpenAI: GPT-5, 5.1, 5.2
  - Anthropic: Claude Opus 4.5, Haiku 4.5
  - X-AI: Grok 4, Grok 4.1-fast
  - DeepSeek: v3.2 Speciale

### Changed

#### Full OpenRouter Migration
- **All Providers via OpenRouter** — Gemini, OpenAI, Anthropic, X-AI, DeepSeek all route through OpenRouter API
- **Unified API Pattern** — Single `AsyncOpenAI` client with `base_url="https://openrouter.ai/api/v1"`
- **Fallback Support** — Direct provider APIs used only when OpenRouter key missing
- **Council.py Rewrite** — All 3 members, peer reviews, and chairman now via OpenRouter
- **Mega.py Rewrite** — Elite voting, refinement, mega chairman all via OpenRouter
- **Hive.py Update** — Chairman synthesis now via OpenRouter
- **Scribe.py Rewrite** — Background analyzer with OpenAI-style function calling via OpenRouter

#### Council Updates
- **Council Chairman upgraded** — GPT-5 → GPT-5.2 for better synthesis
- **GPT-5.2 as chairman option** — Available in settings dropdown

---

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
