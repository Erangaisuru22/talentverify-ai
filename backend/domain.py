"""Validated recruitment domain records; Gemini never writes to MongoDB directly."""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

PROFILE_CATEGORIES = ("technical_skills", "experience", "projects", "education", "certifications", "github_evidence", "job_relevance")
CATEGORIES = (*PROFILE_CATEGORIES, "technical_assessment", "structured_interview")
AI_CATEGORIES = PROFILE_CATEGORIES
DEFAULT_WEIGHTS = {"technical_skills": 20, "experience": 15, "projects": 10, "education": 5,
                   "certifications": 5, "github_evidence": 5, "job_relevance": 10,
                   "technical_assessment": 15, "structured_interview": 15}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PersonalInfo(StrictModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    professional_title: str | None = None
    linkedin_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None


class TechnicalSkill(StrictModel):
    skill: str
    category: str | None = None
    source: str = "cv"
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=.5, ge=0, le=1)


class SoftSkill(StrictModel):
    skill: str
    evidence: str | None = None
    confidence: float = Field(default=.5, ge=0, le=1)


class Experience(StrictModel):
    company: str | None = None
    position: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    employment_type: str | None = None
    location: str | None = None
    confidence: float = Field(default=.5, ge=0, le=1)


class Project(StrictModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    github_url: HttpUrl | None = None
    demo_url: HttpUrl | None = None
    candidate_contribution: str | None = None
    project_type: str | None = None
    achievements: list[str] = Field(default_factory=list)
    confidence: float = Field(default=.5, ge=0, le=1)


class Education(StrictModel):
    qualification: str | None = None
    institution: str | None = None
    field: str | None = None
    start_year: int | None = Field(default=None, ge=1900, le=2200)
    end_year: int | None = Field(default=None, ge=1900, le=2200)
    grade: str | None = None
    degree: str | None = None
    final_year_project: str | None = None
    confidence: float = Field(default=.5, ge=0, le=1)


class Certification(StrictModel):
    name: str
    issuer: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    credential_url: HttpUrl | None = None
    credential_id: str | None = None
    confidence: float = Field(default=.5, ge=0, le=1)


class Github(StrictModel):
    profile_url: HttpUrl | None = None
    username: str | None = None
    repositories: list = Field(default_factory=list, max_length=0)


class GithubSkillFinding(StrictModel):
    type: str
    finding: str


class GithubSkillEvidence(StrictModel):
    skill: str
    evidence_source: str = "github"
    repository: str
    evidence: list[GithubSkillFinding] = Field(default_factory=list)
    verified: bool = True
    confidence: float = Field(default=0.9, ge=0, le=1)


class GithubRepositoryEvidence(StrictModel):
    candidate_id: str | None = None
    repository_name: str
    repository_url: str
    description: str | None = None
    languages: list[str] = Field(default_factory=list)
    technologies_detected: list[str] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    repository_metadata: dict = Field(default_factory=dict)
    verification_status: str = "verified"


class CvGithubConsistency(StrictModel):
    confirmed_skills: list[str] = Field(default_factory=list)
    unverified_skills: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    consistency_level: str = "strong"


class JobRelevantRepository(StrictModel):
    repository: str
    relevance: str = "medium"
    reason: str


class GeminiGithubAnalysis(StrictModel):
    match_percentage: float = Field(default=0.0, ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    job_relevant_repositories: list[JobRelevantRepository] = Field(default_factory=list)
    confidence: float = Field(default=0.9, ge=0, le=1)


class Language(StrictModel):
    language: str
    level: str | None = None
    evidence: str | None = None
    speaking_level: str | None = None
    reading_level: str | None = None
    writing_level: str | None = None


class CvExtraction(StrictModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    technical_skills: list[TechnicalSkill] = Field(default_factory=list)
    soft_skills: list[SoftSkill] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    github: Github = Field(default_factory=Github)
    languages: list[Language] = Field(default_factory=list)


class ScoreWeights(StrictModel):
    technical_skills: float = Field(default=20, ge=0, le=100)
    experience: float = Field(default=15, ge=0, le=100)
    projects: float = Field(default=10, ge=0, le=100)
    education: float = Field(default=5, ge=0, le=100)
    certifications: float = Field(default=5, ge=0, le=100)
    github_evidence: float = Field(default=5, ge=0, le=100)
    job_relevance: float = Field(default=10, ge=0, le=100)
    technical_assessment: float = Field(default=15, ge=0, le=100)
    structured_interview: float = Field(default=15, ge=0, le=100)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_weights(cls, value):
        # Jobs saved before enterprise scoring used incompatible categories. Migrating to
        # the published enterprise defaults is safer than silently producing a non-100 total.
        if isinstance(value, dict) and ("cv_soft_skills" in value or "interview" in value):
            return DEFAULT_WEIGHTS.copy()
        return value

    @model_validator(mode="after")
    def exact_total(self):
        if abs(sum(getattr(self, key) for key in CATEGORIES) - 100) > .001:
            raise ValueError("Scoring weights must total exactly 100")
        return self

class CategoryEvaluation(StrictModel):
    match_percentage: float = Field(ge=0, le=100)
    reason: str
    evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    source: list[str] = Field(default_factory=list)

class AiEvaluation(StrictModel):
    technical_skills: CategoryEvaluation
    experience: CategoryEvaluation
    projects: CategoryEvaluation
    education: CategoryEvaluation
    certifications: CategoryEvaluation
    github_evidence: CategoryEvaluation
    job_relevance: CategoryEvaluation

def weighted_evaluation(evaluation, weights):
    scores = {}; total = 0
    for category in AI_CATEGORIES:
        item = getattr(evaluation, category); maximum = getattr(weights, category)
        weighted = round(item.match_percentage / 100 * maximum, 2); total += weighted
        scores[category] = {**item.model_dump(), "weighted_score": weighted, "maximum_score": maximum}
    return scores, round(total, 2)


def utcnow(): return datetime.now(timezone.utc)
def identifier(): return str(uuid.uuid4())
def normalized(value): return " ".join(str(value or "").strip().casefold().split())

def language_proficiency(value):
    key = normalized(value)
    if any(term in key for term in ("native", "bilingual", "fluent", "advanced", "full professional")): return "Fluent"
    if any(term in key for term in ("moderate", "intermediate", "professional working", "conversational")): return "Moderate"
    return "Basic"

def audit(db, action, actor_id, entity_type, entity_id, details=None):
    db.audit_logs.insert_one({"id": identifier(), "action": action, "actor_id": actor_id,
        "entity_type": entity_type, "entity_id": entity_id, "details": details or {}, "created_at": utcnow()})

def duration_months(start, end, current=False):
    if not start: return None
    try:
        start_date = datetime.strptime(start[:7], "%Y-%m")
        end_date = utcnow() if current or not end else datetime.strptime(end[:7], "%Y-%m").replace(tzinfo=timezone.utc)
        if start_date.tzinfo is None: start_date = start_date.replace(tzinfo=timezone.utc)
        return max(0, (end_date.year - start_date.year) * 12 + end_date.month - start_date.month)
    except (TypeError, ValueError): return None


def save_extraction(db, candidate_id, extraction, document_id, file_name, model_name):
    data = extraction.model_dump(mode="json"); stamp = utcnow()
    tech_skills = [item["skill"] for item in data.get("technical_skills", []) if item.get("skill")]
    soft_skills = [item["skill"] for item in data.get("soft_skills", []) if item.get("skill")]
    all_skills = list(dict.fromkeys(tech_skills + soft_skills))

    personal_info = data.get("personal_info", {})
    social_links = {
        "linkedin_url": str(personal_info.get("linkedin_url") or "") if personal_info.get("linkedin_url") else None,
        "github_url": str(data.get("github", {}).get("profile_url") or "") if data.get("github", {}).get("profile_url") else None,
        "portfolio_url": str(personal_info.get("portfolio_url") or "") if personal_info.get("portfolio_url") else None,
    }

    skills_summary = {
        "technical_skills": tech_skills,
        "soft_skills": soft_skills,
        "all_skills": all_skills,
    }

    db.candidates.update_one(
        {"id": candidate_id},
        {
            "$set": {
                "id": candidate_id,
                "user_id": candidate_id,
                "personal_info": personal_info,
                "social_links": social_links,
                "skills_summary": skills_summary,
                "cv": {
                    "file_id": document_id,
                    "file_name": file_name,
                    "uploaded_at": stamp,
                    "parsed_at": stamp,
                    "parser": "gemini",
                    "parser_model": model_name,
                    "parsing_status": "completed",
                },
                "updated_at": stamp,
            },
            "$setOnInsert": {"created_at": stamp},
        },
        upsert=True,
    )

    for kind, items in (("technical", data["technical_skills"]), ("soft", data["soft_skills"])):
        for item in items:
            evidence = item.get("evidence") or []
            if isinstance(evidence, str): evidence = [evidence]
            key = normalized(item["skill"])
            existing = db.candidate_skills.find_one({"candidate_id": candidate_id, "normalized_skill": key, "kind": kind})
            db.candidate_skills.update_one({"_id": existing["_id"]} if existing else {"candidate_id": candidate_id, "normalized_skill": key, "source": "cv_gemini"},
                {"$set": {"candidate_id": candidate_id, "skill": item["skill"], "normalized_skill": key,
                "kind": kind, "confidence": max(float((existing or {}).get("confidence", 0)), item["confidence"]),
                "verified_by_recruiter": False, "updated_at": stamp},
                 "$setOnInsert": {"id": identifier(), "source": "cv_gemini", "created_at": stamp},
                 "$addToSet": {"sources": "cv_gemini", "evidence": {"$each": evidence}}}, upsert=True)
    for field, collection in (("experience", "candidate_experience"), ("projects", "candidate_projects"),
                              ("education", "candidate_education"), ("certifications", "candidate_certifications")):
        db[collection].delete_many({"candidate_id": candidate_id, "source": "cv_gemini"})
        keys = {"experience": ("company", "position", "start_date"), "projects": ("name",),
                "education": ("qualification", "institution", "field"), "certifications": ("name", "issuer")}[field]
        unique = {}
        for item in data[field]:
            key = "|".join(normalized(item.get(part)) for part in keys)
            if key.strip("|") and key not in unique: unique[key] = item
        records = [{**item, **{f"normalized_{part}": normalized(item.get(part)) for part in keys}, "id": identifier(), "candidate_id": candidate_id, "source": "cv_gemini",
            **({"duration_months": duration_months(item.get("start_date"), item.get("end_date"), item.get("is_current", False))} if field == "experience" else {})} for item in unique.values()]
        if records: db[collection].insert_many(records)
    db.candidate_languages.delete_many({"candidate_id": candidate_id, "source": "cv_gemini"})
    unique_languages = {normalized(item.get("language")): item for item in data["languages"] if normalized(item.get("language"))}
    languages = [{**item, "level": None,
        "speaking_level": language_proficiency(item.get("speaking_level") or item.get("level")),
        "reading_level": language_proficiency(item.get("reading_level") or item.get("level")),
        "writing_level": language_proficiency(item.get("writing_level") or item.get("level")),
        "normalized_language": key, "id": identifier(), "candidate_id": candidate_id, "source": "cv_gemini"}
        for key, item in unique_languages.items()]
    if languages: db.candidate_languages.insert_many(languages)
    github = data["github"]
    existing_github = db.candidate_github.find_one({"candidate_id": candidate_id}) or {}
    incoming_url = github.get("profile_url")
    same_verified_profile = (existing_github.get("verification_status") == "verified" and incoming_url and
                             str(existing_github.get("github_url", "")).rstrip("/").casefold() == str(incoming_url).rstrip("/").casefold())
    if not same_verified_profile and (incoming_url or not existing_github):
        db.candidate_github.update_one({"candidate_id": candidate_id}, {"$set": {"candidate_id": candidate_id,
            "github_url": incoming_url, "username": github.get("username"), "source": "cv",
            "verification_status": "not_verified", "analysis": {"repository_count": None, "selected_repositories": [],
            "main_languages": [], "candidate_commits_sampled": None, "code_quality_score": None}}}, upsert=True)
    audit(db, "cv_extraction_saved", candidate_id, "candidate", candidate_id, {"document_id": document_id})


def save_manual_profile(db, user, changes):
    stamp = utcnow()
    user_id = user["id"]
    role = user.get("role")

    if role == "candidate":
        candidate_id = user_id
        personal = {
            "full_name": changes.get("name", user.get("name")),
            "email": user.get("email"),
            "phone": changes.get("phone", user.get("phone")),
            "location": changes.get("location", user.get("location")),
            "headline": changes.get("headline", user.get("headline")),
            "company": changes.get("company", user.get("company")),
            "bio": changes.get("bio", user.get("bio")),
            "experience_years": float(changes.get("experience", user.get("experience") or 0)),
        }
        social_links = {
            "linkedin_url": changes.get("linkedinUrl", user.get("linkedinUrl")),
            "github_url": changes.get("githubUrl", user.get("githubUrl")),
            "portfolio_url": changes.get("portfolioUrl", user.get("portfolioUrl")),
        }
        career_preferences = {
            "notice_period": changes.get("noticePeriod", user.get("noticePeriod")),
            "availability": changes.get("availability", user.get("availability")),
            "preferred_roles": [r.strip() for r in str(changes.get("preferredRoles", user.get("preferredRoles") or "")).split(",") if r.strip()],
            "work_preference": changes.get("workPreference", user.get("workPreference")),
        }

        tech_str = changes.get("technicalSkills", user.get("technicalSkills", ""))
        soft_str = changes.get("softSkills", user.get("softSkills", ""))
        tech_skills = [x.strip() for x in str(tech_str or "").split(",") if x.strip()]
        soft_skills = [x.strip() for x in str(soft_str or "").split(",") if x.strip()]
        all_skills = list(dict.fromkeys(tech_skills + soft_skills))

        skills_summary = {
            "technical_skills": tech_skills,
            "soft_skills": soft_skills,
            "all_skills": all_skills,
        }

        candidate_doc = {
            "id": candidate_id,
            "user_id": candidate_id,
            "personal_info": personal,
            "social_links": social_links,
            "career_preferences": career_preferences,
            "skills_summary": skills_summary,
            "updated_at": stamp,
        }
        db.candidates.update_one(
            {"id": candidate_id},
            {"$set": candidate_doc, "$setOnInsert": {"created_at": stamp}},
            upsert=True,
        )
        # Keep the canonical intelligence profile synchronized with manual edits.
        db.candidate_profiles.update_one(
            {"id": candidate_id},
            {"$set": {
                "id": candidate_id,
                "user_id": candidate_id,
                "personal_info": personal,
                "social_links": social_links,
                "career_preferences": career_preferences,
                "technical_skills": tech_skills,
                "soft_skills": soft_skills,
                "updated_at": stamp,
            }, "$setOnInsert": {"created_at": stamp}},
            upsert=True,
        )

        for kind, field in (("technical", "technicalSkills"), ("soft", "softSkills")):
            if field not in changes: continue
            for skill in [x.strip() for x in str(changes.get(field) or "").split(",") if x.strip()]:
                key = normalized(skill)
                existing = db.candidate_skills.find_one({"candidate_id": candidate_id, "normalized_skill": key, "kind": kind})
                db.candidate_skills.update_one(
                    {"_id": existing["_id"]} if existing else {"candidate_id": candidate_id, "normalized_skill": key, "source": "candidate_manual"},
                    {
                        "$set": {
                            "candidate_id": candidate_id,
                            "skill": skill,
                            "normalized_skill": key,
                            "kind": kind,
                            "entered_by": candidate_id,
                            "updated_at": stamp,
                        },
                        "$setOnInsert": {
                            "id": identifier(),
                            "source": "candidate_manual",
                            "evidence": ["Added manually to profile"],
                            "created_at": stamp,
                        },
                        "$addToSet": {"sources": "candidate_manual"},
                    },
                    upsert=True,
                )

    elif role == "recruiter":
        recruiter_id = user_id
        recruiter_doc = {
            "id": recruiter_id,
            "user_id": recruiter_id,
            "personal_info": {
                "full_name": changes.get("name", user.get("name")),
                "email": user.get("email"),
                "phone": changes.get("phone", user.get("phone")),
                "headline": changes.get("headline", user.get("headline")),
                "bio": changes.get("bio", user.get("bio")),
            },
            "company_details": {
                "company_name": changes.get("company", user.get("company")),
                "location": changes.get("location", user.get("location")),
            },
            "updated_at": stamp,
        }
        db.recruiters.update_one(
            {"id": recruiter_id},
            {"$set": recruiter_doc, "$setOnInsert": {"created_at": stamp}},
            upsert=True,
        )



def legacy_evaluation(analysis, candidate_years, required_years, weights):
    breakdown = analysis.get("score_breakdown", {}); skill_max = float(breakdown.get("skill_max") or 100)
    technical = min(100, 100 * float(breakdown.get("skill_points") or 0) / skill_max) if skill_max else 0
    experience = min(100, 100 * float(candidate_years or 0) / float(required_years)) if float(required_years or 0) else 100
    matches = len(analysis.get("matched_skills") or []); missing = len(analysis.get("missing_skills") or [])
    relevance = 100 * matches / (matches + missing) if matches + missing else 0
    percentages = {"technical_skills": technical, "cv_soft_skills": 0, "experience": experience, "projects": 0,
                   "education": 0, "certifications": 0, "github_evidence": 0, "job_relevance": relevance}
    scores = {}; total = 0
    for category in AI_CATEGORIES:
        percentage = round(percentages[category], 2); maximum = getattr(weights, category)
        weighted = round(percentage / 100 * maximum, 2); total += weighted
        scores[category] = {"match_percentage": percentage, "weighted_score": weighted, "maximum_score": maximum,
            "reason": "Calculated from validated application evidence" if percentage else "No validated evidence supplied",
            "evidence": analysis.get("matched_skills", []) if category in {"technical_skills", "job_relevance"} else [], "confidence": .8 if percentage else 0}
    return scores, round(total, 2)
