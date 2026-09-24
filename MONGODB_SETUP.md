# TalentVerifyAI MongoDB Setup

## Introduction

MongoDB is a document database. It stores JSON-like BSON documents in collections instead of
rows in relational tables. TalentVerifyAI uses it because candidate profiles, jobs, CV-analysis
results, and application snapshots contain flexible nested fields and arrays.

React must never connect directly to MongoDB. A browser connection would expose the database
username, password, and full database access to every visitor. This project uses:

```text
React UI -> HTTP REST API -> FastAPI -> PyMongo -> MongoDB
```

The supplied generic prompt mentioned Express and Mongoose. This project already uses Python,
so FastAPI replaces Express and the official PyMongo driver replaces Mongoose.

## MongoDB concepts

- **Cluster:** the MongoDB servers hosting databases.
- **Database:** the `talentverify` container inside the cluster.
- **Collection:** a group of similar documents, comparable to a table.
- **Document:** one JSON-like record.
- **Database user:** a server-side username/password permitted to access the cluster.
- **IP access list:** networks allowed to connect to an Atlas cluster.
- **Connection string:** the private URI used by FastAPI to connect.

## MongoDB Atlas setup

1. Create an account at MongoDB Atlas and create a free cluster.
2. Open **Database Access**, create an application user, and grant read/write access to the
   `talentverify` database. Do not reuse your Atlas account password.
3. Open **Network Access** and add your current public IP. Use `0.0.0.0/0` only temporarily for
   development because it allows connection attempts from every IP.
4. Click **Connect > Drivers > Python**, then copy the `mongodb+srv://...` URI.
5. Copy `backend/.env.example` to `backend/.env` and configure:

