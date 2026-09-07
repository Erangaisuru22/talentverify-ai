"""Job-specific, evidence-aware candidate evaluation used when an application is submitted."""

import json
import re
from typing import Any, Awaitable, Callable, Dict


CATEGORY_MAX = {
    "technical_skills": 30, "relevant_experience": 20, "projects": 15,
    "github_evidence": 10, "education": 8, "soft_skills": 7,
    "languages": 4, "professional_alignment": 3, "certifications": 3,
}

SYSTEM_PROMPT = """You are an enterprise-grade AI Candidate Evaluation Engine.
Evaluate the candidate specifically against the supplied JOB DESCRIPTION; never give a generic CV or profile-completeness score.
First classify job requirements as MANDATORY, IMPORTANT, PREFERRED, or OPTIONAL. Use all supplied profile evidence: technical and soft skills, detailed experience, projects, education, certifications, human languages, CV records, GitHub, portfolio, LinkedIn, and source metadata.
Evidence confidence is separate from suitability. GitHub API/repository evidence and demonstrable portfolio evidence are strongest; detailed experience/projects are strong; CV-extracted claims are moderate; unsupported manual keywords are low. Never award points merely because an external API or URL is connected. API unavailable, not_verified, Plus tier required, or missing API fields must not automatically lower suitability; represent uncertainty in evidence_confidence. Do not double-count evidence.
Use exactly these category maxima: technical_skills 30, relevant_experience 20, projects 15, github_evidence 10, education 8, soft_skills 7, languages 4, professional_alignment 3, certifications 3. Score job relevance, not quantity. If GitHub is irrelevant or unavailable, do not infer inability; explain uncertainty. The nine category scores must sum exactly to candidate_score and candidate_score must be 0..100.
Mandatory statuses are only PASS, FAIL, NOT_VERIFIED, MANUAL_REVIEW_REQUIRED, NOT_APPLICABLE. Missing information is NOT_VERIFIED, never automatically FAIL. Skill candidate_match is only STRONG_MATCH, MATCH, PARTIAL_MATCH, WEAK_MATCH, NO_EVIDENCE. Evidence strength is HIGH, MEDIUM, LOW, NONE.
Never use or infer gender, race, ethnicity, religion, sexuality, disability, marital status, age, appearance, or national origin. Never fabricate facts.
Return strict JSON only with: candidate_score, maximum_score=100, match_percentage, match_level, evidence_confidence, score_breakdown (all nine keys, each containing score,max,reason), mandatory_requirements, skill_analysis, strongest_matches, skill_gaps, experience_gaps, verification_gaps, candidate_strengths, concerns, recommendation {decision,reason}. Recommendation decision is one of HIGHLY_RECOMMENDED, RECOMMENDED, CONSIDER, MANUAL_REVIEW, NOT_RECOMMENDED."""


def _names(values, *fields):
    result = []
    for value in values or []:
        if isinstance(value, str): result.append(value)
        elif isinstance(value, dict):
            text = next((value.get(field) for field in fields if value.get(field)), None)
            if text: result.append(str(text))
    return result


def _terms(value):
    return {" ".join(x.casefold().replace("-", " ").split()) for x in value if str(x).strip()}


def _ratio(required, candidate):
    required, candidate = _terms(required), _terms(candidate)
    if not required: return 1.0, []
    matches = [req for req in required if any(req == item or (min(len(req), len(item)) >= 3 and (req in item or item in req)) for item in candidate)]
    return len(matches) / len(required), matches


def _score(maximum, ratio): return round(max(0.0, min(float(maximum), maximum * ratio)), 1)


