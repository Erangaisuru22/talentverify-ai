"""Evidence-based candidate evaluation helpers."""
SCORING_VERSION = "2.1"
import asyncio, json, os, re
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SCORE_MAXIMUMS = {"technical_skills": 25, "soft_skills": 5, "experience": 20, "projects": 20, "education": 10, "certifications": 5, "github": 10, "job_relevance": 5}
DEFAULT_JOB_WEIGHTS = {"technical_skills": 20, "soft_skills": 3, "experience": 15, "projects": 15, "education": 10, "certifications": 5, "github": 10, "job_relevance": 10, "interview": 12}
PROTECTED_TERMS = {"age", "gender", "sex", "race", "religion", "nationality", "marital status", "disability", "photograph", "photo", "appearance"}

def _number(value, default=0.0):
    try: return float(value)
    except (TypeError, ValueError): return float(default)

def _clamp(value, maximum): return round(max(0.0, min(_number(value), float(maximum))), 1)

def _strings(value):
    if not isinstance(value, list): return []
    output, seen = [], set()
    for item in value:
        text, key = str(item).strip(), str(item).strip().casefold()
        if text and key not in seen: seen.add(key); output.append(text[:500])
    return output

def _safe_evidence(value):
    return [item for item in _strings(value) if not any(term in item.casefold() for term in PROTECTED_TERMS)]

