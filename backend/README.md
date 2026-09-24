<div align="center">

# ⚙️ TalentVerify AI — Backend & AI Engine Module
### High-Performance Asynchronous REST API & Gemini Evaluation Pipeline

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-499848?style=for-the-badge)](https://www.uvicorn.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev)

<p align="center">
  <b>Lead Developers:</b> Baskaran Tharmika & MuraliTharanT<br>
  <b>Branches:</b> <code>Tharmika</code> | <code>Murali</code>
</p>

</div>

---

## 📖 Module Overview

The **Backend Module** powers the core intelligence and business logic of the TalentVerify AI platform. Built with **FastAPI** on **Python 3.10+**, it exposes asynchronous RESTful endpoints for resume ingestion, semantic skill extraction via **Google Gemini AI**, automated code verification through the **GitHub API**, multi-dimensional candidate-to-job matching, and recruiter audit trail management.

---

## 🔑 Core Services & Architectural Modules

### 1. 🚀 Asynchronous Web Server (`main.py`)
- High-concurrency ASGI request handling with FastAPI and Uvicorn.
- Token-based session verification (`require_session`) and role-based access control (RBAC).
- Startup event handler ensuring database connectivity, indexes, and weight backfilling.
- Cascading deletion handler for job removals (cleans applications, evaluations, and audit logs).

### 2. 🧠 Enterprise Evaluation Engine (`services/enterprise_job_evaluation_service.py`)
- Integrates Google Gemini AI (Flash) with structured prompt engineering.
- Evaluates candidates across 9 distinct categories: Technical Skills, Relevant Experience, Projects, GitHub Evidence, Education, Soft Skills, Languages, Professional Alignment, and Certifications.
- Deterministic fallback scoring engine ensures zero system downtime if external AI APIs are unreachable.

### 3. 🔍 Multi-Source Evidence Scanners
- **GitHub Scanner (`github_evidence.py` & `services/github_service.py`):** Connects to the GitHub API, inspects public repositories, extracts commit frequencies, evaluates language distributions, and scores code quality.
- **Portfolio & LinkedIn Verification (`portfolio_evidence.py`, `linkedin_evidence.py`):** Validates external profile links with HTTP verification and timestamped evidence records.

### 4. 📝 Audit & Overrides Subsystem (`assessment_routes.py`)
- Versioned evaluations (`/api/applications/{id}/re-evaluate`) that capture snapshot history over time (`Version 1`, `Version 2`).
- Recruiter override endpoints allowing hiring managers to adjust category scores with mandatory audit justification strings.

---

## 📂 Backend Source Structure

```
backend/
├── main.py                      # FastAPI app entry point & route definitions
├── database.py                  # PyMongo client, collection handles, & schema indexes
├── crud_routes.py               # Standardized 8-collection CRUD API router
├── database_validator.py        # Referential integrity & collection consistency checker
├── normalize_database_schema.py # 8-collection database seeder & migration script
├── assessment_routes.py         # Recruiter score override & assessment endpoints
├── enterprise_evaluation.py     # Evaluation data normalizer & score calculations
├── github_evidence.py           # GitHub repository scraper & evidence analyzer
├── linkedin_evidence.py         # LinkedIn evidence checker
├── portfolio_evidence.py        # Portfolio evidence validator
├── requirements.txt             # Python package dependencies
├── .env.example                 # Template for environment variables
│
├── models/                      # Pydantic Schemas & DTOs
│   ├── candidate.py             # Candidate profile schemas
│   ├── score.py                 # Multi-dimensional score breakdown models
│   ├── github.py                # GitHub snapshot models
│   ├── project.py               # Project models
│   └── experience.py            # Experience models
│
├── repositories/                # Data Access Layer
│   ├── candidate_repository.py  # Candidate profile MongoDB queries
│   ├── job_repository.py        # Job posting queries
│   └── github_repository.py     # GitHub snapshot queries
│
└── services/                    # Business Logic Layer
    ├── cv_analysis_service.py   # CV text extraction & Gemini prompt parser
    ├── enterprise_job_evaluation_service.py # Gemini role evaluation engine
    ├── github_service.py        # GitHub API service
    ├── job_match_service.py     # Scoring formula calculations
    └── scoring_service.py       # Deterministic scoring fallbacks
```

---

## 🚀 How to Run Locally

### 1. Set Up Python Virtual Environment
```powershell
python -m venv backend\venv
.\backend\venv\Scripts\activate
```

### 2. Install Requirements
```powershell
pip install -r backend\requirements.txt
```

### 3. Configure Environment Variables (`backend\.env`)
Create a `.env` file inside the `backend/` directory:
```dotenv
MONGODB_URI=mongodb://127.0.0.1:27017/talentverify
GEMINI_API_KEY=your_google_gemini_api_key
GITHUB_TOKEN=your_optional_github_token
```

### 4. Start Uvicorn Server
```powershell
uvicorn backend.main:app --reload --port 8000
```

- **Interactive Swagger Documentation:** 👉 **http://127.0.0.1:8000/docs**
- **ReDoc Documentation:** 👉 **http://127.0.0.1:8000/redoc**
- **Health Check Endpoint:** 👉 **http://127.0.0.1:8000/api/health**
