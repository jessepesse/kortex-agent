# Changelog

All notable changes to Kortex Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
