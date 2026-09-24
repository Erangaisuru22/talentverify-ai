"""Deterministic enterprise hiring stages. AI supplies evidence; this module owns marks."""
from copy import deepcopy
from datetime import datetime, timezone

from domain import DEFAULT_WEIGHTS, PROFILE_CATEGORIES, ScoreWeights, normalized

ELIGIBILITY_STATUSES = {"pass", "fail", "not_verified", "manual_review_required", "not_applicable"}
DECISIONS = {"Shortlist", "Technical Interview", "Final Interview", "Offer", "Hold", "Reject"}
DEFAULT_BANDS = [
    {"minimum": 85, "label": "Strong Match"}, {"minimum": 70, "label": "Good Match"},
    {"minimum": 55, "label": "Moderate Match"}, {"minimum": 0, "label": "Weak Match"},
]
INTERVIEW_DIMENSIONS = ("communication", "problem_solving", "ownership", "teamwork", "adaptability",
                        "feedback_handling", "critical_thinking", "leadership")

def validate_bands(value):
    if isinstance(value, dict):
        strong = float(value.get("strong_min", 85))
        rec = float(value.get("recommended_min", 70))
        mod = float(value.get("moderate_min", 55))
        bands = [
            {"minimum": strong, "label": "Strong Match"},
            {"minimum": rec, "label": "Good Match"},
            {"minimum": mod, "label": "Moderate Match"},
            {"minimum": 0, "label": "Weak Match"},
        ]
    else:
        bands = deepcopy(value or DEFAULT_BANDS)
    if not bands or any(not isinstance(x, dict) or not isinstance(x.get("minimum"), (int, float)) or not x.get("label") for x in bands):
        bands = deepcopy(DEFAULT_BANDS)
    minimums = [float(x["minimum"]) for x in bands]
    if any(x < 0 or x > 100 for x in minimums) or len(set(minimums)) != len(minimums):
        bands = deepcopy(DEFAULT_BANDS)
    return sorted(bands, key=lambda x: x["minimum"], reverse=True)

def validate_requirements(value):
    result = []
    for raw in value or []:
        requirement = str(raw.get("requirement", "")).strip()
        kind = str(raw.get("type", "")).strip().lower()
        if not requirement or kind not in {"skill", "experience", "work_authorization", "education", "language", "certification", "other"}:
            raise ValueError("Each must-have needs a requirement and valid type.")
        result.append({**raw, "requirement": requirement, "type": kind, "mandatory": bool(raw.get("mandatory", True))})
    return result

def _candidate_values(candidate, key):
    return candidate.get(key) or []

def evaluate_eligibility(candidate, requirements):
    skills = {normalized(x.get("skill")) for x in _candidate_values(candidate, "skills")}
    verified_skills = {normalized(x.get("skill")) for x in _candidate_values(candidate, "skills")
                       if x.get("verified_by_recruiter") or x.get("source") in {"recruiter_manual", "github_verified"}}
    experience_skills = {normalized(t) for x in _candidate_values(candidate, "experience") for t in x.get("technologies", [])}
    project_skills = {normalized(t) for x in _candidate_values(candidate, "projects") for t in x.get("technologies", [])}
    languages = {normalized(x.get("language")) for x in _candidate_values(candidate, "languages")}
    certifications = {normalized(x.get("name")) for x in _candidate_values(candidate, "certifications")}
    education = " ".join(normalized(x.get("qualification") or x.get("degree")) for x in _candidate_values(candidate, "education"))
    experience_months = sum(max(0, int(x.get("duration_months") or 0)) for x in _candidate_values(candidate, "experience"))
    checks = []
    for raw_req in requirements or []:
        req = raw_req if isinstance(raw_req, dict) else {"requirement": str(raw_req)}
        kind = str(req.get("type") or req.get("category") or "skill").strip().lower()
        if kind not in {"skill", "experience", "work_authorization", "education", "language", "certification", "other"}:
            kind = "skill"
        req_text = str(req.get("requirement") or "")
        target = normalized(req_text)
        status, evidence = "not_verified", "No verified candidate evidence found"
        if kind == "skill" and target in (verified_skills | experience_skills | project_skills):
            status, evidence = "pass", f"Verified professional or project evidence found: {req['requirement']}"
        elif kind == "skill" and target in skills:
            status, evidence = "not_verified", f"{req['requirement']} appears in the skills list without verified usage evidence"
        elif kind == "language" and target in languages:
            status, evidence = "pass", f"Language evidence found: {req['requirement']}"
        elif kind == "certification" and target in certifications:
            status, evidence = "pass", f"Certification evidence found: {req['requirement']}"
        elif kind == "education" and target and target in education:
            status, evidence = "pass", f"Education evidence found: {req['requirement']}"
        elif kind == "experience":
            minimum = float(req.get("minimum_years", req.get("value", 0)) or 0)
            years = experience_months / 12
            status = "pass" if years >= minimum else ("fail" if experience_months else "not_verified")
            evidence = f"Calculated experience: {experience_months // 12} years {experience_months % 12} months" if experience_months else "Experience dates are not verified"
        elif kind == "work_authorization":
            value = candidate.get("work_authorization")
            status = "pass" if value is True else "fail" if value is False else "not_verified"
            evidence = "Work authorization confirmed" if value is True else "Work authorization not confirmed"
        checks.append({**req, "status": status, "evidence": evidence,
                       "message": "Does not meet mandatory requirement" if req.get("mandatory") and status == "fail" else None})
    mandatory = [x for x in checks if x.get("mandatory") and x["status"] != "not_applicable"]
    if any(x["status"] == "fail" for x in mandatory): status = "fail"
    elif any(x["status"] in {"not_verified", "manual_review_required"} for x in mandatory): status = "manual_review_required"
    else: status = "pass"
    return {"status": status, "checks": checks, "summary": {"met": sum(x["status"] == "pass" for x in mandatory),
            "total": len(mandatory), "requires_verification": sum(x["status"] in {"not_verified", "manual_review_required"} for x in mandatory)}}