```env
MONGODB_URI=mongodb+srv://APP_USER:URL_ENCODED_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=talentverify
GEMINI_API_KEY=optional_key
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

Special password characters must be URL-encoded. `backend/.env` is ignored by Git; commit only
`.env.example`, which contains placeholders. Never create a `VITE_MONGODB_URI`: Vite variables
are delivered to browsers.

## Backend configuration

`backend/database.py` loads environment variables, creates the shared PyMongo client, selects
the database, and provides a connection check. FastAPI verifies MongoDB during startup and the
health endpoint verifies it on demand. A connection failure returns a clear service error or
prevents an unhealthy backend from pretending to be ready.

Local MongoDB can use:

```env
MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DB=talentverify
```

## Database Design (Core 6 Collections Architecture)

The database is simplified into **6 core collections** (plus an optional `audit_logs` collection for recruiter action auditing):

| # | Collection | Sinhala / Purpose | Key Fields & Relationships | Indexes |
|---|---|---|---|---|
| 1 | `users` | Candidates සහ recruitersගේ login/account data & session tokens | `id`, `role` ("candidate"\|"recruiter"), `email`, `passwordHash`, `token`, `name`, `company`, `headline`, `location`, `createdAt` | unique `email`, unique `id`, `token` |
| 2 | `candidate_profiles` | Candidate profile, skills, education, projects, experience (Unified document) | `id`, `user_id` -> `users.id`, `personal_info`, `social_links`, `skills` (with verification status), `technical_skills`, `soft_skills`, `experience`, `education`, `projects`, `certifications`, `languages` | unique `user_id`, unique `id`, `personal_info.email` |
| 3 | `jobs` | Job details, requirements සහ scoring weights | `id`, `recruiterId` -> `users.id`, `title`, `company`, `location`, `type`, `experience`, `skills`, `description`, `requirements`, `must_have_requirements`, `recommendation_bands`, `scoring_weights`, `createdAt` | unique `id`, `recruiterId` |
| 4 | `applications` | Applications, AI results, assessments සහ decisions | `id`, `userId` -> `users.id`, `jobId` -> `jobs.id`, `status`, `jobMatchScore`, `candidateProfileScore`, `scores`, `analysis`, `enterpriseEvaluation`, `evaluations`, `interviews_history`, `technical_assessments_history`, `score_overrides`, `final_decision` | unique `(userId, jobId)`, unique `id`, `jobId` |
| 5 | `cv_documents` | Uploaded CV සහ extracted data | `id`, `candidate_id` -> `users.id`, `file_name`, `content_type`, `content` (bytes), `parsing_status`, `uploaded_at`, `raw_gemini_result` | unique `id`, `candidate_id`, `uploaded_at` |
| 6 | `evidence_snapshots` | GitHub, LinkedIn සහ Portfolio evidence | `id`, `candidate_id` -> `users.id`, `platform` ("github"\|"linkedin"\|"portfolio"), `verified_at` / `scanned_at`, `repos`, `top_languages`, `raw_evidence`, `profile_data` | unique `id`, `(candidate_id, platform, scanned_at)` |

### Optional Collection:
| Collection | Sinhala / Purpose | Key Fields | Indexes |
|---|---|---|---|
| `audit_logs` | Recruiter changes සහ important actions history | `id`, `action`, `actor_id`, `entity_type`, `entity_id`, `metadata`, `created_at` | `(entity_type, entity_id, created_at)` |

The application uses UUID strings as public IDs. MongoDB also creates an internal `_id`, which
the API deliberately removes from responses. Password hashes are also removed.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend and MongoDB |
| POST | `/api/auth` | Register or login |
| DELETE | `/api/session` | Logout |
| GET | `/api/app-data` | Load the signed-in user's dashboard data |
| PATCH | `/api/profile` | Update the current profile |
| GET | `/api/jobs` | List jobs |
| GET | `/api/jobs/{id}` | Read one job |
| POST | `/api/jobs` | Recruiter creates a job |
| PATCH | `/api/jobs/{id}` | Owning recruiter updates a job |
| DELETE | `/api/jobs/{id}` | Owning recruiter deletes a job and its applications |
| POST | `/api/applications` | Candidate applies |
| DELETE | `/api/applications/{id}` | Candidate withdraws |
| PATCH | `/api/applications/{id}/status` | Owning recruiter changes status |
| POST | `/api/import-cv` | Extract text from a CV |
| POST | `/api/analyze-cv` | Analyze compatibility |
| POST | `/api/candidates/me/github/verify` | Verify and store GitHub repository evidence |
| POST | `/api/candidates/me/linkedin/verify` | Validate and store a LinkedIn profile/post URL |
| GET | `/api/candidates/{candidate_id}/skills/matrix` | Read the multi-source technical skills matrix |
- **Evidence matrix:** FastAPI starts with saved technical skills and marks evidence from CV,
  experience, projects, GitHub, portfolio, and LinkedIn. Portfolio/LinkedIn links are available
  link evidence; GitHub receives repository-level technical verification.

Protected routes currently receive an opaque session token as a query parameter. Recruiter
routes enforce resource ownership, candidate withdrawal enforces user ownership, duplicate
emails/applications are rejected, and passwords use PBKDF2-HMAC-SHA256 with random salts.

## Data flows

- **Registration:** React posts details -> FastAPI validates and hashes the password -> PyMongo
  inserts `users` -> FastAPI creates `sessions` -> React stores only the opaque token.
- **Login:** FastAPI finds the email/role, verifies the hash, inserts a session, and returns safe
  user fields.
- **Create job:** FastAPI verifies recruiter role, attaches the authenticated recruiter ID, and
  inserts into `jobs`.
- **View jobs:** React requests app data; FastAPI reads jobs and returns JSON.
- **Apply:** FastAPI rejects a duplicate `(userId, jobId)` and inserts the analysis snapshot.
- **Recruiter review:** FastAPI finds jobs owned by the recruiter and returns only applications
  related to those jobs.

## CRUD examples

After login, replace `TOKEN` and `JOB_ID`:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod "http://127.0.0.1:8000/api/jobs?token=TOKEN"
Invoke-RestMethod -Method Patch "http://127.0.0.1:8000/api/jobs/JOB_ID?token=TOKEN" -ContentType application/json -Body '{"data":{"location":"Remote"}}'
Invoke-RestMethod -Method Delete "http://127.0.0.1:8000/api/jobs/JOB_ID?token=TOKEN"
```

## MongoDB Compass

1. Install Compass and paste the same `MONGODB_URI` into **New Connection**.
2. Connect and open `talentverify`; the collections appear after the app first runs.
3. Open a collection to view documents. Use **Add Data > Insert Document** for test JSON.
4. Use the pencil icon to edit, or the trash icon to delete a test document.
5. Avoid changing demo IDs, password hashes, relationships, or production data manually.

## Run and test

One-time setup:

```powershell
python -m venv backend\venv; .\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt; npm.cmd install --prefix frontend
```

Start MongoDB and then run the complete system from the project root:

```powershell
npm.cmd run dev
```

Open `http://127.0.0.1:5173` and API docs at `http://127.0.0.1:8000/docs`. Test candidate and
 Test candidate and recruiter registration/login, profile update, LinkedIn URL verification, GitHub
 scan, matrix loading, job create/update/delete, application submission, withdrawal, and recruiter
 status changes. The frontend uses `src/services/api.js`; it never receives database credentials.

## Troubleshooting

- **Connection refused:** start local MongoDB or verify the Atlas URI.
- **Authentication failed:** verify database username, password, and URL encoding.
- **IP not allowed:** add the current IP in Atlas Network Access.
- **Port in use:** the root launcher reuses a healthy TalentVerify service already on 8000/5173.
- **CORS error:** add the exact frontend origin to `CORS_ORIGINS`, then restart FastAPI.
- **Frontend cannot reach backend:** open `/api/health` and confirm Vite's `/api` proxy target.
- **Empty database:** call `/api/health` or login once; startup creates indexes and demo records.
