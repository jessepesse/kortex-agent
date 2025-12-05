# Kortex Agent - Quick Start Guide

## 🚀 Starting the Application

### Option 1: One Command (Recommended)

```bash
./start.sh
```

This starts both backend and frontend. Press `Ctrl+C` to stop both.

### Option 2: Docker Compose

```bash
docker-compose up --build
```

Builds and runs both services in containers.

### Option 3: Manual Start (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
python3 app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

## 📍 Access Points

| Service | URL |
|---------|-----|
| **Frontend (UI)** | http://localhost:3000 |
| **Backend (API)** | http://localhost:5001 |
| **Health Check** | http://localhost:5001/health |

---

## 🔑 Configuration

### API Keys

Configure via the **Settings modal** in the UI, or create a `.env` file:

```bash
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key  # Required for Hive Mode
```

---

## 📝 First Time Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install frontend dependencies:**
   ```bash
   cd frontend && npm install && cd ..
   ```

3. **Configure API keys** (via UI Settings or `.env`)

4. **Start the app:**
   ```bash
   ./start.sh
   ```

5. **Open** http://localhost:3000

---

## 🛑 Stopping

| Method | Command |
|--------|---------|
| start.sh | `Ctrl+C` |
| Docker | `docker-compose down` |
| Manual | `Ctrl+C` in each terminal |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5001 in use | Check with `lsof -i :5001` |
| Frontend won't start | Run `npm install` in `frontend/` |
| Backend errors | Check Python 3.8+ and `pip install -r requirements.txt` |
| Missing API keys | Configure in Settings modal or `.env` |

---

## 📚 More Information

See [README.md](README.md) for full documentation.
