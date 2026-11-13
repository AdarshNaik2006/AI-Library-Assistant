# Universal AI Library Assistant 📚

A comprehensive, multi-tier educational resource navigator and intelligent study assistant for students of **all ages, classes, departments, and educational levels (1st Standard to University & Postgraduate)**, with full support for both **Kannada (ಕನ್ನಡ)** and **English**.

The application combines a verified SQLite library catalogue of **65+ authentic school and university textbooks** with a **100% free, local AI chatbot powered by Ollama (`llama3.2:3b`)**. The local AI model is grounded in verified curriculum resources to recommend textbooks, explain academic concepts, build structured study plans, and guide learning journeys without any paid API keys, external billing, or cloud data tracking.

---

## 🌟 Key Features

### 1. Universal Educational Coverage (1st Standard to Postgraduate)
- **Primary School (1st to 5th Standard)**: Foundational readers, arithmetic, and environmental studies (DSERT Karnataka & NCERT *Marigold English*, *Math-Magic*, *Siri Kannada*, *Ganitha Prakash*).
- **Middle School (6th to 8th Standard)**: Core science, mathematics, social studies, and Kannada (*Science Class VIII*, *Mathematics Class VIII*, *Tili Kannada*, *Resources & Development*).
- **High School (9th & 10th Standard / SSLC)**: Board syllabus textbooks and exam preparation (*Mathematics Class X*, *Science Class X*, *First Flight English*, *Siri Kannada 10th*, *R.S. Aggarwal Class 10 Math*).
- **PUC / Higher Secondary (1st & 2nd PUC / 11th & 12th)**: Karnataka Pre-University & NCERT board editions (*Physics Parts I & II*, *Chemistry Parts I & II*, *Mathematics Parts I & II*, *Biology Class XII*, *Accountancy*, *Micro/Macroeconomics*, *Concepts of Physics* by Dr. H.C. Verma).
- **Diploma / Polytechnic**: Applied science and engineering fundamentals (*Applied Science for Diploma* by Theraja, *Basic Mechanical Engineering* by Rajput, *Basic Civil Engineering* by Bhavikatti, *Basic Electrical Engineering* by Bhattacharya, *Applied Mathematics for Polytechnics* by Dass).
- **Undergraduate (BA, BSc, BCom, BCA, BBA, BE, BTech)**: Standard university textbooks (*Higher Engineering Mathematics M1/M2* by Dr. B.S. Grewal, *Advanced Engineering Mathematics M2* by Erwin Kreyszig, *Machine Design* by Khurmi, *Thermodynamics* by Cengel, *Double Entry Book Keeping* by T.S. Grewal, *Computer Science* core by Silberschatz, Cormen, Matthes, Ramalho).
- **Postgraduate (MA, MSc, MCom, MCA, MBA, MTech)**: Rigorous advanced references (*Principles of Mathematical Analysis* by Walter Rudin, *Corporate Finance* by Aswath Damodaran, *Marketing Management* by Philip Kotler, *Deep Learning* by Goodfellow et al., *Fluent Python* by Ramalho).

### 2. Dual-Language Intelligence (Kannada & English)
- **Automatic Language Detection**: Instantly detects Kannada Unicode script (`[\u0C80-\u0CFF]`) or English queries.
- **Native-Language Responses**: When asked in Kannada, the assistant responds completely in natural, fluent Kannada (*ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ*).
- **Age-Adapted Explanations**:
  - *Primary School*: Simple, friendly language with short sentences and encouraging examples.
  - *Middle & High School*: Clear definitions, step-by-step points, and exam tips.
  - *PUC*: Formulas, derivations, diagrams, and board/competitive exam focus.
  - *Diploma*: Practical technical steps, industry application, and applied formulas.
  - *University & PG*: Academic depth, mathematical foundations, and research-level citations.

### 3. Complete Resource-Opening & Book Details Modal
- **Clickable Book Cards**: Every book card in the catalogue is interactive with hover elevation and keyboard accessibility.
- **Dual Action Opening**:
  - **Books with Verified External URLs**: Clickable **"View Resource"** button that opens legitimate official publisher or educational portals in a new tab (`target="_blank" rel="noopener noreferrer"`), plus a **"Details"** button.
  - **Books in Physical Campus Collection**: Clickable **"View Book Details"** button replacing static labels so every single book can be viewed and inspected.