def deterministic_evaluation(job, candidate):
    required = [x.strip() for x in str(job.get("skills") or "").split(",") if x.strip()]
    skill_records = candidate.get("skills") or []
    tech = list(candidate.get("technical_skills") or []) + list(candidate.get("programming_languages") or []) + [
        str(x.get("skill")) for x in skill_records if isinstance(x, dict) and x.get("skill") and x.get("kind", "technical") != "soft"]
    soft = list(candidate.get("soft_skills") or []) + [str(x.get("skill")) for x in skill_records if isinstance(x, dict) and x.get("skill") and x.get("kind") == "soft"]
    experiences, projects = candidate.get("experience") or [], candidate.get("projects") or []
    education, certifications = candidate.get("education") or [], candidate.get("certifications") or []
    languages = _names(candidate.get("human_languages") or candidate.get("languages"), "language", "name")
    tech_ratio, matched = _ratio(required, tech)
    project_ratio, project_matches = _ratio(required, [t for p in projects for t in p.get("technologies", [])])
    github = candidate.get("github") or candidate.get("github_profile") or {}
    github_ratio, github_matches = _ratio(required, github.get("detected_skills") or [])
    portfolio = candidate.get("portfolio_evidence") or {}
    portfolio_matches = _names(portfolio.get("matched_skills"), "skill")
    required_years = float(job.get("experience") or 0); candidate_years = float((candidate.get("personal_info") or {}).get("experience_years") or 0)
    if not candidate_years: candidate_years = sum(float(x.get("duration_months") or 0) for x in experiences) / 12
    exp_ratio = min(1.0, candidate_years / required_years) if required_years else (1.0 if experiences else 0.5)
    description = str(job.get("description") or "").casefold()
    soft_required = [s for s in soft if s.casefold() in description]
    soft_ratio = min(1.0, len(soft_required) / max(1, min(3, len(soft)))) if soft else 0
    language_matches = [lang for lang in languages if lang.casefold() in description]
    language_ratio = 1.0 if not any(word in description for word in ("language", "english", "sinhala", "tamil")) else min(1.0, len(language_matches))
    title_words = set(re.findall(r"[a-z0-9+#.]+", str(job.get("title") or "").casefold()))
    alignment_words = set(re.findall(r"[a-z0-9+#.]+", f"{(candidate.get('personal_info') or {}).get('headline', '')} {candidate.get('professional_summary', '')}".casefold()))
    alignment_ratio = len(title_words & alignment_words) / max(1, len(title_words))
    cert_relevant = [c for c in certifications if any(term in str(c).casefold() for term in required + list(title_words))]
    edu_text = " ".join(str(x) for x in education).casefold(); edu_relevance = 1.0 if education and any(x in edu_text for x in ("computer", "software", "engineering", "information technology")) else 0.5 if education else 0
    github_available = github.get("verification_status") in {"verified", "success"}
    breakdown = {
        "technical_skills": (_score(30, tech_ratio), f"Matched {len(matched)} of {len(required)} job technologies from candidate records."),
        "relevant_experience": (_score(20, exp_ratio), f"Evaluated {candidate_years:g} years and recorded work details against {required_years:g} required years."),
        "projects": (_score(15, project_ratio), f"Project technologies support {len(project_matches)} job requirements."),
        "github_evidence": (_score(10, github_ratio) if github_available else 0, "GitHub repository evidence supports relevant technologies." if github_matches else "No relevant verified GitHub evidence was available; this affects confidence, not other category marks."),
        "education": (_score(8, edu_relevance), "Education was evaluated for relevance to this job."),
        "soft_skills": (_score(7, soft_ratio), "Soft skills were credited only when relevant to the job description."),
        "languages": (_score(4, language_ratio), "Human-language evidence was evaluated only against communication requirements."),
        "professional_alignment": (_score(3, alignment_ratio), "Headline and professional summary were compared with the target role."),
        "certifications": (_score(3, min(1, len(cert_relevant))), "Only job-relevant certifications received credit."),
    }
    output_breakdown = {key: {"score": value[0], "max": CATEGORY_MAX[key], "reason": value[1]} for key, value in breakdown.items()}
    total = round(sum(x["score"] for x in output_breakdown.values()), 1)
    level = "Exceptional Match" if total >= 90 else "Strong Match" if total >= 80 else "Good Match" if total >= 70 else "Moderate Match" if total >= 60 else "Weak/Borderline Match" if total >= 50 else "Low Match"
    confidence_sources = sum(bool(x) for x in (experiences, projects, education, certifications, github_matches, portfolio_matches))
    confidence = min(95, 35 + confidence_sources * 10)
    skill_analysis = [{"skill": skill, "importance": "IMPORTANT", "candidate_match": "MATCH" if skill.casefold() in matched else "NO_EVIDENCE",
        "evidence_sources": [source for source, values in (("Profile/CV", tech), ("Projects", project_matches), ("GitHub", github_matches), ("Portfolio", portfolio_matches)) if any(skill.casefold() == str(x).casefold() for x in values)],
        "evidence_strength": "HIGH" if skill in github_matches or skill in project_matches else "MEDIUM" if skill.casefold() in matched else "NONE",
        "score_percentage": 100 if skill.casefold() in matched else 0, "explanation": "Evidence was cross-checked across available candidate sources."} for skill in required]
    mandatory = []
    all_candidate_text = json.dumps(candidate, default=str).casefold()
    for requirement in job.get("must_have_requirements") or []:
        label, kind = str(requirement.get("requirement") or ""), str(requirement.get("type") or "other")
        present = bool(label and label.casefold() in all_candidate_text)
        mandatory.append({"requirement": label, "status": "PASS" if present else "NOT_VERIFIED",
            "evidence": f"Candidate records contain {label}." if present else "No conclusive evidence was found.",
            "reason": f"Evaluated as a mandatory {kind} requirement without converting missing data to failure."})
    return {"candidate_score": total, "maximum_score": 100, "match_percentage": total, "match_level": level,
        "evidence_confidence": confidence, "score_breakdown": output_breakdown, "mandatory_requirements": mandatory, "skill_analysis": skill_analysis,
        "strongest_matches": sorted(matched)[:5], "skill_gaps": sorted(set(_terms(required)) - set(matched)), "experience_gaps": [],
        "verification_gaps": ([] if github_available else ["GitHub evidence unavailable or unverified"]), "candidate_strengths": sorted(matched)[:5],
        "concerns": [], "recommendation": {"decision": "HIGHLY_RECOMMENDED" if total >= 90 else "RECOMMENDED" if total >= 75 else "CONSIDER" if total >= 55 else "MANUAL_REVIEW" if confidence < 60 else "NOT_RECOMMENDED", "reason": f"Job-specific evidence score is {total}/100 with {confidence}% evidence confidence."}}