def profile_totals(scores, weights):
    maximum = round(sum(getattr(weights, key) for key in PROFILE_CATEGORIES), 2)
    score = round(sum(float(scores.get(key, {}).get("weighted_score", 0)) for key in PROFILE_CATEGORIES), 2)
    return {"score": score, "maximum": maximum, "normalized_percentage": round(score / maximum * 100, 2) if maximum else 0}

def build_profile_scores(breakdown, weights):
    """Adapt the existing matching engine's evidence into enterprise category percentages."""
    aliases = {"technical_skills": "skills", "experience": "experience", "projects": "projects",
               "education": "education", "certifications": "certifications", "github_evidence": "github"}
    result = {}
    for category in PROFILE_CATEGORIES:
        raw = breakdown.get(aliases.get(category, category), {})
        if category == "job_relevance":
            inputs = [breakdown.get(x, {}) for x in ("skills", "experience", "projects")]
            ratios = [float(x.get("score", 0)) / float(x.get("max_score", 1)) for x in inputs if float(x.get("max_score", 0)) > 0]
            percentage = sum(ratios) / len(ratios) * 100 if ratios else 0
            reason, evidence, source = "Overall recent-work, responsibility, and project alignment.", [], ["job_match_engine"]
        else:
            max_score = float(raw.get("max_score", raw.get("maximum_score", 0)) or 0)
            percentage = float(raw.get("match_percentage", (float(raw.get("score", 0)) / max_score * 100 if max_score else 0)))
            reason = str(raw.get("reason") or "No validated evidence supplied")
            evidence = [str(x) for x in raw.get("evidence", []) if x]
            source = ["verified_github_api"] if category == "github_evidence" and evidence else ["candidate_profile"]
        maximum = getattr(weights, category)
        result[category] = {"match_percentage": round(max(0, min(100, percentage)), 2),
            "weighted_score": round(max(0, min(100, percentage)) / 100 * maximum, 2), "maximum_score": maximum,
            "reason": reason, "evidence": evidence, "missing_evidence": [] if evidence else ["No verified evidence available"],
            "confidence": .9 if evidence else .45, "source": source}
    return result

def normalized_stage(raw_score, maximum):
    raw = float(raw_score)
    if raw < 0 or raw > 100: raise ValueError("Raw score must be from 0 to 100.")
    return {"status": "completed", "raw_score": raw, "normalized_percentage": raw,
            "weighted_score": round(raw / 100 * maximum, 2), "max_score": maximum}

def score_interview(scorecard, maximum):
    present = []
    clean = {}
    for key in INTERVIEW_DIMENSIONS:
        if key not in scorecard: continue
        item = scorecard[key]; score = float(item.get("score", 0)); max_score = float(item.get("max_score", 5))
        if max_score <= 0 or score < 1 or score > max_score: raise ValueError(f"{key} must use an anchored score from 1 to {max_score:g}.")
        clean[key] = {**item, "score": score, "max_score": max_score}; present.append(score / max_score)
    if not present: raise ValueError("At least one interview dimension is required.")
    percentage = round(sum(present) / len(present) * 100, 2)
    return {"status": "completed", "scorecard": clean, "normalized_percentage": percentage,
            "weighted_score": round(percentage / 100 * maximum, 2), "max_score": maximum}

def recommendation(score, bands):
    return next((x["label"] for x in validate_bands(bands) if score >= float(x["minimum"])), "Weak Match")

def pending_decision():
    return {"status": "pending", "decision": None, "decision_by": None, "reason": None, "decided_at": None}
