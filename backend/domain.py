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
    linkedin_url: str | None = None
    portfolio_url: str | None = None


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
    start_year: int | None = Field(default=None)
    end_year: int | None = Field(default=None)
    grade: str | None = None
    degree: str | None = None
    final_year_project: str | None = None
    confidence: float = Field(default=.5, ge=0, le=1)

    @model_validator(mode="before")
    @classmethod
    def parse_years(cls, data):
        if not isinstance(data, dict):
            return data
        for k in ("start_year", "end_year"):
            val = data.get(k)
            if isinstance(val, str):
                import re
                m = re.search(r"\b(19\d\d|20\d\d)\b", val)
                data[k] = int(m.group(1)) if m else None
        return data


class Certification(StrictModel):
    name: str
    issuer: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    credential_url: str | None = None
    credential_id: str | None = None
    confidence: float = Field(default=.5, ge=0, le=1)


class Github(StrictModel):
    profile_url: str | None = None
    username: str | None = None
    repositories: list = Field(default_factory=list)


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

    @model_validator(mode="before")
    @classmethod
    def handle_null_submodels(cls, data):
        if not isinstance(data, dict):
            return data
        if data.get("personal_info") is None:
            data["personal_info"] = {}
        if data.get("github") is None:
            data["github"] = {}
        for list_field in ("technical_skills", "soft_skills", "experience", "projects", "education", "certifications", "languages"):
            if data.get(list_field) is None:
                data[list_field] = []
        return data


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
        if isinstance(value, dict):
            required_keys = set(CATEGORIES)
            if not required_keys.issubset(set(value.keys())):
                return DEFAULT_WEIGHTS.copy()
            cleaned = {k: float(value[k]) for k in required_keys if k in value}
            if abs(sum(cleaned.values()) - 100.0) > 0.1:
                return DEFAULT_WEIGHTS.copy()
            return cleaned
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
    stamp = utcnow()
    log_doc = {
        "id": identifier(),
        "action": action,
        "actor_id": actor_id,
        "userId": actor_id,
        "performedBy": actor_id,
        "entity_type": entity_type,
        "collectionName": entity_type,
        "entity_id": str(entity_id),
        "documentId": str(entity_id),
        "details": details or {},
        "oldValue": (details or {}).get("oldValue") if isinstance(details, dict) else None,
        "newValue": (details or {}).get("newValue") if isinstance(details, dict) else None,
        "createdAt": stamp,
        "created_at": stamp,
    }
    db.audit_logs.insert_one(log_doc)

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

    # Build rich skill objects
    structured_skills = []
    seen_skills = set()
    for kind, items in (("technical", data.get("technical_skills", [])), ("soft", data.get("soft_skills", []))):
        for item in items:
            skill_name = item.get("skill")
            if not skill_name:
                continue
            key = (normalized(skill_name), kind)
            if key in seen_skills:
                continue
            seen_skills.add(key)
            evidence = item.get("evidence") or []
            if isinstance(evidence, str): evidence = [evidence]
            structured_skills.append({
                "id": identifier(),
                "candidate_id": candidate_id,
                "skill": skill_name,
                "normalized_skill": normalized(skill_name),
                "kind": kind,
                "confidence": float(item.get("confidence", 0.85)),
                "evidence": evidence,
                "source": "cv_gemini",
                "sources": ["cv_gemini"],
                "verified_by_recruiter": False,
                "updated_at": stamp,
                "created_at": stamp,
            })

    # Build structured experience records
    experience_records = []
    for item in data.get("experience", []):
        experience_records.append({
            **item,
            "id": identifier(),
            "candidate_id": candidate_id,
            "normalized_company": normalized(item.get("company")),
            "normalized_position": normalized(item.get("position")),
            "normalized_start_date": normalized(item.get("start_date")),
            "duration_months": duration_months(item.get("start_date"), item.get("end_date"), item.get("is_current", False)),
            "source": "cv_gemini",
            "sources": ["cv_gemini"],
            "confidence": float(item.get("confidence", 0.9)),
            "created_at": stamp,
            "updated_at": stamp,
        })

    # Build structured education records
    education_records = []
    for item in data.get("education", []):
        education_records.append({
            **item,
            "id": identifier(),
            "candidate_id": candidate_id,
            "normalized_qualification": normalized(item.get("qualification")),
            "normalized_institution": normalized(item.get("institution")),
            "normalized_field": normalized(item.get("field")),
            "source": "cv_gemini",
            "sources": ["cv_gemini"],
            "confidence": float(item.get("confidence", 0.9)),
            "created_at": stamp,
            "updated_at": stamp,
        })

    # Build structured projects records
    project_records = []
    for item in data.get("projects", []):
        project_records.append({
            **item,
            "id": identifier(),
            "candidate_id": candidate_id,
            "normalized_name": normalized(item.get("name")),
            "source": "cv_gemini",
            "sources": ["cv_gemini"],
            "confidence": float(item.get("confidence", 0.9)),
            "created_at": stamp,
            "updated_at": stamp,
        })

    # Build structured certifications records
    certification_records = []
    for item in data.get("certifications", []):
        certification_records.append({
            **item,
            "id": identifier(),
            "candidate_id": candidate_id,
            "normalized_name": normalized(item.get("name")),
            "normalized_issuer": normalized(item.get("issuer")),
            "source": "cv_gemini",
            "sources": ["cv_gemini"],
            "confidence": float(item.get("confidence", 0.9)),
            "created_at": stamp,
            "updated_at": stamp,
        })

    # Build structured language records
    language_records = []
    unique_languages = {normalized(item.get("language")): item for item in data.get("languages", []) if normalized(item.get("language"))}
    for key, item in unique_languages.items():
        language_records.append({
            **item,
            "id": identifier(),
            "candidate_id": candidate_id,
            "language": item.get("language"),
            "normalized_language": key,
            "level": None,
            "speaking_level": language_proficiency(item.get("speaking_level") or item.get("level")),
            "reading_level": language_proficiency(item.get("reading_level") or item.get("level")),
            "writing_level": language_proficiency(item.get("writing_level") or item.get("level")),
            "source": "cv_gemini",
            "sources": ["cv_gemini"],
            "created_at": stamp,
            "updated_at": stamp,
        })

    profile_doc = {
        "id": candidate_id,
        "user_id": candidate_id,
        "personal_info": personal_info,
        "social_links": social_links,
        "skills_summary": skills_summary,
        "technical_skills": tech_skills,
        "soft_skills": soft_skills,
        "skills": structured_skills,
        "experience": experience_records,
        "education": education_records,
        "projects": project_records,
        "certifications": certification_records,
        "languages": language_records,
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
    }

    # Save to candidate_profiles collection
    db.candidate_profiles.update_one(
        {"$or": [{"id": candidate_id}, {"user_id": candidate_id}]},
        {"$set": profile_doc, "$setOnInsert": {"created_at": stamp}},
        upsert=True,
    )

    # Sync user record display fields
    user_updates = {
        "technicalSkills": ", ".join(tech_skills),
        "softSkills": ", ".join(soft_skills),
        "skills": ", ".join(all_skills),
        "headline": personal_info.get("professional_title") or personal_info.get("headline"),
        "location": personal_info.get("location"),
        "phone": personal_info.get("phone"),
        "updatedAt": stamp.isoformat(),
    }
    if social_links.get("linkedin_url"):
        user_updates["linkedinUrl"] = social_links["linkedin_url"]
    if social_links.get("portfolio_url"):
        user_updates["portfolioUrl"] = social_links["portfolio_url"]
    if social_links.get("github_url"):
        user_updates["githubUrl"] = social_links["github_url"]
    
    clean_updates = {k: v for k, v in user_updates.items() if v is not None}
    db.users.update_one({"id": candidate_id}, {"$set": clean_updates})

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

        # Update candidate_profiles collection
        existing_profile = db.candidate_profiles.find_one({"$or": [{"id": candidate_id}, {"user_id": candidate_id}]}) or {}
        existing_skills = existing_profile.get("skills", [])
        
        # Merge manual skills into skills array
        updated_skills = [s for s in existing_skills if s.get("source") != "candidate_manual"]
        for skill in tech_skills:
            updated_skills.append({
                "id": identifier(),
                "candidate_id": candidate_id,
                "skill": skill,
                "normalized_skill": normalized(skill),
                "kind": "technical",
                "source": "candidate_manual",
                "sources": ["candidate_manual"],
                "confidence": 1.0,
                "evidence": ["Added manually to profile"],
                "entered_by": candidate_id,
                "created_at": stamp,
                "updated_at": stamp,
            })
        for skill in soft_skills:
            updated_skills.append({
                "id": identifier(),
                "candidate_id": candidate_id,
                "skill": skill,
                "normalized_skill": normalized(skill),
                "kind": "soft",
                "source": "candidate_manual",
                "sources": ["candidate_manual"],
                "confidence": 1.0,
                "evidence": ["Added manually to profile"],
                "entered_by": candidate_id,
                "created_at": stamp,
                "updated_at": stamp,
            })

        profile_doc = {
            "id": candidate_id,
            "user_id": candidate_id,
            "personal_info": personal,
            "social_links": social_links,
            "career_preferences": career_preferences,
            "skills_summary": skills_summary,
            "technical_skills": tech_skills,
            "soft_skills": soft_skills,
            "skills": updated_skills,
            "updated_at": stamp,
        }
        db.candidate_profiles.update_one(
            {"$or": [{"id": candidate_id}, {"user_id": candidate_id}]},
            {"$set": profile_doc, "$setOnInsert": {"created_at": stamp}},
            upsert=True,
        )

    elif role == "recruiter":
        # Recruiter details are maintained in users collection
        recruiter_updates = {
            "name": changes.get("name", user.get("name")),
            "phone": changes.get("phone", user.get("phone")),
            "headline": changes.get("headline", user.get("headline")),
            "bio": changes.get("bio", user.get("bio")),
            "company": changes.get("company", user.get("company")),
            "location": changes.get("location", user.get("location")),
            "updatedAt": stamp.isoformat(),
        }
        clean_recruiter_updates = {k: v for k, v in recruiter_updates.items() if v is not None}
        db.users.update_one({"id": user_id}, {"$set": clean_recruiter_updates})



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
