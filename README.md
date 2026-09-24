# TalentVerify AI — Database & Schema Architecture Module
**Lead Developers:** Hiruni & Pujani

This module contains the complete normalized MongoDB database architecture, schema integrity validator, seeder scripts, data models, and the 8-Collection Postman CRUD API suite for the TalentVerify AI platform.

---

## 8-Collection Normalized Schema Design

The database is structured into 8 distinct collections aligned with Third Normal Form (3NF) principles, eliminating data redundancy while maintaining referential integrity across candidates, recruiters, jobs, applications, and AI evaluations.

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

### Detailed Collections Breakdown:

| # | Collection Name | Primary Key | Description & Foreign Key References |
|---|---|---|---|
| 1 | `users` | `id` (`CAND-xxx` / `REC-xxx`) | Authentication credentials, roles (`candidate`/`recruiter`), sessions. |
| 2 | `candidate_profiles` | `id` | Candidate bio, headline, experience, skills, social links (`userId` -> `users.id`). |
| 3 | `jobs` | `id` (`JOB-xxx`) | Vacancies, scoring weights, required skills (`recruiterId` -> `users.id`). |
| 4 | `applications` | `id` (`APP-xxx`) | Job applications (`userId` -> `users.id`, `jobId` -> `jobs.id`). |
| 5 | `candidate_evaluations` | `id` (`EVAL-xxx`) | Versioned AI evaluations (`application_id`, `candidate_id`, `job_id`). |
| 6 | `cv_documents` | `id` (`CV-xxx`) | Uploaded CV files, extracted raw text (`candidate_id` -> `users.id`). |
| 7 | `evidence_snapshots` | `id` (`SNAP-xxx`) | Verified GitHub repo stats, commits, language metrics (`candidate_id`). |
| 8 | `evaluation_audit_logs` | `id` (`AUDIT-xxx`) | Recruiter score adjustments, override justifications, hiring decisions. |

---

## Postman 8-Collection CRUD Test Suite

A complete Postman test collection with 49 automated requests is included:
- **Collection File:** `TalentVerify_CRUD_API.postman_collection.json`
- **Environment File:** `TalentVerify_Local.postman_environment.json`
- **Endpoints Supported for ALL 8 Collections:**
  1. `findAll` (GET) — Fetch all documents
  2. `findOne` (GET) — Fetch single document by ID
  3. `save` (POST) — Insert/create a new validated document
  4. `update` (PATCH) — Update fields of an existing document
  5. `deleteOne` (DELETE) — Delete single document by ID
  6. `deleteAll` (DELETE) — Safety-gated bulk deletion (`?confirm=true`)

---

## Database Validation & Seeder Scripts

### 1. Run Schema & Referential Integrity Validator:
```powershell
python backend/database_validator.py
```
*Validates that all foreign keys reference valid documents and all 8 collections are populated with zero orphan records.*

### 2. Run Database Normalization & Migration:
```powershell
python backend/normalize_database_schema.py
```
*Migrates and normalizes legacy data into the 8 distinct collections.*
