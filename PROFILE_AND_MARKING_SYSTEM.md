# TalentVerifyAI Profile Management and Candidate Marking System

## 1. Purpose

TalentVerifyAI maintains a structured, evidence-aware candidate profile and evaluates that profile against a specific job. It does not treat a candidate profile as one unstructured block of text, and it does not calculate an application score from skills alone.

The application-time score answers this question:

> How well does the candidate's available, job-related evidence match the requirements of this particular vacancy?

The score is not a generic CV-quality score. A candidate may receive different marks for different jobs because the required skills, experience, education, languages, domain and credentials differ.

## 2. Main System Components

The implementation consists of:

- React frontend screens for profile management, job matching, application review and recruiter assessment.
- FastAPI endpoints for authentication, profiles, evidence collection, jobs and applications.
- MongoDB collections for canonical profile records, evidence snapshots and immutable evaluation history.
- Gemini-based evaluation when a configured model is available.
- A deterministic nine-category fallback when Gemini is missing, unavailable or returns an invalid result.

Primary implementation files:

- `backend/main.py`: API endpoints and application workflow.
- `backend/domain.py`: validated domain records, legacy recruitment-stage weights and persistence helpers.
- `backend/services/candidate_service.py`: complete candidate-profile assembly.
- `backend/services/enterprise_job_evaluation_service.py`: current job-specific 100-mark evaluation.
- `backend/github_evidence.py` and `backend/services/github_service.py`: GitHub collection and analysis.
- `backend/assessment_routes.py`: structured profile records, evidence matrix, evaluation history and later assessment stages.
- `frontend/src/components/ProfilePage.jsx`: candidate profile and evidence-management interface.
- `frontend/src/components/CandidateDashboard.jsx`: job-match preview, application submission and score explanation.
- `frontend/src/components/RecruiterDashboard.jsx`: recruiter application review and assessment controls.

## 3. Candidate Profile Lifecycle

### 3.1 Account profile

Basic account and display fields are kept in `users`. Candidate fields can include:

- Name and email
- Phone and location
- Professional headline and biography
- Stated total experience
- Technical-skill text
- Soft-skill text
- LinkedIn, GitHub and portfolio URLs
- CV filename and import time
- Availability, notice period, preferred roles and work preference
- Profile-photo location and recruiter-visibility preference

Passwords are stored as hashes. API responses remove password hashes. MongoDB identifiers are recursively sanitized before JSON responses, including nested evidence objects.

### 3.2 Canonical profile

Manual candidate edits are synchronized into `candidate_profiles` and the backward-compatible `candidates` collection. The canonical structure contains:

- `personal_info`
- `social_links`
- `career_preferences`
- `skills_summary`
- Top-level normalized technical and soft-skill arrays
- Created and updated timestamps

The candidate ID/user ID links this profile to every related record.
### 3.3 Structured profile sections

Information that needs individual evidence, editing and deduplication is stored in separate collections:

| Collection | Information retained |
|---|---|
| `candidate_skills` | Skill name, normalized name, technical/soft kind, source, evidence, confidence and timestamps |
| `candidate_experience` | Employer, position, dates, duration, responsibilities, technologies, achievements, employment type and location |
| `candidate_projects` | Name, description, candidate contribution, technologies, project type, achievements, GitHub URL and demo URL |
| `candidate_education` | Qualification/degree, field, institution, years, grade and final-year project |
| `candidate_certifications` | Name, issuer, dates, credential ID and credential URL |
| `candidate_languages` | Language, overall level, speaking, reading, writing and evidence |

The structured-profile API deduplicates display records by their meaningful identity fields while preserving their source list.

### 3.4 Manual profile updates

When a candidate saves profile changes:

1. Allowed fields are filtered at the API boundary.
2. Portfolio URLs are validated as HTTP/HTTPS URLs.
3. Technical and soft skills are normalized and combined without case-insensitive duplicates.
4. `users`, `candidate_profiles` and `candidates` are synchronized.
5. Individual skill records are upserted into `candidate_skills` with `candidate_manual` as their source.
6. The update is timestamped.

