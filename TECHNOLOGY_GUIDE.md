# TalentVerifyAI — Technology Guide

## Architecture overview

TalentVerifyAI is a two-part web application:

```text
React/Vite browser application
          |
          | /api through the Vite proxy
          v
FastAPI Python backend
          |
          v
Google Gemini API or local fallback analysis
```

## Frontend technologies

### React 18

React builds the candidate and recruiter interfaces as reusable components. It manages login state, selected jobs, application reviews, modal forms, filters, and match-score sorting without full-page reloads.

### Vite 5

Vite provides the development server and production build system. It offers fast startup and hot module replacement. Its `/api` proxy forwards browser requests to FastAPI on port 8000 and avoids development-time origin and port problems.

### Tailwind CSS 3

Tailwind supplies utility classes for responsive layouts, spacing, colours, cards, forms, tables, status badges, and mobile behaviour. It keeps most styling close to the relevant React markup.

### Lucide React

Lucide supplies consistent interface icons for jobs, profiles, verification, editing, review actions, selection, shortlisting, and rejection.

### Browser session storage

The browser stores only the opaque session token needed to call the backend. Candidate profiles,
jobs, applications, CV records, GitHub snapshots, and verification results are stored in MongoDB
through FastAPI. The browser never receives database credentials.

## Backend technologies

### Python

Python supports document processing, text normalization, skill comparison, score calculation, and integration with generative AI libraries.

### FastAPI

FastAPI exposes authentication, profile, job, application, CV, GitHub, LinkedIn, and matrix
endpoints. Important evidence endpoints include:

- `POST /api/candidates/me/github/verify` — scans and stores GitHub repository evidence.
- `POST /api/candidates/me/linkedin/verify` — validates and stores a LinkedIn profile/post URL.
- `GET /api/candidates/{candidate_id}/skills/matrix` — returns the multi-source skills matrix.
- `POST /api/import-cv` — extracts text from an uploaded CV.
- `POST /api/analyze-cv` — compares a candidate with a selected job.

FastAPI was selected for its validation, async request support, clear API structure, and automatically generated Swagger documentation.

### Uvicorn

Uvicorn is the ASGI development server that runs the FastAPI application. Reload mode automatically restarts the backend when Python files change.

### python-multipart

This package enables FastAPI to receive CV uploads and `FormData` fields from the React frontend.

### pypdf and python-docx

- `pypdf` extracts readable text from PDF CVs.
- `python-docx` extracts text from Microsoft Word DOCX CVs.

Plain text CV files are also supported.

## AI and matching

### Google Gemini

Gemini analyzes candidate information against the requirements of the selected job. It produces structured JSON containing:

- Extracted professional skills
- Full, partial, and missing skill assessments
- Evidence for skill matches
- Candidate career guidance
- Recruiter hiring guidance
- Suggested selection, shortlisting, or rejection direction
- Strengths, risks, and interview focus

The backend instructs Gemini not to invent evidence or base recommendations on protected personal characteristics.

### Deterministic score reconciliation

The backend does not blindly accept an AI-generated percentage. It reconciles required skills and experience using deterministic rules:

- Full skill match: 100% skill credit
- Partial transferable match: 50% skill credit
- Missing skill: 0% skill credit
- When experience is required, skills contribute 80 points and experience contributes 20 points
- When no experience is required, skills contribute all 100 points

Mismatch is displayed as `100 - match score`.

### Local fallback analysis

If Gemini is unavailable or no API key is configured, the backend performs local skill and experience matching. This allows the main application flow to remain demonstrable offline, although Gemini gives richer explanations.

## Application data flow

1. A recruiter creates or edits a job with skills and experience requirements.
2. A candidate saves profile data, imports a CV, and optionally verifies GitHub and LinkedIn URLs.
3. React sends authenticated requests to FastAPI; FastAPI reads and writes MongoDB.
4. GitHub scans create immutable evidence snapshots; the skills matrix combines source flags.
5. FastAPI evaluates the selected job and reconciles the match score using deterministic rules.
6. The candidate confirms the application and the recruiter reviews evidence and status.

## Production improvements

For a production deployment, add a dedicated authentication service, store CVs in protected
object storage, strengthen rate limiting and observability, audit recruiter decisions, obtain
candidate consent, and treat AI recommendations as decision support rather than the final
employment decision.
