# AI Library Assistant 📚

A smart, interactive educational resource navigator and study assistant built for Computer Science students as a college mini-project.

The application combines a local SQLite library catalogue containing verified computer science textbooks, documentation, and guides with a **100% free, local AI chatbot powered by Ollama (`llama3.2:3b`)**. The local model is grounded in library data to recommend learning resources and generate custom study plans without any paid API keys or external cloud dependencies.

---

## 🌟 Key Features

1. **Local AI Study Assistant (Ollama `llama3.2:3b`)**:
   - Runs **100% locally and free** on your computer (optimized for laptops with 16 GB RAM).
   - Understands learning goals and skill levels (Beginner, Intermediate, Advanced).
   - Recommends verified resources directly from the local library catalogue.
   - Explains *why* each resource is recommended and suggests a logical learning sequence.
   - Generates structured day-by-day study plans (e.g., 7-day or 30-day plans).
   - Preserves conversation context for follow-up questions.
   - Does not invent fake books or unverified links.

2. **Library Catalogue Explorer**:
   - Fast, parameterized keyword search across titles, authors, and descriptions.
   - Subject filtering (Python, Java, DSA, DBMS, OS, Networks, AI, Web Development).
   - Skill-level filtering (Beginner, Intermediate, Advanced).
   - Displays resource cards with tags and direct verified links where available.
   - Works completely offline alongside the local Ollama LLM.

3. **Safe & Resilient Backend**:
   - Built with Python and Flask.
   - Parameterized SQLite queries to prevent SQL injection.
   - Duplicate-safe database seeding on application startup.
   - Comprehensive request validation and graceful error handling if Ollama is not running or the model is missing.
   - No API keys or external billing required.

4. **Clean, Responsive UI**:
   - Plain HTML5, CSS3, and JavaScript (no heavy frontend frameworks required).
   - Real-time system health indicator showing Ollama connectivity and model status.
   - Suggested query quick-chips for instant asking.
   - Responsive split-panel layout on desktop and tabbed view on mobile.

---

## 🗂️ Project Directory Structure

```text
AI-Library-Assistant/
├── app.py                  # Flask backend server and API endpoints
├── assistant.py            # Local Ollama integration and catalogue grounding
├── requirements.txt        # Python package dependencies
├── .env                    # Environment variables (Ollama endpoint and model name)
├── .env.example            # Example configuration template
├── .gitignore              # Git ignore rules
├── README.md               # Project documentation
├── database/
│   ├── db.py               # SQLite database access, seeding, and search logic
│   ├── schema.sql          # SQL schema definition for resources table
│   └── resources.db        # SQLite database file (created automatically)
├── data/
│   └── resources.json      # Verified sample computer science resources
├── frontend/
│   ├── index.html          # Web application structure
│   ├── css/
│   │   └── style.css       # Responsive styling and themes
│   └── js/
│       └── script.js       # Client logic, chat handling, and catalogue filtering
└── tests/
    └── test_app.py         # Automated unit and integration tests
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (virtual environment in `.venv`)
- [Ollama](https://ollama.com/download) installed on your system

### 2. Setting Up Ollama and Downloading `llama3.2:3b`

1. **Install Ollama**:
   - Download the Windows installer from [ollama.com/download](https://ollama.com/download) and run it.

2. **Start Ollama & Pull the Model**:
   Open a terminal (PowerShell or Command Prompt) and run:
   ```powershell
   ollama run llama3.2:3b
   ```
   *This downloads the 3-billion-parameter Llama 3.2 model (~2.0 GB) and starts the local Ollama API server on `http://localhost:11434`.*
   *You can type `/bye` to exit the interactive terminal session; Ollama will stay running in the background as a system service.*

3. **Verify Ollama is Running**:
   In your browser or terminal, check:
   ```text
   http://localhost:11434
   ```
   It should display: `Ollama is running`.

### 3. Environment Configuration
Check your `.env` file in the project root:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

### 4. Running the Flask Application

In your VS Code terminal, run:

```powershell
.\.venv\Scripts\python.exe app.py
```

Then open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

Run the test suite using Python's `unittest` framework:

```powershell
.\.venv\Scripts\python.exe -m unittest tests/test_app.py
```

All Ollama HTTP responses are mocked during unit tests so they execute instantly without requiring Ollama to be active.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web frontend (`index.html`) |
| `GET` | `/api/health` | Health check reporting DB, Ollama status, and model availability |
| `GET` | `/api/subjects` | Retrieves all distinct CS subjects in catalogue |
| `GET` | `/api/resources` | Searches & filters resources (`q`, `subject`, `level`) |
| `POST` | `/api/chat` | AI conversation endpoint (`{"message": "...", "history": [...]}`) |

---

## 🛡️ Helpful Error Handling
- **If Ollama is not running**: The web UI shows an orange notice explaining how to start Ollama (`ollama serve`).
- **If the model is not found**: The web UI shows a notice explaining how to pull the model (`ollama run llama3.2:3b`).
- **Offline Library Search**: Even when Ollama is offline, students can still search, filter, and view all 24 verified library textbooks.