A manually entered skill is a claim. It can contribute to suitability when relevant, but it has lower evidence confidence than independently demonstrated use.

## 4. CV Import and Extraction

Candidates may upload PDF, DOCX or TXT files up to the configured frontend limit. The backend:

1. Extracts text from the document.
2. Creates a record in `cv_documents` with file metadata and parsing status.
3. Uses Gemini, when available, to convert the document into the validated `CvExtraction` structure.
4. Persists extracted personal information, technical skills, soft skills, experience, projects, education, certifications, languages and social links into their corresponding candidate collections.
5. Records source, confidence and evidence instead of treating AI output as verified truth.
6. Retains parsing status, errors, timestamps and recent extraction metadata for audit/history use.

Gemini does not write directly to MongoDB. Its output is validated and then saved through application-controlled persistence logic.

## 5. External and Public Evidence

### 5.1 GitHub

GitHub verification uses the GitHub API and stores:

- Canonical username and profile URL
- Public repository metadata
- Detected languages and technologies
- Repository quality indicators
- CV-to-GitHub consistency information
- Verification time and API status
- An immutable snapshot ID

`candidate_github` is the latest pointer/current view. `github_evidence_snapshots` preserves history. Verified GitHub skill findings can also be represented in `candidate_skills` with an API evidence source.

GitHub percentages and language percentages are supporting signals. They are not copied directly into final candidate marks.

### 5.2 Portfolio link evidence

Portfolio URLs are validated as HTTP/HTTPS links and stored with the candidate profile. The
multi-source matrix exposes a supplied portfolio link as an available evidence source for saved
technical skills. The current implementation does not fetch or scan portfolio page content, so a
portfolio link alone does not prove a skill.

### 5.3 LinkedIn public URL

The public URL validator accepts LinkedIn profile and post URLs, including versions copied without a URL scheme. It canonicalizes accepted links to an HTTPS `www.linkedin.com` form.

Public URL validation proves only that the URL shape is acceptable. It does not prove:

- Account ownership
- Identity
- Employment
- Education
- Technical or soft skills
- Certifications

### 5.4 LinkedIn URL verification

The candidate can verify a LinkedIn profile or post URL through
`POST /api/candidates/me/linkedin/verify`. Accepted paths include `/in/`, `/posts/`, and
`/feed/update/`. The backend validates the LinkedIn host and URL shape, stores the URL and a
verification timestamp, and returns `verified_url` status.

This is URL verification only. It does not verify account ownership, identity, employment,
skills, certifications, or LinkedIn post content. No LinkedIn OAuth integration is currently
included.

## 6. Multi-Source Skill Evidence

The skill matrix begins with skills explicitly saved on the candidate profile. Evidence sources may confirm an existing row but do not silently create unrelated profile skills.

For each profile technical skill, the system checks:

- CV/manual skill records
- Technologies in work-experience entries
- Technologies in project entries
- Verified GitHub skill evidence
- Portfolio URL availability as a link only, not as skill proof
- LinkedIn URL availability and URL-verification status, not as skill proof

Evidence from several independent sources increases confidence. The same claim appearing repeatedly is not supposed to generate duplicate marks.

## 7. Job Definition

A job can contain:

- Title, company, location and employment type
- Required experience
- Skill list
- Full job description
- Structured requirements
- Mandatory/must-have requirements
- Recommendation bands
- Versioned recruitment-stage weights

Recruiter updates increment requirement/weight versions where applicable. Applications are evaluated against the job that was selected, not against a generic role.

## 8. Evaluation Input Assembly

The authenticated preview endpoint and authoritative application endpoint assemble candidate data from MongoDB through `CandidateService` and direct evidence lookups. The evaluation input contains:

- Canonical personal/professional profile
- Technical and soft skills
- Programming and human languages
- Structured work history
- Structured projects
- Education
- Certifications
- Recent CV extraction records
- Latest verified GitHub snapshot
- Candidate portfolio and LinkedIn profile links, including LinkedIn URL verification metadata
- Evidence-source metadata and confidence where stored