def extract_github_urls(text):
    urls = re.findall(r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?", text or "", re.I)
    return _strings([url.rstrip("/.,;)") for url in urls])

def _github_request(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "TalentVerify/2.0"}
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token: headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def _fetch_github(urls):
    repositories, errors = [], []
    for source_url in urls[:5]:
        parts = [part for part in urlparse(source_url).path.split("/") if part]
        if not parts: errors.append("Invalid GitHub URL"); continue
        try:
            items = [_github_request(f"https://api.github.com/repos/{parts[0]}/{parts[1]}")] if len(parts) >= 2 else _github_request(f"https://api.github.com/users/{parts[0]}/repos?sort=updated&per_page=10")
            for item in items[:10]:
                repositories.append({"name": item.get("name", ""), "url": item.get("html_url", ""), "description": item.get("description") or "", "language": item.get("language") or "", "topics": item.get("topics") or [], "stars": int(item.get("stargazers_count") or 0), "fork": bool(item.get("fork")), "updated_at": item.get("updated_at", ""), "source_url": source_url})
        except HTTPError as exc: errors.append(f"GitHub returned HTTP {exc.code}")
        except (URLError, TimeoutError, json.JSONDecodeError) as exc: errors.append(str(exc)[:160])
    status = "verified" if repositories else "unavailable" if errors else "invalid"
    return {"urls": urls, "repositories": repositories, "verification_status": status, "errors": errors}

async def fetch_github_evidence(cv_text, supplied_urls=None):
    urls = _strings((supplied_urls or []) + extract_github_urls(cv_text))
    if not urls: return {"urls": [], "repositories": [], "verification_status": "not_provided", "errors": []}
    return await asyncio.to_thread(_fetch_github, urls)

def _score_entry(raw, key, default_score, default_reason, default_evidence):
    maximum = SCORE_MAXIMUMS[key]
    candidate = (raw.get("scores") or {}).get(key, {}) if isinstance(raw, dict) else {}
    if isinstance(candidate, (int, float)): awarded, reason, evidence = candidate, default_reason, default_evidence
    elif isinstance(candidate, dict):
        awarded = candidate.get("awarded", candidate.get("score", default_score)); reason = str(candidate.get("reason") or default_reason).strip(); evidence = candidate.get("evidence", default_evidence)
    else: awarded, reason, evidence = default_score, default_reason, default_evidence
    return {"awarded": _clamp(awarded, maximum), "maximum": maximum, "reason": reason[:1000] or default_reason, "evidence": _safe_evidence(evidence)[:20]}

def validate_job_weights(value):
    weights = value if isinstance(value, dict) else DEFAULT_JOB_WEIGHTS
    cleaned = {key: _clamp(weights.get(key, DEFAULT_JOB_WEIGHTS[key]), 100) for key in DEFAULT_JOB_WEIGHTS}
    if abs(sum(cleaned.values()) - 100) > 0.01:
        raise ValueError("Job evaluation weights must total exactly 100.")
    return cleaned

def apply_job_weights(evaluation, value):
    weights = validate_job_weights(value)
    weighted_scores = {}
    for key, raw in evaluation["scores"].items():
        weight = weights[key]
        contribution = round((raw["awarded"] / raw["maximum"]) * weight, 1) if raw["maximum"] else 0
        weighted_scores[key] = {**raw, "raw_awarded": raw["awarded"], "raw_maximum": raw["maximum"], "awarded": contribution, "maximum": weight}
    interview_weight = weights["interview"]
    weighted_scores["interview"] = {"awarded": 0, "maximum": interview_weight, "reason": "Interview assessment has not been completed.", "evidence": [], "raw_awarded": 0, "raw_maximum": 6}
    evaluation["scores"], evaluation["score_weights"] = weighted_scores, weights
    evaluation["score"] = evaluation["total_score"] = round(sum(item["awarded"] for item in weighted_scores.values()), 1)
    evaluation["score_breakdown"]["total"] = evaluation["total_score"]
    evaluation["score_breakdown"]["interview_score"] = 0
    evaluation["score_breakdown"]["interview_max"] = interview_weight
    return evaluation

def build_evaluation(raw, legacy, cv_text, job_title, job_skills, job_description, candidate_experience, required_experience, github):
    raw, legacy = (raw if isinstance(raw, dict) else {}), (legacy if isinstance(legacy, dict) else {})
    breakdown = legacy.get("score_breakdown") or {}
    old_skill_max = max(_number(breakdown.get("skill_max"), 100), 1)
    technical = round(_clamp(breakdown.get("skill_points", legacy.get("score", 0)), old_skill_max) / old_skill_max * 25, 1)
    profile_details = legacy.get("profile_details") or {}
    soft_skill_evidence = _strings(profile_details.get("soft_skills", []))
    soft_skill_score = min(len(soft_skill_evidence), 5)
    required_years, candidate_years = max(_number(required_experience), 0), max(_number(candidate_experience), 0)
    experience = round((min(candidate_years / required_years, 1) if required_years else (1 if candidate_years else 0)) * 20, 1)
    projects = raw.get("projects") if isinstance(raw.get("projects"), list) else []
    education = raw.get("education") if isinstance(raw.get("education"), list) else []
    certifications = raw.get("certifications") if isinstance(raw.get("certifications"), list) else []
    repos = github.get("repositories", [])
    required_count = len([item for item in str(job_skills).split(",") if item.strip()])
    matched_count = len(legacy.get("matched_skills", [])) + .5 * len(legacy.get("partial_skills", []))
    defaults = {
        "technical_skills": (technical, "Normalized from the existing required-skill matching logic.", [item.get("evidence", "") for item in legacy.get("skill_breakdown", []) if item.get("credit")]),
        "soft_skills": (soft_skill_score, "Based only on soft skills explicitly evidenced in the CV or candidate profile.", soft_skill_evidence),
        "experience": (experience, f"{candidate_years:g} years supplied against {required_years:g} years required.", [f"Candidate experience: {candidate_years:g} years", f"Required experience: {required_years:g} years"]),
        "projects": (min(len(projects) * 5, 20), "Based on explicitly extracted CV projects and their relevance.", [str(item.get("title") or item.get("name") or "CV project") for item in projects if isinstance(item, dict)]),
        "education": (min(len(education) * 5, 10), "Based only on education explicitly stated in the CV.", [str(item.get("degree") or item.get("qualification") or "CV education") for item in education if isinstance(item, dict)]),
        "certifications": (min(len(certifications) * 2.5, 5), "Based only on certifications explicitly stated in the CV.", [str(item.get("name") or item) for item in certifications]),
        "github": (min(len(repos) * 2, 10), "Based on public repositories retrieved from CV-provided GitHub URLs." if repos else "No verifiable public GitHub evidence was available; this does not imply lack of technical ability.", [repo.get("url", "") for repo in repos]),
        "job_relevance": (round(min(matched_count / required_count, 1) * 5, 1) if required_count else 0, "Based on explicit alignment with the supplied job requirements.", _strings(legacy.get("matched_skills", []))),
    }
    scores = {key: _score_entry(raw, key, *defaults[key]) for key in SCORE_MAXIMUMS}
    scores["technical_skills"]["awarded"], scores["soft_skills"]["awarded"], scores["experience"]["awarded"] = technical, soft_skill_score, experience
    if github.get("verification_status") != "verified": scores["github"]["awarded"] = 0
    total = round(sum(item["awarded"] for item in scores.values()), 1)
    extended = {"technical_skill_score": technical, "technical_skill_max": 25, "soft_skill_score": soft_skill_score, "soft_skill_max": 5, "experience_score": experience, "experience_max": 20, "project_score": scores["projects"]["awarded"], "project_max": 20, "education_score": scores["education"]["awarded"], "education_max": 10, "certification_score": scores["certifications"]["awarded"], "certification_max": 5, "github_score": scores["github"]["awarded"], "github_max": 10, "job_relevance_score": scores["job_relevance"]["awarded"], "job_relevance_max": 5, "total": total, "total_max": 100}
    return {**legacy, "score": total, "total_score": total, "scores": scores, "projects": projects, "education": education, "certifications": certifications, "github": github, "matched_skills": _strings(raw.get("matched_skills") or legacy.get("matched_skills", [])), "partially_matched_skills": raw.get("partially_matched_skills") or legacy.get("partial_skills", []), "missing_skills": _strings(raw.get("missing_skills") or legacy.get("missing_skills", [])), "strengths": _strings(raw.get("strengths", [])), "areas_to_improve": _strings(raw.get("areas_to_improve", [])), "overall_summary": str(raw.get("overall_summary") or "Evidence-based evaluation for recruiter review.")[:1500], "scoring_version": SCORING_VERSION, "ai_model": os.getenv("GEMINI_MODEL", "gemini-3.6-flash"), "evaluation_status": "completed", "evaluated_at": datetime.now(timezone.utc).isoformat(), "job_context": {"title": job_title, "skills": job_skills, "description": job_description}, "legacy_score": legacy.get("score", 0), "legacy_score_maximum": 100, "score_breakdown": {**breakdown, **extended}}
