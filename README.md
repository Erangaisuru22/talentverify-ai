# TalentVerify AI
### Intelligent Multi-Source Candidate Screening & Verification Platform

TalentVerify AI is an advanced AI-powered web platform designed to streamline and automate technical candidate screening. It bridges candidates and recruiters by combining intelligent CV parsing, GitHub code evidence verification, portfolio validation, and transparent multi-dimensional job matching.

---

## Key Highlights & Capabilities

- **AI-Powered CV Parsing:** Uses Google Gemini API to extract technical skills, soft skills, projects, and work history directly from PDF, DOCX, and TXT files.
- **GitHub Code Evidence Verification:** Connects to GitHub API to scan candidate repositories, analyze language distributions, code quality indicators, and verify declared skills against real code commits.
- **Normalized 8-Collection MongoDB Architecture:** Fully normalized database schema (`users`, `candidate_profiles`, `jobs`, `applications`, `candidate_evaluations`, `cv_documents`, `evidence_snapshots`, `evaluation_audit_logs`) guaranteeing referential integrity and complete auditability.
- **Dual Role Portals:**
  - **Candidate Portal:** Real-time job discovery, instant AI compatibility analysis, strengths & skill gap insights, and application tracking.
  - **Recruiter Portal:** Job posting management, applicant ranking, evaluation versioning (`Re-evaluate with Latest Evidence`), and documented recruiter score overrides.
- **Postman CRUD API:** Full RESTful collection covering `findAll`, `findOne`, `save`, `updateOne`, `deleteOne`, and `deleteAll` across all 8 database collections.

---

## Technology Stack

- **Frontend:** React 18, Vite, TailwindCSS, Vanilla CSS, Lucide Icons
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **AI & Evaluation:** Google Gemini AI (2.5 / Flash), Multi-dimensional Scoring Engine
- **Database:** MongoDB / PyMongo (Normalized 8 collections)
- **API Testing:** Postman Collection v2.1 with local environment

---

## Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- Node.js (v18 or higher) & npm
- MongoDB Community Server running locally on port `27017`

### 2. Quick Start

Start MongoDB, open your terminal in the project root, and run:

```cmd
start_app.bat
```

Or run via npm:

```powershell
npm.cmd run dev
```

- **Frontend Application:** [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Backend Interactive API (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

To stop running servers cleanly:
```cmd
stop_app.bat
```

---

## First-Time Manual Setup

### Backend Setup:
```powershell
python -m venv backend\venv
.\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Create `backend\.env` file (copy from `backend\.env.example` if available):
```dotenv
MONGODB_URI=mongodb://127.0.0.1:27017/talentverify
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_optional_github_token_here
```

### Frontend Setup:
```powershell
cd frontend
npm install
npm run build
```

---

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| **Recruiter** | `recruiter@gmail.com` | `recruiter123` |
| **Candidate** | `candidate@gmail.com` | `candidate123` |

---

## Project Structure

```
talentverify/
├── backend/
│   ├── main.py                  # FastAPI application entrypoint & API routes
│   ├── database.py              # MongoDB connection & collection references
│   ├── crud_routes.py           # Standardized 8-collection CRUD API router
│   ├── database_validator.py    # Database schema & foreign key integrity validator
│   ├── normalize_database_schema.py # 8-collection normalization & seeder
│   └── services/                # Gemini CV parsing, scoring & evaluation services
├── frontend/
│   ├── src/
│   │   ├── pages/               # CandidateDashboard, RecruiterDashboard, LoginPage
│   │   ├── components/          # Header, BrandLogo, Modals
│   │   └── services/api.js      # REST API client
│   └── vite.config.js
├── postman/                     # Postman 8-collection test suites
├── TalentVerify_CRUD_API.postman_collection.json
├── start_app.bat                # 1-click startup script
├── stop_app.bat                 # 1-click shutdown script
└── README.md
```