Photo, gender, date of birth, marital status and similar irrelevant/protected fields are removed before evaluation.

## 9. When Evaluation Runs

### 9.1 Preview

`POST /api/jobs/{job_id}/candidate-evaluation` loads the current database profile and generates a preview. The preview uses the same enterprise evaluation engine as application submission.

### 9.2 Application submission

`POST /api/applications` recalculates the score authoritatively. The backend does not trust a score submitted by the browser. It then stores:

- Final job-match score
- All category marks and reasons
- Evidence confidence
- Match level
- Recommendation
- Mandatory-requirement results
- Skill-level analysis
- Strengths, concerns and gaps
- Evidence snapshot references
- Evaluation provider/model/version
- Application and evaluation timestamps

Only one active record is allowed for the same candidate/job pair by a compound unique index.

### 9.3 Re-evaluation

The re-evaluation endpoint reloads the latest database profile and evidence. It creates a new `ai_evaluations` version with a pointer to the previous evaluation instead of overwriting history. The application receives the latest score for display.

Older applications retain their older structure until they are re-evaluated.

## 10. Current 100-Point Job-Match Marking Model

| Category | Maximum | What is evaluated |
|---|---:|---|
| Technical Skills | 30 | Required and preferred job technologies, related tools/frameworks and strength of supporting evidence |
| Relevant Experience | 20 | Relevant duration, roles, responsibilities, seniority, ownership, production exposure and domain relevance |
| Projects | 15 | Job relevance, technologies, complexity, contribution, architecture, outcomes and demonstrable evidence |
| GitHub / Technical Evidence | 10 | Relevant repositories, languages, frameworks, structure, tests, documentation, activity and code evidence |
| Education | 8 | Required level, field relevance, equivalent professional background and related training |
| Soft Skills | 7 | Job-required communication, teamwork, leadership, ownership, problem solving, adaptability and similar evidence |
| Languages | 4 | Only human-language and communication requirements relevant to the job |
| Professional Alignment | 3 | Headline, specialization, career direction and coherent alignment with the target role |
| Certifications | 3 | Only job-relevant certificates and additional qualifications |
| **Total** | **100** | Sum of all nine awarded category marks |

The backend clamps every category to its maximum and recalculates the total from the normalized categories. This prevents an AI response from exceeding 100 or producing a total inconsistent with the breakdown.

### 10.1 Mark explanation

Every category stores:

- Awarded score
- Maximum score
- Reason
- Evidence list when supplied

The frontend's **How was this calculated?** control displays:

- `awarded / maximum × 100`
- The category's contribution to the 100-point total
- The job-relevance assessment reason
- Overall evidence confidence
- Recorded evidence details

### 10.2 Match levels

| Score | Match level |
|---:|---|
| 90–100 | Exceptional Match |
| 80–89.9 | Strong Match |
| 70–79.9 | Good Match |
| 60–69.9 | Moderate Match |
| 50–59.9 | Weak/Borderline Match |
| Below 50 | Low Match |

## 11. AI Evaluation Path

When Gemini is configured, the enterprise prompt instructs the model to:

1. Analyze the job before the candidate.
2. Classify requirements by importance.
3. Evaluate only supplied evidence.
4. Prefer verified/demonstrated sources over unsupported keywords.
5. Score all nine categories.
6. Return mandatory checks and skill-level analysis.
7. Keep suitability and evidence confidence separate.
8. Avoid double-counting.
9. Avoid protected characteristics.
10. Return strict JSON.

The backend then normalizes the result. Missing/invalid category values become safe values, marks are clamped, the category total is recomputed, evidence confidence is constrained to 0–100 and invalid recommendation output falls back to deterministic output.

## 12. Deterministic Fallback Path

If Gemini is not configured, times out, fails or returns unusable output, application processing continues with a deterministic evaluator. It uses the same nine category maxima and considers:

