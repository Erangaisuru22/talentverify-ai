<div align="center">

# 🎯 TalentVerify AI
### Intelligent Multi-Source Candidate Screening & Technical Verification Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas%20%2F%20Local-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-2.5_Flash-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Postman](https://img.shields.io/badge/Postman-CRUD_API_Suite-FF6C37?style=for-the-badge&logo=postman&logoColor=white)](https://postman.com)

<p align="center">
  <b>TalentVerify AI</b> bridges candidates and hiring recruiters by unifying AI-powered CV parsing, real-world GitHub code evidence validation, multi-dimensional job matching, and transparent audit logging into a single cohesive platform.
</p>

---

</div>

## 📑 Table of Contents
1. [Project Overview & Objectives](#-project-overview--objectives)
2. [System Architecture & Workflow](#-system-architecture--workflow)
3. [Key Highlights & Innovation](#-key-highlights--innovation)
4. [Team Contributions & Branch Map](#-team-contributions--branch-map)
5. [Database Architecture (8 Normalized Collections)](#-database-architecture-8-normalized-collections)
6. [Technology Stack](#-technology-stack)
7. [Installation & Getting Started](#-installation--getting-started)
8. [Demo User Accounts](#-demo-user-accounts)
9. [Postman CRUD API Testing](#-postman-crud-api-testing)
10. [Repository Structure](#-repository-structure)

---

## 🌟 Project Overview & Objectives

Traditional resume screening relies heavily on keyword matching and self-claimed achievements on static CVs, resulting in high false-positive rates and recruiter fatigue. **TalentVerify AI** solves this by:

- **Automating Resume Ingestion:** Extracting structured technical skills, soft skills, projects, and work history with Google Gemini AI.
- **Validating Technical Evidence:** Connecting directly to candidate GitHub profiles to analyze language distributions, code quality indicators, repository velocity, and commit history.
- **Fair & Multi-Dimensional Scoring:** Calculating objective compatibility scores across technical skills, relevant experience, projects, education, and verified code evidence.
- **Protecting Candidate Privacy:** Presenting high-level match percentages and career advice to candidates, while preserving granular calculation rubrics for recruiters.
- **Maintaining Full Auditability:** Recording recruiter score overrides and versioning AI evaluation snapshots over time (`Version 1`, `Version 2`).

---

## 🏗 System Architecture & Workflow

```
[ Candidate / CV Document ]
           │
           ▼
[ Google Gemini AI Engine ] ──── (Extracts Skills, History, Projects)
           │
           ├───► [ GitHub API Scanner ] ───► (Validates real code repositories)
           │
           ▼
[ Enterprise Evaluation Engine ] ───► (Calculates 100-point compatibility score)
           │
           ▼
[ 8 Normalized MongoDB Collections ] 
           │
   ┌───────┴────────────────────────────────────────┐
   ▼                                                ▼
[ Candidate Portal ]                       [ Recruiter Portal ]
- Match Score % & Status                   - Applicant Ranking
- AI Career Guidance & Gaps                - Evaluation Versioning
- Application Tracking                     - Score Overrides & Audit Logs
```

---

## 🚀 Key Highlights & Innovation

### 1. Dual Role-Based Portals
- **Candidate Portal:** Real-time job search, instant AI CV parsing, matching scores, strength and gap insights, and application status tracking.
- **Recruiter Portal:** Job posting creation/editing/deletion, candidate ranking, detailed evaluation drawer, versioned re-evaluations, and score overrides.

### 2. Session Security
- Implements tab-scoped `sessionStorage` token management. Closing the browser tab or window automatically clears the session, ensuring zero stale credential exposure.

### 3. Cascading Data Cleanup
- Demo recruiter (`recruiter@gmail.com`) can safely delete job postings with full cascading cleanup across linked applications, evaluations, and audit records.

---

## 👥 Team Contributions & Branch Map

To support modular development and clear ownership, the repository is structured across dedicated Git branches:

| Module | Team Members | Branch Name | Responsibilities |
|---|---|---|---|
| **Frontend & UI/UX** | **Eranga Isuru Bandara** (Lead) | [`Eranga`](https://github.com/Erangaisuru22/talentverify-ai/tree/Eranga) | React 18 SPA, Vite setup, Candidate & Recruiter Dashboards, Responsive UI, Session persistence. |
| **Backend & AI Pipeline** | **MuraliTharanT & Baskaran Tharmika** | [`Murali`](https://github.com/Erangaisuru22/talentverify-ai/tree/Murali)<br>[`Tharmika`](https://github.com/Erangaisuru22/talentverify-ai/tree/Tharmika) | FastAPI REST API, Google Gemini AI pipeline, Multi-source evaluation engine, Assessment & override routes. |
| **Database & Modeling** | **Hiruni & Pujani** | [`Hiruni`](https://github.com/Erangaisuru22/talentverify-ai/tree/Hiruni)<br>[`Pujani`](https://github.com/Erangaisuru22/talentverify-ai/tree/Pujani) | MongoDB 8-collection normalization, Schema validator, Referential integrity rules, Postman CRUD test suite. |
| **Master Production** | **Entire Team** | [`main`](https://github.com/Erangaisuru22/talentverify-ai/tree/main) | Production-ready integrated platform unifying Frontend, Backend, and Database. |

---

## 🗄 Database Architecture (8 Normalized Collections)

The database strictly follows Third Normal Form (3NF) principles, eliminating duplicate records and ensuring full referential integrity:

```
       [users]
       ├── candidate_profiles (1-to-1)
       │    ├── cv_documents (1-to-many)
       │    └── evidence_snapshots (1-to-many: GitHub, LinkedIn, Portfolio)
       │
       └── jobs (1-to-many, created by Recruiters)
            └── applications (Many-to-Many bridge: candidate + job)
                 ├── candidate_evaluations (1-to-many versioned evaluations)
                 └── evaluation_audit_logs (1-to-many score overrides & audit trails)
```

| # | Collection Name | Primary Key | Description & Foreign Key References |
|---|---|---|---|
| 1 | `users` | `id` (`CAND-xxx` / `REC-xxx`) | Authentication credentials, roles (`candidate`/`recruiter`), password hashes. |
| 2 | `candidate_profiles` | `id` | Bio, headline, experience, technical & soft skills (`userId` -> `users.id`). |
| 3 | `jobs` | `id` (`JOB-xxx`) | Vacancies, required skills, scoring weights (`recruiterId` -> `users.id`). |
| 4 | `applications` | `id` (`APP-xxx`) | Job applications linking candidate and job (`userId` -> `users.id`, `jobId` -> `jobs.id`). |
| 5 | `candidate_evaluations` | `id` (`EVAL-xxx`) | Versioned AI evaluations (`application_id`, `candidate_id`, `job_id`). |
| 6 | `cv_documents` | `id` (`CV-xxx`) | Stored CV files, parsed text, upload timestamps (`candidate_id` -> `users.id`). |
| 7 | `evidence_snapshots` | `id` (`SNAP-xxx`) | Scanned GitHub repositories, language metrics, code quality (`candidate_id`). |
| 8 | `evaluation_audit_logs` | `id` (`AUDIT-xxx`) | Recruiter score adjustments, override justifications, hiring decisions. |

---

## 💻 Technology Stack

- **Frontend:** React 18, Vite, TailwindCSS, Vanilla CSS, Lucide Icons
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Starlette, Pydantic v2
- **AI & Evaluation:** Google Gemini AI API (`gemini-2.5-flash` / fallback heuristics)
- **Database:** MongoDB Community Server / MongoDB Atlas, PyMongo
- **Testing & Tooling:** Postman v2.1 Collections & Environments

---

## ⚡ Installation & Getting Started

### 1. Prerequisites
- **Python:** 3.10 or higher ([Download](https://www.python.org/downloads/))
- **Node.js:** v18 or higher ([Download](https://nodejs.org/))
- **MongoDB:** Community Server running locally on port `27017` ([Download](https://www.mongodb.com/try/download/community))

---

### 2. One-Click Quick Start (Windows)

Make sure MongoDB is running, open a terminal in the project root, and execute:

```cmd
start_app.bat
```

Or start both servers simultaneously via npm:

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

### 3. Manual Step-by-Step Setup

#### Backend Setup:
```powershell
# 1. Create and activate Python virtual environment
python -m venv backend\venv
.\backend\venv\Scripts\activate

# 2. Install dependencies
pip install -r backend\requirements.txt

# 3. Configure environment variables (backend\.env)
# MONGODB_URI=mongodb://127.0.0.1:27017/talentverify
# GEMINI_API_KEY=your_gemini_api_key_here
# GITHUB_TOKEN=your_github_token_optional

# 4. Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

#### Frontend Setup:
```powershell
cd frontend
npm install
npm run dev
```

---

## 🔑 Demo User Accounts

| Role | Email | Password | Access Capabilities |
|---|---|---|---|
| **Recruiter** | `recruiter@gmail.com` | `recruiter123` | Create/Delete jobs, view applicants, override scores, re-evaluate. |
| **Candidate** | `candidate@gmail.com` | `candidate123` | Search jobs, upload CV, view match score, track application status. |

---

## 🧪 Postman CRUD API Testing

A complete Postman test suite covering all **8 normalized collections** (49 total automated endpoints) is included in the project root:

- **Collection File:** [`TalentVerify_CRUD_API.postman_collection.json`](./TalentVerify_CRUD_API.postman_collection.json)
- **Environment File:** [`TalentVerify_Local.postman_environment.json`](./TalentVerify_Local.postman_environment.json)

### Supported Operations for every Collection:
1. `findAll` (GET) — Retrieve all documents
2. `findOne` (GET) — Retrieve single document by ID
3. `save` (POST) — Create new validated document
4. `update` (PATCH) — Partial update by ID
5. `deleteOne` (DELETE) — Delete single document by ID
6. `deleteAll` (DELETE) — Safety-gated bulk deletion (`?confirm=true`)

### Database Integrity Verification:
```powershell
python backend/database_validator.py
```
*Validates that all foreign key references are intact and collections have zero orphan records.*

---

## 📁 Repository Structure

```
talentverify/
├── backend/
│   ├── main.py                     # FastAPI application entrypoint & routing
│   ├── database.py                 # MongoDB client, collections & indexes
│   ├── crud_routes.py              # Standardized 8-collection CRUD API router
│   ├── database_validator.py       # Referential integrity validator
│   ├── normalize_database_schema.py# 8-collection schema normalizer & seeder
│   ├── assessment_routes.py        # Recruiter overrides & audit endpoints
│   ├── github_evidence.py          # GitHub API integration & repo scanner
│   ├── requirements.txt            # Python dependencies
│   ├── models/                     # Pydantic schemas (User, Job, Evaluation, etc.)
│   └── services/                   # Gemini CV parsing & scoring engine
├── frontend/
│   ├── src/
│   │   ├── pages/                  # CandidateDashboard, RecruiterDashboard, LoginPage
│   │   ├── components/             # Header, BrandLogo, Modals
│   │   └── services/api.js         # REST API client
│   ├── package.json
│   └── vite.config.js
├── postman/                        # Postman collection YAML source files
├── TalentVerify_CRUD_API.postman_collection.json
├── TalentVerify_Local.postman_environment.json
├── start_app.bat                   # 1-click startup script
├── stop_app.bat                    # 1-click shutdown script
└── README.md                       # Comprehensive platform documentation
```

---

<div align="center">
  <b>TalentVerify AI</b> — Objective, Evidence-Based Hiring Powered by AI.
</div>