def normalize_result(raw, fallback):
    result = raw if isinstance(raw, dict) else fallback
    incoming = result.get("score_breakdown") if isinstance(result.get("score_breakdown"), dict) else {}
    clean = {}
    for key, maximum in CATEGORY_MAX.items():
        item = incoming.get(key) if isinstance(incoming.get(key), dict) else {}
        try: value = float(item.get("score", 0))
        except (TypeError, ValueError): value = 0
        clean[key] = {"score": round(max(0, min(maximum, value)), 1), "max": maximum, "reason": str(item.get("reason") or "No relevant evidence was identified.")[:1000]}
    result["score_breakdown"] = clean
    result["candidate_score"] = result["match_percentage"] = round(sum(x["score"] for x in clean.values()), 1)
    result["maximum_score"] = 100
    try: result["evidence_confidence"] = round(max(0, min(100, float(result.get("evidence_confidence", fallback["evidence_confidence"])))), 1)
    except (TypeError, ValueError): result["evidence_confidence"] = fallback["evidence_confidence"]
    total = result["candidate_score"]
    result["match_level"] = "Exceptional Match" if total >= 90 else "Strong Match" if total >= 80 else "Good Match" if total >= 70 else "Moderate Match" if total >= 60 else "Weak/Borderline Match" if total >= 50 else "Low Match"
    for key in ("mandatory_requirements", "skill_analysis", "strongest_matches", "skill_gaps", "experience_gaps", "verification_gaps", "candidate_strengths", "concerns"):
        if not isinstance(result.get(key), list): result[key] = fallback[key]
    allowed_decisions = {"HIGHLY_RECOMMENDED", "RECOMMENDED", "CONSIDER", "MANUAL_REVIEW", "NOT_RECOMMENDED"}
    if not isinstance(result.get("recommendation"), dict) or result["recommendation"].get("decision") not in allowed_decisions:
        result["recommendation"] = fallback["recommendation"]
    return result


async def evaluate(job: Dict[str, Any], candidate: Dict[str, Any], generate_json: Callable[[str], Awaitable[dict]] | None = None):
    fallback = deterministic_evaluation(job, candidate)
    if not generate_json: return fallback, "deterministic"
    prompt = f"{SYSTEM_PROMPT}\n\nJOB DESCRIPTION:\n{json.dumps(job, default=str)}\n\nCANDIDATE PROFILE:\n{json.dumps(candidate, default=str)}"
    try: return normalize_result(await generate_json(prompt), fallback), "gemini"
    except Exception: return fallback, "deterministic_fallback"


def enterprise_scores(result):
    return {key: {"match_percentage": round(item["score"] / item["max"] * 100, 1) if item["max"] else 0,
        "weighted_score": item["score"], "maximum_score": item["max"], "reason": item["reason"], "evidence": [],
        "confidence": result.get("evidence_confidence", 0) / 100} for key, item in result["score_breakdown"].items()}