- Required skill matches against normalized candidate skills
- Recorded experience duration against required years
- Project technology overlap
- Verified GitHub technology overlap
- Education relevance
- Soft skills appearing in job requirements
- Human languages appearing in job requirements
- Headline/summary alignment with the role title
- Relevant certification terms
- Structured mandatory requirements

The stored provider value indicates `gemini`, `deterministic` or `deterministic_fallback`, so the route used is auditable.

## 13. Evidence Confidence

Evidence confidence is 0–100 and is not included in candidate marks.

Examples:

- Candidate score: 82/100
- Evidence confidence: 61%

This means available information suggests a strong job match, but some claims still require confirmation.

Confidence considers independent sources, detailed experience/projects, verified technical evidence, credentials, missing information and inconsistency. `API unavailable`, `not verified`, `Plus tier required` and `information not provided by API` affect certainty, not automatic suitability failure.

## 14. Mandatory Requirements

Mandatory requirements are evaluated separately from the 100-point score. Allowed statuses are:

- `PASS`: sufficient supporting evidence exists.
- `FAIL`: explicit evidence shows the requirement is not met.
- `NOT_VERIFIED`: required information is absent or currently unverifiable.
- `MANUAL_REVIEW_REQUIRED`: evidence is ambiguous, conflicting or needs human judgment.
- `NOT_APPLICABLE`: the requirement does not apply.

Missing information is not converted automatically to `FAIL`.

## 15. Skill-Level Analysis

Important job skills can contain:

- Skill name
- Importance (`MANDATORY`, `IMPORTANT`, `PREFERRED`, `OPTIONAL`)
- Candidate match (`STRONG_MATCH`, `MATCH`, `PARTIAL_MATCH`, `WEAK_MATCH`, `NO_EVIDENCE`)
- Evidence sources
- Evidence strength (`HIGH`, `MEDIUM`, `LOW`, `NONE`)
- Percentage
- Explanation

This analysis helps a recruiter distinguish a profile keyword from a skill demonstrated across work, projects, GitHub or portfolio evidence.

## 16. Recommendation

The enterprise output uses:

- `HIGHLY_RECOMMENDED`
- `RECOMMENDED`
- `CONSIDER`
- `MANUAL_REVIEW`
- `NOT_RECOMMENDED`

The recommendation includes a reason and must be considered decision support. It is not an autonomous hiring decision. Recruiters retain responsibility for review, interview, lawful eligibility checks and final decisions.

## 17. Recruitment Stages After Profile Evaluation

The codebase also contains a configurable staged recruitment framework with profile categories, technical assessment and structured interview weights. It supports:

- Technical-assessment records
- Structured interview dimensions
- Recruiter score overrides with reasons
- Final decisions
- Eligibility summaries
- Recommendation bands

These later controls must not be confused with the nine-category, 100-point application job-match score. The application score represents profile-to-job suitability before later human/assessment stages.

## 18. Data History and Auditability

The following preserve historical or audit data:

- `cv_documents`: CV import and parsing history
- `github_evidence_snapshots`: immutable GitHub scans
- `analysis_runs`: submitted evaluation-input and scoring audit data
- `ai_evaluations`: versioned application evaluations
- `interviews`: structured interview versions
- `technical_assessments`: technical-test results
- `score_overrides`: recruiter changes with original values and reasons
- `final_decisions`: final recruitment decisions
- `audit_logs`: actor/action/entity/time records

Historical evidence retains timestamps so a reviewer can judge freshness. Re-evaluation uses current data without erasing earlier evaluation records.

## 19. Main MongoDB Collections