- **Comprehensive Book Details Modal**: Displays complete metadata:
  - Book Title & Author
  - Verified Publisher (e.g., *O'Reilly Media*, *Pearson*, *NCERT*, *DSERT Karnataka*, *MIT Press*, *McGraw-Hill*, *John Wiley & Sons*, *Bharati Bhawan*)
  - Subject & Department
  - Educational Level & Class / Grade
  - Difficulty Level & Language
  - Full Book Description
  - Official Resource Link (with safe external opening) or Physical Library Section status.

### 4. Strict Educational Domain Protection
- Politely rejects off-topic queries (cooking, biryani, cricket scores, entertainment, jokes, politics) in both English and Kannada.
- **Catalogue Honesty**: When an academic question is asked on a topic without a physical textbook in the catalogue, the assistant clearly notes: *"No matching books are currently available in our catalogue."*, while still providing general conceptual guidance.

### 5. 100% Free, Local AI (No Paid APIs)
- Powered by local **Ollama (`llama3.2:3b`)** running on `http://localhost:11434`.
- **Zero API subscriptions, zero token fees, zero external telemetry**.

---

## 🗂️ Project Directory Structure

```text
AI-Library-Assistant/
├── app.py                  # Flask backend server, API routes, and CORS handling
├── assistant.py            # Local Ollama integration, relevance scoring, and prompts
├── requirements.txt        # Python package dependencies (Flask, python-dotenv, gunicorn)
├── Procfile                # WSGI production server command for cloud hosting
├── .env                    # Local environment variables
├── .env.example            # Configuration template
├── .gitignore              # Git ignore rules
├── README.md               # Complete project documentation
├── database/
│   ├── db.py               # SQLite access, migrations, seeding, and search
│   ├── schema.sql          # SQL schema definition for resources table
│   └── resources.db        # SQLite database (created automatically)
├── data/
│   └── resources.json      # 65+ verified school and university curriculum textbooks
├── frontend/
│   ├── index.html          # Responsive single-page interface with Book Details modal
│   ├── css/
│   │   └── style.css       # Clean responsive styles, modal animations, and themes
│   └── js/
│       └── script.js       # Client logic, chat, catalogue search, and modal handling
└── tests/
    └── test_app.py         # Automated test suite (31 comprehensive unit/integration tests)
```

---

## 🚀 Getting Started (Local Development)

### 1. Prerequisites
- Python 3.10 or higher.
- [Ollama](https://ollama.com/download) installed on your system.

### 2. Download and Run the Local Model
Open your terminal (PowerShell or Bash) and run:
```powershell
ollama run llama3.2:3b
```
*This downloads the 3-billion-parameter Llama 3.2 model (~2.0 GB) and starts the local Ollama API server on `http://localhost:11434`.*
*Type `/bye` to exit the terminal session; the background server remains running.*

Verify Ollama is active by visiting `http://localhost:11434` in your browser (it should display: `Ollama is running`).

### 3. Setup Virtual Environment
```powershell
# Navigate to the project root
cd C:\Users\naik7\OneDrive\Documents\AI-Library-Assistant

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` (already pre-configured for local development):
```env
HOST=127.0.0.1
PORT=5000
FLASK_DEBUG=1
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

### 5. Start the Application
```powershell
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

Run the full automated test suite using Python's `unittest` framework:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### Test Coverage (31 Tests Passing):
1. **Scenario 1**: 3rd Standard English recommendations (*Marigold Class 3 English*; 0 unrelated books).
2. **Scenario 2**: 5th Standard Kannada mathematics recommendations (*Ganitha Prakash Class 5* / *Math-Magic*; native Kannada query support).
3. **Scenario 3**: 8th Standard Science explanations (*Science Class VIII*).
4. **Scenario 4**: 10th Standard Mathematics recommendations (*Class X SSLC Math* & *R.S. Aggarwal*).
5. **Scenario 5**: 2nd PUC Physics recommendations (*Physics Parts I & II Class XII / 2nd PUC*).
6. **Scenario 6**: Diploma-level recommendations (*Applied Science*, *Mechanical*, *Civil*, *Electrical* for Diploma).
7. **Scenario 7**: Engineering Mathematics M2 recommendations (*B.S. Grewal*, *Erwin Kreyszig*, *Bali & Goyal*; 0 school books).
8. **Scenario 8**: Python book recommendations (*Python Crash Course*, *Automate the Boring Stuff*, *Fluent Python*).
9. **Scenario 9**: Kannada questions and native Kannada response generation.
10. **Scenario 10**: English questions and English response generation.
11. **Scenario 11**: Strict domain refusal of unrelated questions (biryani, cricket, jokes, politics) in English and Kannada without calling the LLM.
12. **Honesty Verification**: Unmatched catalogue query returns empty list and honest catalogue notice.
13. **Resource Opening & Details**:
    - Verified external URLs (Biology Class XII, Head First Java, Python Crash Course).
    - Books without external URLs (in-library physical collections with complete details).
    - Publisher column persistence and indexing.
    - `GET /api/resources/<id>` endpoint.
    - Frontend Book Details modal structure.
14. **Database & API Resilience**: Idempotent seeding, multi-filter search, health check, and offline Ollama error handling.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web frontend (`index.html`) |
| `GET` | `/api/health` | Health check reporting DB status, Ollama connectivity, and model availability |
| `GET` | `/api/subjects` | Retrieves all distinct academic subjects across school and college |
| `GET` | `/api/education-levels` | Retrieves all distinct educational tiers in catalogue |
| `GET` | `/api/departments` | Retrieves all distinct departments in catalogue |
| `GET` | `/api/resources` | Filters resources (`q`, `subject`, `level`, `education_level`, `class_grade`, `language`) |
| `GET` | `/api/resources/<id>` | Retrieves full details of a specific book by ID |
| `POST` | `/api/chat` | AI chat endpoint with language detection and catalogue grounding |

---

## ☁️ Cloud Deployment & Ollama Feasibility Analysis

When preparing to deploy this project to the cloud, consider how the Flask web application and the local Ollama LLM interact:

### 1. Can Ollama Run on Free-Tier Cloud Hosting?
- **Serverless / Static Hosts (Vercel, Netlify)**: **No**. Serverless platforms only support short-lived stateless functions (10-15s timeouts, 50-250MB RAM). They cannot run continuous background processes like `ollama serve`.
- **Free Container / PaaS Hosts (Render Free, Railway Hobby, Heroku Free)**: **No / Not Feasible**. Free tiers typically grant 512 MB RAM. Running `llama3.2:3b` requires ~2.5–3.5 GB of RAM to load model weights. Running Ollama on 512 MB causes immediate Out-Of-Memory (OOM) crashes.

### 2. Recommended Deployment Architectures (Zero Paid APIs)

#### Architecture A: Hybrid Deployment (100% Free & Recommended)
Deploy the Flask web app on free cloud hosting while running Ollama on your local laptop (which has 16 GB RAM):
1. Deploy the Flask app to **Render** or **Railway** using the included `Procfile` and `requirements.txt`.
2. On your local laptop, expose your running Ollama port (11434) securely using a free Cloudflare Tunnel:
   ```powershell
   cloudflared tunnel --url http://localhost:11434
   ```
3. Set the environment variable on your cloud host:
   ```env
   OLLAMA_BASE_URL=https://your-tunnel-url.trycloudflare.com
   ```
- **Cost**: $0.
- **Benefits**: The web application is publicly accessible on the internet 24/7, while the heavy AI model runs on your local machine with zero paid API tokens.

#### Architecture B: Self-Hosted Cloud VPS / Dedicated Server
Deploy both Flask and Ollama together on a VPS with at least 4 GB of RAM:
1. **Platforms**:
   - **Oracle Cloud Free Tier** (Always-Free 4 ARM cores + 24 GB RAM — 100% free!).
   - Low-cost VPS (DigitalOcean Droplet, Hetzner Cloud, Linode, AWS EC2 `t3.medium`).
2. **Setup on VPS**:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3.2:3b

   # Run Flask with Gunicorn
   pip install -r requirements.txt
   gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
   ```
- **Cost**: $0 on Oracle Cloud Free Tier, or $4–$10/month on standard VPS.

#### Architecture C: Standalone Catalogue Mode (Fallback)
Even if deployed without an Ollama instance, the entire library catalogue, keyword search, educational filters, and Book Details modal function **100% offline without crashing**. The AI chat interface gracefully displays an informational notice advising that AI recommendations require an active Ollama instance.

---

## 🛡️ License & Academic Notice

Built as an open educational library project. All textbook metadata and links reference legitimate official publishers and statutory educational boards (NCERT, DSERT Karnataka, Department of Pre-University Education Karnataka, and standard academic university presses).
