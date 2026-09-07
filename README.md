# TalentVerifyAI

TalentVerifyAI is a React + Tailwind frontend with a FastAPI backend and MongoDB storage. It
supports candidate CV/profile evidence, GitHub repository verification, portfolio and LinkedIn
link evidence, job-specific scoring, and recruiter review.

## Current evidence features

- GitHub profiles are scanned through the GitHub API for repositories, languages, technologies,
	repository quality, and skill-level evidence.
- The Multi-Source Technical Skills Matrix combines CV, experience, projects, GitHub, portfolio,
	and LinkedIn sources for each saved technical skill.
- Portfolio and LinkedIn links are validated as public HTTP/HTTPS links and shown as clickable
	evidence sources in the matrix.
- Candidates can verify a LinkedIn profile or post URL. This verifies the URL format and stores a
	timestamp; it does not claim that LinkedIn post content or identity was independently verified.
- The matrix initially shows 32 rows and provides a `See more` control for additional skills.

## Run the app

Start MongoDB, open PowerShell in this folder, and run:

```powershell
npm.cmd run dev
```

Then open **http://127.0.0.1:5173**. Do not open `frontend/index.html` directly; Vite must serve it.
The API documentation is at **http://127.0.0.1:8000/docs**. Press `Ctrl+C` to stop the app.

## First-time installation

```powershell
python -m venv backend\venv; .\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt; npm.cmd install --prefix frontend
```

Copy `backend/.env.example` to `backend/.env`. The Gemini key is optional because the app has
a local analysis fallback. MongoDB defaults to `mongodb://127.0.0.1:27017`.

For GitHub evidence verification, add an optional token to `backend/.env`:

```dotenv
GITHUB_TOKEN=your_fine_grained_token
```

Public profiles also work without a token, but GitHub applies a much lower anonymous API rate
limit. The token stays in the backend; candidates only submit a public profile URL or username.

## Demo accounts

- Candidate: `candidate@gmail.com` / `abcd123@`
- Recruiter: `recruiter@gmail.com` / `abcd123@`

## White-screen troubleshooting

1. Open the exact Vite URL: http://127.0.0.1:5173.
2. Hard-refresh with `Ctrl+F5`, or clear site data for `127.0.0.1`.
3. Confirm MongoDB is running if login reports a database error.

## Production build check

```powershell
npm.cmd run build --prefix frontend
```
