# TalentVerifyAI — How the AI Works

## Purpose

TalentVerifyAI compares a candidate’s profile or CV with the requirements of one selected job. It produces decision-support information for two audiences:

- Candidate guidance explains strengths, missing skills, and how to improve.
- Recruiter guidance explains job fit, hiring concerns, and what to validate before selecting, shortlisting, or rejecting a candidate.

The AI recommendation supports human review. It must not be treated as the final employment decision.

## End-to-end AI workflow

Before job scoring, the candidate profile can be enriched with structured CV records and external
evidence. GitHub repository data is collected through the GitHub API. Portfolio and LinkedIn URLs
are validated and exposed as source links in the Multi-Source Technical Skills Matrix. LinkedIn
URL verification stores the URL and verification time; it does not scrape LinkedIn posts or claim
identity verification.

### 1. The recruiter defines the job

Each job contains:

- Job title
- Required skills
- Required experience
- Company and location
- Employment type
- Job description

The analysis always uses the requirements of the particular job selected by the candidate. Therefore, the same candidate can receive different results for different jobs.

### 2. The candidate supplies information

The candidate can use their saved profile or upload a CV in PDF, DOCX, or TXT format.

The frontend sends the following information to the backend:

- Selected job title
- Required skills
- Required years of experience
- Candidate profile or extracted CV text
- Candidate years of experience

### 3. The backend extracts CV text

The `POST /api/import-cv` endpoint processes the uploaded file:

- PDF text is extracted with `pypdf`.
- DOCX text is extracted with `python-docx`.
- TXT content is decoded as text.

Empty files, unsupported file types, files larger than 10 MB, and scanned PDFs without readable text are rejected with a clear error.

### 4. Gemini receives a structured prompt

The `POST /api/analyze-cv` endpoint sends Gemini a controlled prompt containing only the relevant job and candidate information.

Gemini is instructed to:

- Extract genuine professional skills.
- Normalize equivalent skill names.
- Evaluate every required skill as Full, Partial, or Missing.
- Provide a short factual evidence statement for each assessment.
- Avoid inferring a skill from a job title alone.
- Avoid inventing candidate experience.
- Return structured JSON instead of free-form text.
- Generate candidate career guidance.
- Generate professional recruiter hiring guidance.
- Avoid using protected personal characteristics in hiring guidance.

## Structured AI result

Gemini returns a JSON object with information similar to this:

```json
{
  "score": 75,
  "matched_skills": ["React", "JavaScript"],
  "missing_skills": ["Docker"],
  "extracted_skills": ["React", "JavaScript", "SQL"],
  "skill_assessments": [
    {
      "skill": "React",
      "status": "Full",
      "evidence": "React project experience is stated in the CV"
    },
    {
      "skill": "Docker",
      "status": "Missing",
      "evidence": "No supporting evidence found"
    }
  ],
  "ai_suggestion": "Candidate-focused improvement guidance",
  "recruiter_guidance": {
    "recommendation": "Shortlist",
    "reason": "The candidate meets most core requirements but has one important gap.",
    "strengths": "Strong React and JavaScript evidence",
    "risks": "No verified Docker experience",
    "interview_focus": "Validate deployment knowledge with a practical scenario"
  }
}
```

## Deterministic score calculation

Gemini does not have final control over the displayed score. After receiving the AI response, the Python backend recalculates and reconciles the score using fixed rules.

### Skill credit

- Full match: `1.0` credit
- Partial or transferable match: `0.5` credit
- Missing skill: `0` credit

Duplicate requirements are removed before scoring.

### Skills and experience weighting

When a job requires experience:

- Skills contribute up to 80 points.
- Experience contributes up to 20 points.

```text
Final score = skill points + experience points
```

The experience score is capped at the required amount. Extra years do not increase the result above the maximum experience points.

When a job requires zero years of experience, skills contribute all 100 points.

### Mismatch score

```text
Mismatch score = 100 - match score
```