| Collection | Responsibility |
|---|---|
| `users` | Authentication identity and current UI profile fields |
| `sessions` | Login session tokens |
| `candidate_profiles` | Canonical candidate intelligence profile |
| `candidates` | Backward-compatible candidate profile view |
| `recruiters` | Recruiter organization/profile data |
| `candidate_skills` | Source-aware normalized skills |
| `candidate_experience` | Work-history records |
| `candidate_projects` | Project records |
| `candidate_education` | Education records |
| `candidate_certifications` | Certification records |
| `candidate_languages` | Human/programming language records |
| `cv_documents` | CV files, parsing metadata and extraction history |
| `candidate_github` | Latest GitHub evidence pointer/view |
| `github_evidence_snapshots` | Immutable GitHub history |
| `jobs` | Vacancies and versioned evaluation configuration |
| `job_requirements` | Structured job requirements |
| `applications` | Current application status and latest evaluation result |
| `analysis_runs` | Evaluation-run input/output audit snapshots |
| `ai_evaluations` | Versioned application evaluation history |
| `interviews` | Structured interviews |
| `technical_assessments` | Technical assessments |
| `score_overrides` | Recruiter overrides and reasons |
| `final_decisions` | Final hiring-stage decisions |
| `audit_logs` | Traceable system actions |

## 20. Security and Fairness Controls

- Candidate/recruiter routes enforce role and ownership checks.
- Recruiters can access only candidates connected to their jobs/applications.
- Client secrets remain in backend environment variables.
- LinkedIn URL verification stores no access token and does not scrape LinkedIn content.
- Password hashes and internal MongoDB IDs are removed from API responses.
- Candidate photographs are shown to recruiters only when the candidate explicitly enables visibility.
- Protected personal characteristics are excluded from evaluation input and prohibited by the evaluation prompt.
- Missing information is not automatically treated as failure.
- External paid service unavailability is not treated as lack of candidate ability.

## 21. Important Limitations

- A manually entered claim is not independent proof.
- CV extraction can be inaccurate and carries source/confidence metadata.
- Public LinkedIn URL validation is not identity or professional-evidence verification.
- LinkedIn post content, identity, skills, soft skills and certifications are not verified by the current URL-only implementation.
- Portfolio link availability confirms only that a candidate supplied a link, not authorship or proficiency.
- GitHub activity is relevant evidence for some technical roles but should not disadvantage candidates for non-coding roles.
- AI reasoning can vary; normalized totals and deterministic fallback improve consistency but do not replace recruiter judgment.
- Existing applications created under an older schema require re-evaluation to receive the current nine-category breakdown.

## 22. Configuration

Core backend settings are documented in `backend/.env.example`, including:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `MONGODB_URI`
- `MONGODB_DB`
- `CORS_ORIGINS`
- `FRONTEND_URL`

Real secrets belong only in `backend/.env`. They must not be committed, placed in `.env.example`, sent to the frontend or shared in documentation/screenshots.

## 23. End-to-End Example

1. Candidate creates an account.
2. Candidate completes profile fields and structured sections.
3. Candidate imports a CV; extracted records are validated and saved with source metadata.
4. Candidate optionally verifies GitHub and LinkedIn, and saves a portfolio link.
5. Recruiter publishes a job with requirements and must-haves.
6. Candidate selects the job and requests an evaluation preview.
7. Backend reloads the complete database profile and evidence.
8. Enterprise evaluator produces nine category marks, evidence confidence, mandatory checks, skill analysis, gaps and recommendation.
9. Candidate confirms the application.
10. Backend recalculates authoritatively and stores the application, analysis run and versioned AI evaluation.
11. Candidate reviews marks through category-level calculation controls.
12. Recruiter reviews evidence, performs assessments/interviews and records a human-controlled final decision.
13. When profile/evidence changes, an authorized re-evaluation creates a new version without deleting the old one.

## 24. Scoring Integrity Rules

The implemented evaluation policy is based on these invariants:

1. Score against the applied job, not generic CV quality.
2. Use all relevant stored profile sections.
3. Required evidence carries greater importance than optional keywords.
4. Do not fabricate missing information.
5. Do not infer a missing skill.
6. Do not convert missing/unavailable verification into failure.
7. Do not treat API connection itself as evidence.
8. Do not copy GitHub percentages directly into marks.
9. Do not double-count the same underlying evidence.
10. Explain every category mark.
11. Keep evidence confidence separate from suitability.
12. Ensure category marks sum to the candidate score.
13. Never exceed 100.
14. Require human review for uncertain or high-impact hiring decisions.

