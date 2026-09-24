# TalentVerifyAI Run Guide

## One-line run command

From the project root in PowerShell:

```powershell
npm.cmd run dev
```

Open http://127.0.0.1:5173 after Vite reports that it is ready. This command supervises the
React frontend and FastAPI backend together. If a healthy TalentVerify backend is already on
port 8000, the launcher safely reuses it. Stop the app with `Ctrl+C`.

## One-line first-time setup

```powershell
python -m venv backend\venv; .\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt; npm.cmd install --prefix frontend
```

MongoDB must be running locally, or `MONGODB_URI` in `backend/.env` must point to MongoDB
Atlas. Copy `backend/.env.example` to `backend/.env` to customize the database or add an
optional Gemini API key.

## URLs

- App: http://127.0.0.1:5173
- API: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

## Evidence verification walkthrough

1. Sign in as a candidate and open **Profile**.
2. Add technical skills, a portfolio URL, and a LinkedIn profile or post URL.
3. Use **Verify LinkedIn URL** to validate and save the LinkedIn link.
4. Use **Refresh GitHub Scan** to collect repository evidence from GitHub.
5. Open **Details** under **Multi-Source Technical Skills Matrix** to inspect evidence by skill.
6. Use **See more** when more than 32 saved technical skills are available.

Portfolio and LinkedIn links are displayed as available sources. GitHub is the source that
currently receives repository-level technical verification. LinkedIn post content is not scanned
without a configured official LinkedIn integration.

## Demo login

- Candidate: `candidate@gmail.com` / `abcd123@`
- Recruiter: `recruiter@gmail.com` / `abcd123@`

Never open `frontend/index.html` directly. If the page was previously blank, restart the app
and use `Ctrl+F5` or clear site data for `127.0.0.1`.
