# 🧠 KORTEX >_ Personal AI Assistant

> **Version 1.0.0-alpha2** | Powered by Council LLM Architecture

**Kortex Agent** is a comprehensive, context-aware AI assistant designed to act as your personal operating system. It integrates deeply with your life's data—values, health, projects, routines—to provide pragmatic, personalized advice.

Built with a modern **React frontend** and a robust **Flask backend**, Kortex supports **multiple AI providers** (Google Gemini, OpenAI, Anthropic) and **multimodal interactions** (text, images, audio, video, PDF).

## ✨ Key Features

### 🤖 Multi-Provider & Multimodal AI
- **Providers:** Seamlessly switch between **Google Gemini**, **OpenAI**, and **Anthropic**.
- **Models:** 11 models across 3 providers:
  - **Google:** `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`, `gemini-3-pro-preview`
  - **OpenAI:** `gpt-5-mini`, `gpt-5-nano`, `gpt-5`, `gpt-5.1`
  - **Anthropic:** `claude-haiku-4-5`, `claude-haiku-3-5`, `claude-haiku-3`
- **Multimodal:** Upload **images, videos, audio files, and PDFs**. The AI can analyze and discuss them with you.
- **Auto-Validation:** The UI automatically adapts file upload options based on the selected model's capabilities.

### 🏛️ Elite Mode — *Powered by Council LLM*
- **Raw LLM Power:** 3 top-tier models (Gemini 3 Pro, GPT-5.1, Claude Haiku 4.5) give their unbiased perspective **without personas**.
- **Peer Review:** Each model anonymously reviews the others' responses.
- **Chairman Synthesis:** A designated model moderates and synthesizes the final decision.

### 🐝 Hive Mode
- **6 Specialized Personas:** DeepSeek models with distinct roles:
  - ⚔️ **Devil's Advocate** — Challenges every assumption
  - 📊 **Pure Data** — Facts and numbers only
  - 💚 **Health Guardian** — Prioritizes wellbeing
  - ⚖️ **Values Keeper** — Ensures alignment with core values
  - 🔧 **Pragmatic Executor** — Focuses on practical execution
  - 💰 **Financial Realist** — Evaluates financial implications
- **Anonymous Peer Review:** Personas critique each other before synthesis.

### 🌟 MEGA Mode
- **Ultimate Synthesis:** Elite + Hive run in parallel, then battle for the best answer.
- **Voting System:** Elite models vote on their best response, Hive personas vote on theirs.
- **Mega Chairman:** An ultimate chairman synthesizes both winners into the final verdict.

### ✍️ Scribe — Autonomous Data Management
- **Passive Tracking:** "Scribe" is a background AI agent that analyzes every conversation.
- **Auto-Updates:** It autonomously updates your JSON data files (e.g., `health.json`, `active_projects.json`) based on what you discuss.
- **Zero-Friction:** You don't need to ask the AI to update data; it just happens. "I went for a run" → Scribe updates your last workout and energy levels.

### 💾 Backup & Restore
- **Full Data Export:** Download all your data as a ZIP file.
- **Selective Backup:** Choose which conversations to include.
- **Easy Restore:** Upload a backup to restore your data.
- **Validation:** Backups are validated before restore to prevent data corruption.

### ⚡ Live Context Sidebar
- **Real-Time Dashboard:** Always-visible sidebar showing your current **Energy**, **Location**, and **Focus**.
- **Dynamic Updates:** Updates automatically as Scribe modifies your data.
- **Chat History:** Persistent chat history with **AI-generated titles** for easy navigation.

### 🛠️ Native Function Calling
- **Tool Use:** The AI has direct access to tools for reading and writing your data files.
- **Transparency:** You see exactly what the AI wants to change and must approve significant updates (unless Scribe handles them).

## 🏗️ Architecture

Kortex Agent is built as a full-stack web application:

- **Frontend:** React, Vite, CSS. Features a modern, responsive chat interface with file previews, settings modal, and markdown rendering.
- **Backend:** Python Flask. Handles API routing, AI model integration, and file system operations.
- **Data Layer:** Local JSON files. Your data stays on your machine. No external database required.

## 📁 Project Structure

```
kortex-agent/
├── backend/                 # Flask API server
│   ├── app.py               # App entry point
│   └── routes.py            # API endpoints
├── frontend/                # React application
│   ├── src/
│   │   ├── components/      # Chat, Sidebar, Settings, Council/Hive/MegaView
│   │   └── services/        # API client
├── kortex/                  # Core logic package
│   ├── ai/                  # AI handlers (Council, Hive, Mega, Scribe, Providers)
│   ├── data.py              # Data management with auto-initialization
│   └── backup.py            # Backup & restore functionality
├── data/                    # YOUR personal data (created automatically)
│   ├── profile.json         # Identity & live context
│   ├── health.json          # Metrics & goals
│   ├── values.json          # Core principles
│   ├── finance.json         # Budgeting
│   ├── conversations/       # Saved chat history
│   └── ...                  # Extensible: add any .json file!
├── data.example/            # Example data structure (for reference)
├── config.json              # API keys and model preferences
├── start.sh                 # Quick start script (Linux/macOS)
└── start.bat                # Quick start script (Windows)
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+ & npm

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/jessepesse/kortex-agent.git
cd kortex-agent

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configuration

Create a `.env` file (or copy from `.env.example`):

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
```

You can also configure API keys through the Settings modal in the UI.

### 3. Running Kortex Agent

Use the helper script to start both backend and frontend:

**Linux/macOS:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

The app will open at `http://localhost:3000`.

**Note:** On first run, Kortex automatically creates the `data/` folder with default empty data files.

### Docker (Alternative)

```bash
docker-compose up --build
```

## 💬 Usage Guide

### Basic Chat
Type your message. Upload files using the 📎 button. The AI has read-access to all your `data/*.json` files and uses them as context.

### Changing Models
Click the **Settings (⚙️)** icon in the sidebar footer.
- Select your preferred **Chat Model** (e.g., `gemini-2.5-flash` for speed, `gpt-5` for reasoning).
- Configure the **Council Chairman**.
- View and edit your raw JSON data directly.

### Using Council Mode
1. Click the **Council** button in the chat header.
2. Ask a complex question (e.g., "Should I quit my job to start a startup?").
3. Watch as the Council members debate and provide a unified answer.

### Backup & Restore
1. Open **Settings (⚙️)** → **Backup** tab.
2. Select which conversations to include.
3. Click **Download Backup** to save a ZIP file.
4. To restore, upload a backup ZIP and confirm.

### Managing Data
- **Manual:** Edit JSON files in `data/` or use the Editor in Settings.
- **Natural Language:** Tell the AI "Add 'Buy milk' to my tasks".
- **Scribe:** Just chat naturally. Scribe will catch details like "I'm feeling tired" and update your energy stats.

## 🙏 Inspiration

The multi-LLM council concept was inspired by [Andrej Karpathy's llm-council](https://github.com/karpathy/llm-council).

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