The score breakdown and per-skill points are saved with the application for later review.

## Candidate guidance

Candidate guidance is shown only on the candidate side. It focuses on professional development rather than hiring decisions.

It can include:

- Skills already demonstrated
- Partial and missing skills
- Which skill to learn first
- A relevant portfolio project
- Evidence to add to the CV
- Interview preparation steps

## Recruiter guidance

Recruiter guidance is shown only in the recruiter’s Candidate Applications area after clicking **Review Details**.

The recommendation is one of:

- **Select** — strong evidence and a high verified fit
- **Shortlist** — moderate fit that needs further assessment
- **Reject** — insufficient verified fit for the selected job

The professional review also provides:

- Evidence-based rationale
- Verified strengths
- Missing or partial skill risks
- Experience fit
- Interview or practical-assessment focus

The recruiter can then independently choose **Select**, **Shortlist**, or **Reject**. The AI does not automatically change an application’s status.

## Individual analysis for every job

An analysis belongs to a specific candidate-job application. When a candidate applies for another job, the system sends the new job’s requirements to the backend and generates a separate result.

Each saved application contains:

- Candidate snapshot at submission time
- Selected job ID and title
- Required skills and experience
- Match and mismatch scores
- Matched, partial, and missing skills
- Per-skill score breakdown
- Candidate guidance
- Recruiter guidance
- Application status

This prevents one job’s analysis from being incorrectly reused for another job.

## Local fallback analysis

If the Gemini API key is missing, the Gemini service is unavailable, or a Gemini request fails, the backend uses a deterministic local fallback.

The fallback:

- Searches for required skills in the candidate text.
- Calculates the same skill and experience weighting.
- Produces matched and missing skill lists.
- Generates basic candidate and recruiter guidance.

This keeps the demonstration usable without Gemini, but the explanation quality is less detailed.

## Multi-source skills matrix

The matrix is built from technical skills explicitly saved on the candidate profile. Each row can
show evidence from CV, experience, projects, GitHub, portfolio, and LinkedIn. Portfolio and
LinkedIn links are source availability indicators, not proof that every skill appears in the
linked content. GitHub rows can include repository-level findings and drill-down evidence.

The interface initially displays 32 rows and offers `See more` for the remaining saved skills.

## Privacy and fairness controls

The AI prompt explicitly avoids using protected personal characteristics for hiring guidance. Recruiters should review only job-related evidence such as skills, experience, and demonstrated work.

For a production system:

- Obtain candidate consent before processing CV data.
- Encrypt stored CVs and personal information.
- Restrict recruiter access by organization and job ownership.
- Audit AI recommendations and recruiter decisions.
- Test outcomes for bias and disparate impact.
- Provide a human appeal and correction process.
- Never allow the AI to make an unsupervised final employment decision.

## API endpoints used by the AI flow

### `POST /api/import-cv`

Accepts a CV file and returns extracted text and the original filename.

### `POST /api/extract-skills`

Accepts candidate text and returns normalized professional skills.

### `POST /api/analyze-cv`

Accepts job requirements and candidate information, calls Gemini when available, reconciles the result, and returns the complete analysis.

Interactive API documentation is available while the backend is running at:

http://127.0.0.1:8000/docs

## Important limitations

- CV text may be incomplete or ambiguous.
- Scanned PDFs require OCR, which is not currently included.
- Skill keyword evidence does not prove practical competence.
- AI explanations may still contain errors and require human verification.
- The browser stores only an opaque session token; application and evidence data are stored in MongoDB.
- LinkedIn content and identity are not independently verified without an official LinkedIn API integration.
- Match scores are decision-support indicators, not objective measures of a person’s overall ability or potential.

## Related documentation

- `RUN_GUIDE.md` — demo accounts, installation, startup, and troubleshooting
- `TECHNOLOGY_GUIDE.md` — technologies used and why they were selected
- `README.md` — short project overview
