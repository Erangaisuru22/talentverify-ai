<div align="center">

# 🗄️ TalentVerify AI — Database Architecture & CRUD API Module
### Normalized 8-Collection MongoDB Schema & Comprehensive Postman Test Suite

[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas%20%2F%20Local-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![PyMongo](https://img.shields.io/badge/PyMongo-4.7+-47A248?style=for-the-badge&logo=python&logoColor=white)](https://pymongo.readthedocs.io)
[![Postman](https://img.shields.io/badge/Postman-49_CRUD_Endpoints-FF6C37?style=for-the-badge&logo=postman&logoColor=white)](https://postman.com)
[![Integrity](https://img.shields.io/badge/Schema_Validation-3NF_Compliant-007ACC?style=for-the-badge)](https://en.wikipedia.org/wiki/Third_normal_form)

<p align="center">
  <b>Lead Developers:</b> Hiruni & Pujani<br>
  <b>Branches:</b> <code>Hiruni</code> | <code>Pujani</code>
</p>

</div>

---

## 📖 Module Overview

The **Database Architecture Module** is responsible for structured persistent storage, relational data integrity, schema validation, and complete CRUD API coverage for the TalentVerify AI platform. 

The database is built on **MongoDB** and strictly organized into **8 normalized collections** adhering to **Third Normal Form (3NF)** principles. This design eliminates data anomalies, prevents orphaned records, and guarantees an auditable lifecycle for candidates, job vacancies, and AI evaluations.

---

## 📐 Entity Relationship (ER) & Schema Design

```
                     ┌───────────────────────┐
                     │         users         │
                     │  (Primary User Auth)  │
                     └──────────┬────────────┘
                                │
          ┌─────────────────────┴────────────────────────┐
          │ (1-to-1)                                     │ (1-to-many)
          ▼                                              ▼
┌───────────────────────┐                      ┌───────────────────────┐
│  candidate_profiles   │                      │         jobs          │
│ (Skills, Bio, Links)  │                      │ (Vacancies & Weights) │
└──────────┬────────────┘                      └──────────┬────────────┘
           │ (1-to-many)                                  │
           ├──────────────────────────┐                   │
           ▼                          ▼                   │
┌───────────────────────┐  ┌───────────────────────┐      │
│     cv_documents      │  │   evidence_snapshots  │      │
│ (Raw CV Files & Text) │  │  (GitHub Repo Scans)  │      │
└───────────────────────┘  └───────────────────────┘      │
                                                          │
          ┌───────────────────────────────────────────────┘
          │ (Many-to-Many Bridge)
          ▼
┌──────────────────────────────────────────────────────────────┐
│                         applications                         │
│             (Links Candidate to Applied Job Role)            │
└──────────┬───────────────────────────────────────────────────┘
           │ (1-to-many)
           ├───────────────────────────────────────────┐
           ▼                                           ▼
┌───────────────────────────────────────┐   ┌──────────────────────────────────────┐
│         candidate_evaluations         │   │        evaluation_audit_logs         │
│ (Versioned AI Scores & Match Reports) │   │ (Recruiter Overrides & Audit History)│
└───────────────────────────────────────┘   └──────────────────────────────────────┘
```

---

## 📋 The 8 Normalized Collections Breakdown

| # | Collection | ID Pattern | Purpose & Relationship | Key Fields & Indexes |
|---|---|---|---|---|
| **1** | `users` | `CAND-xxx` / `REC-xxx` | Core authentication, roles, session tokens | `email` (unique index), `passwordHash`, `role`, `token`, `createdAt` |
| **2** | `candidate_profiles` | `id` | Extended profile details (`userId` -> `users.id`) | `headline`, `experience`, `skills`, `social_links`, `portfolio_url` |
| **3** | `jobs` | `JOB-xxx` | Job listings created by recruiters (`recruiterId` -> `users.id`) | `title`, `company`, `experience`, `skills`, `scoring_weights` |
| **4** | `applications` | `APP-xxx` | Bridge entity (`userId` -> `users.id`, `jobId` -> `jobs.id`) | `status`, `appliedAt`, `overallScore`, `candidateSnapshot` |
| **5** | `candidate_evaluations` | `EVAL-xxx` | Historical AI evaluation records (`application_id`, `candidate_id`) | `scores`, `pre_interview_score`, `evaluation_version`, `model` |
| **6** | `cv_documents` | `CV-xxx` | Uploaded resumes & extracted plain text (`candidate_id` -> `users.id`) | `filename`, `content`, `extracted_skills`, `uploaded_at` |
| **7** | `evidence_snapshots` | `SNAP-xxx` | Scanned GitHub repositories and commit metrics (`candidate_id`) | `platform`, `repositories`, `languages`, `verification_status` |
| **8** | `evaluation_audit_logs` | `AUDIT-xxx` | Recruiter manual overrides (`application_id`, `recruiter_id`) | `category`, `recruiter_score`, `override_reason`, `timestamp` |

---

## 🧪 Postman 8-Collection CRUD Test Suite

A complete Postman test collection with **49 automated API requests** is included in the project:

- **Collection File:** [`TalentVerify_CRUD_API.postman_collection.json`](./TalentVerify_CRUD_API.postman_collection.json)
- **Environment File:** [`TalentVerify_Local.postman_environment.json`](./TalentVerify_Local.postman_environment.json)

### Supported Standard Operations for EVERY Collection:

1. **`findAll`** (`GET /api/crud/{collection}`): Fetch all collection documents.
2. **`findOne`** (`GET /api/crud/{collection}/{id}`): Fetch single document by ID.
3. **`save`** (`POST /api/crud/{collection}`): Create a new document with payload validation.
4. **`update`** (`PATCH /api/crud/{collection}/{id}`): Update fields of an existing document.
5. **`deleteOne`** (`DELETE /api/crud/{collection}/{id}`): Delete a specific document.
6. **`deleteAll`** (`DELETE /api/crud/{collection}?confirm=true`): Safety-gated bulk wipe.

---

## 🛠️ Validation & Seeder Scripts

### 1. Schema & Referential Integrity Validator
Run the validator script to ensure 100% relational integrity across all 8 collections with zero orphan foreign keys:
```powershell
python backend/database_validator.py
```
*Expected Output:*
```
[PASS] Users collection: 10 valid documents
[PASS] Candidate profiles: 8 documents (all valid Foreign Keys)
[PASS] Jobs collection: 6 documents (all valid recruiter IDs)
[PASS] Applications: 12 documents (all valid candidate & job IDs)
[PASS] Candidate evaluations: 12 documents
[PASS] CV documents: 14 documents
[PASS] Evidence snapshots: 14 documents
[PASS] Evaluation audit logs: 16 documents
SUCCESS: 8/8 collections passed integrity checks with 0 orphan references!
```

### 2. Database Normalization & Migration Seeder
To migrate and normalize any unseeded or legacy database data:
```powershell
python backend/normalize_database_schema.py
```
