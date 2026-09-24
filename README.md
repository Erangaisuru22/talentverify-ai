# TalentVerify AI — Backend & AI Engine Module
**Lead Developers:** Baskaran Tharmika & MuraliTharanT

The Backend module of TalentVerify AI provides the asynchronous REST API server, AI-assisted CV evaluation engine, multi-dimensional scoring pipeline, and external evidence verification services.

---

## Architecture & Core Modules

1. **FastAPI Server (`main.py`):**
   - High-throughput asynchronous REST API endpoints.
   - Session authentication (`require_session`), role access control, and cascading job deletion for recruiters.

2. **Enterprise Evaluation Pipeline (`services/enterprise_job_evaluation_service.py`):**
   - Integrates Google Gemini AI (2.5 / Flash) for automated resume analysis.
   - Evaluates mandatory criteria, skills match, experience gaps, and verification quality.
   - Employs deterministic scoring fallbacks if AI services are unavailable.

3. **Multi-Source Evidence Verification:**
   - **GitHub Evidence (`github_evidence.py`, `services/github_service.py`):** Scans candidate repositories, checks language relevance, and code quality.
   - **Portfolio & LinkedIn Validation (`portfolio_evidence.py`, `linkedin_evidence.py`).

4. **Audit & Overrides System (`assessment_routes.py`):**
   - Allows recruiters to log assessment marks and override category scores with mandatory audit justification.
   - Versioned evaluation history (`/api/applications/{id}/re-evaluate`).

---

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI, Uvicorn, Starlette
- **Data Validation:** Pydantic v2
- **AI Engine:** Google Gemini AI API (`google-generativeai`)
- **Database Driver:** PyMongo / MongoDB

---

## How to Run Backend

```powershell
# 1. Create and activate virtual environment
python -m venv backend\venv
.\backend\venv\Scripts\activate

# 2. Install dependencies
pip install -r backend\requirements.txt

# 3. Start server
uvicorn backend.main:app --reload --port 8000
```

- **Interactive API Documentation (Swagger):** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **Health Check:** `http://127.0.0.1:8000/api/health`
