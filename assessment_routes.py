"""FastAPI Assessment and Candidate Profile Routes using 7 core collections."""

from fastapi import APIRouter, HTTPException
from database import db
from domain import AI_CATEGORIES, DEFAULT_WEIGHTS, PROFILE_CATEGORIES, ScoreWeights, audit, duration_months, identifier, normalized, utcnow
from enterprise_evaluation import (DECISIONS, DEFAULT_BANDS, evaluate_eligibility, normalized_stage,
                                   pending_decision, profile_totals, recommendation, score_interview)


def clean(value):
    return {k: v for k, v in value.items() if k != "_id"} if value else None


def deduplicated(records, key_fields):
    """Return one UI record per normalized identity while preserving every source."""
    merged = {}
    for raw in records:
        item = clean(raw)
        key = "|".join(normalized(item.get(field)) for field in key_fields)
        if not key.strip("|"):
            key = item.get("id", "")
        if key not in merged:
            item["sources"] = [item.get("source")] if item.get("source") else []
            merged[key] = item
            continue
        current = merged[key]
        if item.get("source") and item["source"] not in current.get("sources", []):
            current.setdefault("sources", []).append(item["source"])
        for field, value in item.items():
            if field in {"_id", "source", "sources"}:
                continue
            if isinstance(value, list):
                existing = current.get(field) if isinstance(current.get(field), list) else []
                current[field] = list(dict.fromkeys([*existing, *value]))
            elif value not in (None, "", 0, False) and current.get(field) in (None, "", 0, False):
                current[field] = value
    return list(merged.values())


def build_assessment_router(require_session):
    router = APIRouter(prefix="/api")

    def resolve_candidate_id(user, candidate_id: str) -> str:
        """Resolve the candidate-facing `me` alias and enforce self access."""
        if candidate_id == "me":
            if user.get("role") != "candidate":
                raise HTTPException(403, "Only candidates can use the 'me' profile alias.")
            return user["id"]
        if user.get("role") == "candidate" and candidate_id != user.get("id"):
            raise HTTPException(403, "Not authorized to view another candidate's evidence.")
        return candidate_id

    def get_application(user, application_id):
        item = db.applications.find_one({"id": application_id})
        if not item:
            raise HTTPException(404, "Application not found.")
        if user["role"] == "candidate" and item.get("userId") != user["id"]:
            raise HTTPException(404, "Application not found.")
        if user["role"] == "recruiter" and not db.jobs.find_one({"id": item["jobId"], "recruiterId": user["id"]}):
            raise HTTPException(404, "Application not found.")
        return item

    @router.get("/candidates/me/structured")
    def structured_profile(token: str):
        user = require_session(token)
        cid = user["id"]
        cand_profile = db.candidate_profiles.find_one({"$or": [{"id": cid}, {"user_id": cid}]}) or {}

        # Query snapshots from unified evidence_snapshots collection
        github_snap = db.evidence_snapshots.find_one({"candidate_id": cid, "platform": "github"}, sort=[("scanned_at", -1)]) or cand_profile.get("github")
        linkedin_snap = db.evidence_snapshots.find_one({"candidate_id": cid, "platform": "linkedin"}, sort=[("verified_at", -1)])
        linkedin_hist = [clean(x) for x in db.evidence_snapshots.find({"candidate_id": cid, "platform": "linkedin"}).sort("verified_at", -1).limit(10)]
        portfolio_snap = db.evidence_snapshots.find_one({"candidate_id": cid, "platform": "portfolio"}, sort=[("verified_at", -1)])

        return {
            "candidate": clean(cand_profile),
            "skills": deduplicated(cand_profile.get("skills", []), ("normalized_skill", "kind")),
            "experience": deduplicated(cand_profile.get("experience", []), ("company", "position", "start_date")),
            "projects": deduplicated(cand_profile.get("projects", []), ("name",)),
            "education": deduplicated(cand_profile.get("education", []), ("qualification", "institution", "field")),
            "certifications": deduplicated(cand_profile.get("certifications", []), ("name", "issuer")),
            "languages": deduplicated(cand_profile.get("languages", []), ("language",)),
            "cv_analyses": [clean(x) for x in db.cv_documents.find({"candidate_id": cid}, {"_id": 0, "content": 0, "raw_gemini_result": 0}).sort("uploaded_at", -1)],
            "github": clean(github_snap),
            "linkedin": clean(linkedin_snap),
            "linkedin_history": linkedin_hist,
            "portfolio": clean(portfolio_snap)
        }

    @router.post("/candidates/me/{section}")
    def add_profile_record(section: str, payload: dict, token: str):
        user = require_session(token)
        if user["role"] != "candidate":
            raise HTTPException(403, "Only candidates can edit profile records.")

        valid_sections = {"experience", "education", "projects", "certifications", "languages"}
        if section not in valid_sections:
            raise HTTPException(404, "Profile section not found.")

        required = {
            "experience": "company",
            "education": "qualification",
            "projects": "name",
            "certifications": "name",
            "languages": "language",
        }
        value = str(payload.get(required[section], "")).strip()
        if not value:
            raise HTTPException(422, f"{required[section]} is required")

        allowed = {
            "experience": {"company", "position", "start_date", "end_date", "is_current", "responsibilities", "technologies", "achievements", "location", "employment_type"},
            "education": {"qualification", "degree", "field", "institution", "start_year", "end_year", "grade", "final_year_project"},
            "projects": {"name", "description", "candidate_contribution", "technologies", "github_url", "demo_url", "project_type", "achievements"},
            "certifications": {"name", "issuer", "issue_date", "expiry_date", "credential_url", "credential_id"},
            "languages": {"language", "speaking_level", "reading_level", "writing_level", "level", "evidence"},
        }[section]

        item = {key: value for key, value in payload.items() if key in allowed}
        if section == "languages":
            supported_languages = {"english", "sinhala", "tamil"}
            proficiency_levels = {"basic", "moderate", "fluent"}
            if normalized(item.get("language")) not in supported_languages:
                raise HTTPException(422, "Language must be English, Sinhala, or Tamil.")
            item.pop("level", None)
            for field in ("speaking_level", "reading_level", "writing_level"):
                if normalized(item.get(field)) not in proficiency_levels:
                    raise HTTPException(422, f"{field.replace('_', ' ').title()} must use a recognized professional proficiency level.")

        identity_fields = {
            "experience": ("company", "position", "start_date"),
            "education": ("qualification", "institution", "field"),
            "projects": ("name",),
            "certifications": ("name", "issuer"),
            "languages": ("language",),
        }[section]
        identity = {f"normalized_{field}": normalized(item.get(field)) for field in identity_fields}
        item.update(identity)
        if section == "experience":
            item["duration_months"] = duration_months(item.get("start_date"), item.get("end_date"), item.get("is_current", False))

        cand_profile = db.candidate_profiles.find_one({"$or": [{"id": user["id"]}, {"user_id": user["id"]}]}) or {}
        section_list = list(cand_profile.get(section, []))

        # Check existing item
        existing_idx = None
        for idx, existing in enumerate(section_list):
            if all(existing.get(k) == v for k, v in identity.items()):
                existing_idx = idx
                break

        stamp = utcnow()
        if existing_idx is not None:
            prior = section_list[existing_idx]
            prior_source = prior.get("source")
            sources = list(dict.fromkeys([*(prior.get("sources") or ([prior_source] if prior_source else [])), "candidate_manual"]))
            item.update({
                "id": prior.get("id", identifier()),
                "candidate_id": user["id"],
                "source": "candidate_manual",
                "sources": sources,
                "confidence": 1.0,
                "created_at": prior.get("created_at", stamp),
                "updated_at": stamp
            })
            section_list[existing_idx] = item
        else:
            item.update({
                "id": identifier(),
                "candidate_id": user["id"],
                "source": "candidate_manual",
                "sources": ["candidate_manual"],
                "confidence": 1.0,
                "created_at": stamp,
                "updated_at": stamp
            })
            section_list.append(item)

        db.candidate_profiles.update_one(
            {"$or": [{"id": user["id"]}, {"user_id": user["id"]}]},
            {"$set": {section: section_list, "updated_at": stamp}, "$setOnInsert": {"id": user["id"], "user_id": user["id"], "created_at": stamp}},
            upsert=True
        )

        audit(db, "profile_record_added", user["id"], "candidate", user["id"], {"section": section, "record_id": item["id"]})
        return clean(item)

    @router.delete("/candidates/me/{section}/{record_id}")
    def delete_profile_record(section: str, record_id: str, token: str):
        user = require_session(token)
        valid_sections = {"experience", "education", "projects", "certifications", "languages"}
        if section not in valid_sections:
            raise HTTPException(404, "Profile section not found.")

        cand_profile = db.candidate_profiles.find_one({"$or": [{"id": user["id"]}, {"user_id": user["id"]}]}) or {}
        section_list = cand_profile.get(section, [])
        new_list = [item for item in section_list if not (item.get("id") == record_id and item.get("source") == "candidate_manual")]

        if len(new_list) == len(section_list):
            raise HTTPException(404, "Editable profile record not found.")

        db.candidate_profiles.update_one(
            {"$or": [{"id": user["id"]}, {"user_id": user["id"]}]},
            {"$set": {section: new_list, "updated_at": utcnow()}}
        )
        audit(db, "profile_record_deleted", user["id"], "candidate", user["id"], {"section": section, "record_id": record_id})
        return {"ok": True}

    @router.post("/candidates/{candidate_id}/skills")
    def add_skill(candidate_id: str, payload: dict, token: str):
        user = require_session(token)
        if user["role"] == "candidate" and user["id"] != candidate_id:
            raise HTTPException(403, "Not allowed.")
        if user["role"] == "recruiter":
            jobs = [x["id"] for x in db.jobs.find({"recruiterId": user["id"]}, {"id": 1})]
            if not db.applications.find_one({"userId": candidate_id, "jobId": {"$in": jobs}}):
                raise HTTPException(403, "Candidate is not linked to your jobs.")

        skill = str(payload.get("skill", "")).strip()
        if not skill:
            raise HTTPException(422, "skill is required")

        source = "candidate_manual" if user["role"] == "candidate" else "recruiter_manual"
        kind = payload.get("kind", "technical")
        stamp = utcnow()
        item = {
            "id": identifier(),
            "candidate_id": candidate_id,
            "skill": skill,
            "normalized_skill": normalized(skill),
            "kind": kind,
            "source": source,
            "sources": [source],
            "entered_by": user["id"],
            "evidence": [],
            "created_at": stamp,
            "updated_at": stamp
        }

        cand_profile = db.candidate_profiles.find_one({"$or": [{"id": candidate_id}, {"user_id": candidate_id}]}) or {}
        skills_list = [s for s in cand_profile.get("skills", []) if not (normalized(s.get("skill")) == normalized(skill) and s.get("kind") == kind)]
        skills_list.append(item)

        # Update candidate_profiles
        db.candidate_profiles.update_one(
            {"$or": [{"id": candidate_id}, {"user_id": candidate_id}]},
            {"$set": {"skills": skills_list, "updated_at": stamp}, "$setOnInsert": {"id": candidate_id, "user_id": candidate_id, "created_at": stamp}},
            upsert=True
        )

        audit(db, "manual_skill_saved", user["id"], "candidate", candidate_id, {"skill": skill, "source": source})
        return clean(item)

    @router.delete("/candidates/me/skills")
    def delete_own_skill(skill: str, kind: str, token: str):
        """Delete CV-extracted or manually entered skill evidence and synchronize profile views."""
        user = require_session(token)
        if user["role"] != "candidate":
            raise HTTPException(403, "Only candidates can delete their skills.")

        key = normalized(skill)
        kind = normalized(kind)
        if not key or kind not in {"technical", "soft"}:
            raise HTTPException(422, "A valid skill and kind are required.")

        cand_profile = db.candidate_profiles.find_one({"$or": [{"id": user["id"]}, {"user_id": user["id"]}]}) or {}
        original_skills = cand_profile.get("skills", [])
        updated_skills = [s for s in original_skills if not (normalized(s.get("skill")) == key and normalized(s.get("kind")) == kind)]
        deleted_count = len(original_skills) - len(updated_skills)

        tech = [x.strip() for x in str(user.get("technicalSkills") or "").split(",") if x.strip() and normalized(x) != key]
        soft = [x.strip() for x in str(user.get("softSkills") or "").split(",") if x.strip() and normalized(x) != key]
        combined = list(dict.fromkeys([*tech, *soft]))

        # Synchronize users collection
        db.users.update_one({"id": user["id"]}, {"$set": {"technicalSkills": ", ".join(tech), "softSkills": ", ".join(soft), "skills": ", ".join(combined)}})

        profile_tech = [x for x in cand_profile.get("technical_skills", []) if normalized(x) != key]
        programming = [x for x in cand_profile.get("programming_languages", []) if normalized(x) != key]
        profile_soft = [x for x in cand_profile.get("soft_skills", []) if normalized(x) != key]

        db.candidate_profiles.update_one(
            {"$or": [{"id": user["id"]}, {"user_id": user["id"]}]},
            {"$set": {
                "skills": updated_skills,
                "skills_summary.technical_skills": tech,
                "skills_summary.soft_skills": soft,
                "skills_summary.all_skills": combined,
                "technical_skills": profile_tech,
                "programming_languages": programming,
                "soft_skills": profile_soft,
                "updated_at": utcnow()
            }}
        )

        audit(db, "candidate_skill_deleted", user["id"], "candidate", user["id"],
              {"skill": skill, "kind": kind, "structured_records_deleted": deleted_count})
        return {"ok": True, "skill": skill, "kind": kind, "structured_records_deleted": deleted_count,
                "technicalSkills": ", ".join(tech), "softSkills": ", ".join(soft), "skills": ", ".join(combined)}

    @router.get("/candidates/{candidate_id}/github/snapshots")
    def get_github_snapshots(candidate_id: str, token: str):
        user = require_session(token)
        candidate_id = resolve_candidate_id(user, candidate_id)
        snapshots = [clean(x) for x in db.evidence_snapshots.find({"candidate_id": candidate_id, "platform": "github"}).sort("scanned_at", -1)]
        return snapshots

    @router.get("/candidates/{candidate_id}/github/snapshots/{snapshot_id}")
    def get_github_snapshot(candidate_id: str, snapshot_id: str, token: str):
        user = require_session(token)
        candidate_id = resolve_candidate_id(user, candidate_id)
        snapshot = db.evidence_snapshots.find_one({"id": snapshot_id, "candidate_id": candidate_id, "platform": "github"})
        if not snapshot:
            raise HTTPException(404, "GitHub snapshot not found.")
        return clean(snapshot)

    @router.get("/candidates/{candidate_id}/github/compare")
    def compare_snapshots_endpoint(candidate_id: str, from_id: str, to_id: str, token: str):
        user = require_session(token)
        candidate_id = resolve_candidate_id(user, candidate_id)
        snap1 = db.evidence_snapshots.find_one({"id": from_id, "candidate_id": candidate_id, "platform": "github"})
        snap2 = db.evidence_snapshots.find_one({"id": to_id, "candidate_id": candidate_id, "platform": "github"})
        if not snap1 or not snap2:
            raise HTTPException(404, "One or both snapshots were not found.")
        from github_evidence import compare_github_snapshots
        return compare_github_snapshots(snap1, snap2)

    @router.get("/candidates/{candidate_id}/skills/matrix")
    def candidate_skill_matrix(candidate_id: str, token: str):
        user = require_session(token)
        candidate_id = resolve_candidate_id(user, candidate_id)

        candidate_user = db.users.find_one(
            {"id": candidate_id},
            {"technicalSkills": 1, "linkedinUrl": 1, "portfolioUrl": 1},
        ) or {}
        candidate_profile = db.candidate_profiles.find_one({"$or": [{"id": candidate_id}, {"user_id": candidate_id}]}) or {}
        social_links = candidate_profile.get("social_links") or {}
        portfolio_url = candidate_user.get("portfolioUrl") or social_links.get("portfolio_url")
        linkedin_url = candidate_user.get("linkedinUrl") or social_links.get("linkedin_url")

        skills = candidate_profile.get("skills", [])
        experience_items = candidate_profile.get("experience", [])
        project_items = candidate_profile.get("projects", [])

        # Fetch latest snapshots from evidence_snapshots
        latest_github = db.evidence_snapshots.find_one({"candidate_id": candidate_id, "platform": "github"}, sort=[("scanned_at", -1)]) or candidate_profile.get("github") or {}
        latest_portfolio = db.evidence_snapshots.find_one({"candidate_id": candidate_id, "platform": "portfolio"}, sort=[("verified_at", -1)]) or {}
        portfolio_skill_items = {normalized(item.get("skill")): item for item in latest_portfolio.get("matched_skills", [])}
        github_skill_items = {s.get("skill", "").casefold(): s for s in latest_github.get("skill_evidence", [])}

        all_skill_names = []
        seen_skill_names = set()
        for raw_name in str(candidate_user.get("technicalSkills") or "").split(","):
            name = raw_name.strip()
            key = normalized(name)
            if name and key not in seen_skill_names:
                seen_skill_names.add(key)
                all_skill_names.append(name)

        matrix = []
        for name in all_skill_names:
            key = normalized(name)
            cv_ev = any(normalized(s.get("skill")) == key and s.get("source") in {"cv", "cv_gemini", "candidate_manual"} for s in skills)
            exp_ev = any(any(normalized(t) == key for t in exp.get("technologies", [])) for exp in experience_items)
            proj_ev = any(any(normalized(t) == key for t in proj.get("technologies", [])) for proj in project_items)

            g_match = None
            for g_k, g_data in github_skill_items.items():
                if g_k == key or (min(len(key), len(g_k)) >= 3 and (key in g_k or g_k in key)):
                    g_match = g_data
                    break
            portfolio_match = portfolio_skill_items.get(key)

            sources = []
            if cv_ev:
                sources.append("CV")
            if exp_ev:
                sources.append("Experience")
            if proj_ev:
                sources.append("Projects")
            if portfolio_match:
                sources.append("Portfolio")
            if linkedin_url:
                sources.append("LinkedIn")
            if g_match:
                sources.append("GitHub")

            matrix.append({
                "skill": name,
                "normalized_skill": key,
                "sources": sources,
                "cv_evidence": cv_ev or (not exp_ev and not proj_ev and not g_match),
                "experience_evidence": exp_ev,
                "projects_evidence": proj_ev,
                "github_evidence": g_match is not None,
                "github_status": "verified" if g_match else "not_verified_from_github",
                "github_details": g_match,
                "portfolio_evidence": portfolio_match is not None,
                "portfolio_url": portfolio_url,
                "portfolio_details": portfolio_match,
                "linkedin_evidence": bool(linkedin_url),
                "linkedin_url": linkedin_url,
            })
        return matrix

    @router.get("/applications/{application_id}/evaluations")
    def get_application_evaluations(application_id: str, token: str):
        user = require_session(token)
        app = get_application(user, application_id)
        evaluations = app.get("ai_evaluations") or []
        if not evaluations and app.get("enterpriseEvaluation"):
            evaluations = [{
                "application_id": application_id,
                "scores": app.get("scores", {}),
                "enterpriseEvaluation": app.get("enterpriseEvaluation"),
                "created_at": app.get("appliedAt"),
            }]
        return [clean(x) for x in evaluations]

    @router.post("/applications/{application_id}/interviews")
    def interview(application_id: str, payload: dict, token: str):
        user = require_session(token)
        app = get_application(user, application_id)
        if user["role"] != "recruiter":
            raise HTTPException(403, "Only recruiters can record interviews.")
        job = db.jobs.find_one({"id": app["jobId"]})
        maximum = ScoreWeights.model_validate(job.get("scoring_weights", DEFAULT_WEIGHTS)).structured_interview
        try:
            if payload.get("scorecard"):
                stage = score_interview(payload["scorecard"], maximum)
            else:
                old = float(payload.get("final_interview_score", 0))
                stage = normalized_stage(old / maximum * 100 if maximum else 0, maximum)
        except (TypeError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc

        existing_interviews = app.get("interviews_history", [])
        version = len(existing_interviews) + 1
        item = {
            **payload,
            **stage,
            "id": identifier(),
            "application_id": application_id,
            "interviewer_id": user["id"],
            "interview_scorecard_version": version,
            "created_at": utcnow()
        }

        db.applications.update_one(
            {"id": application_id},
            {
                "$set": {"structured_interview": item, "interview_score": item.get("weighted_score", 0)},
                "$push": {"interviews_history": item}
            }
        )
        audit(db, "structured_interview_saved", user["id"], "application", application_id, {"interview_id": item["id"], "version": version})
        return clean(item)

    @router.post("/applications/{application_id}/technical-assessments")
    def technical_assessment(application_id: str, payload: dict, token: str):
        user = require_session(token)
        app = get_application(user, application_id)
        if user["role"] != "recruiter":
            raise HTTPException(403, "Only recruiters can record technical assessments.")
        job = db.jobs.find_one({"id": app["jobId"]})
        maximum = ScoreWeights.model_validate(job.get("scoring_weights", DEFAULT_WEIGHTS)).technical_assessment
        try:
            stage = normalized_stage(payload.get("normalized_percentage", payload.get("raw_score")), maximum)
        except (TypeError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc

        existing_assessments = app.get("technical_assessments_history", [])
        version = len(existing_assessments) + 1
        item = {
            **payload,
            **stage,
            "id": identifier(),
            "application_id": application_id,
            "assessment_version": version,
            "recorded_by": user["id"],
            "created_at": utcnow()
        }

        db.applications.update_one(
            {"id": application_id},
            {
                "$set": {"technical_assessment": item, "assessment_score": item.get("weighted_score", 0)},
                "$push": {"technical_assessments_history": item}
            }
        )
        audit(db, "technical_assessment_saved", user["id"], "application", application_id, {"assessment_id": item["id"], "version": version})
        return clean(item)

    @router.post("/applications/{application_id}/overrides")
    def override(application_id: str, payload: dict, token: str):
        user = require_session(token)
        app = get_application(user, application_id)
        if user["role"] != "recruiter":
            raise HTTPException(403, "Only recruiters can override scores.")
        category = payload.get("category")
        reason = str(payload.get("override_reason", "")).strip()

        original = app.get("scores", {}).get(category, {})
        if category not in AI_CATEGORIES or not reason:
            raise HTTPException(422, "Valid category and override reason are required.")
        maximum = float(original.get("maximum_score", 0))
        score = float(payload.get("recruiter_score", -1))
        if not 0 <= score <= maximum:
            raise HTTPException(422, f"Recruiter score must be between 0 and {maximum}.")

        item = {
            "id": identifier(),
            "application_id": application_id,
            "category": category,
            "ai_score": original.get("weighted_score"),
            "recruiter_score": score,
            "override": True,
            "override_reason": reason,
            "updated_by": user["id"],
            "updated_at": utcnow()
        }

        overrides = [o for o in app.get("score_overrides", []) if o.get("category") != category]
        overrides.append(item)

        db.applications.update_one({"id": application_id}, {"$set": {"score_overrides": overrides}})
        audit(db, "score_overridden", user["id"], "application", application_id, {"override_id": item["id"], "category": category})
        return clean(item)

    @router.get("/applications/{application_id}/assessment")
    def assessment(application_id: str, token: str):
        user = require_session(token)
        app = get_application(user, application_id)

        evaluation = app.get("enterpriseEvaluation") or {}
        meeting = app.get("structured_interview")
        technical = app.get("technical_assessment")
        job = db.jobs.find_one({"id": app["jobId"]}) or {}
        weights = ScoreWeights.model_validate(job.get("scoring_weights", DEFAULT_WEIGHTS))

        overrides = [clean(x) for x in app.get("score_overrides", [])]
        scores = app.get("scores", {})
        profile = profile_totals(scores, weights)
        effective = profile["score"]
        latest = {}
        for item in overrides:
            latest[item["category"]] = item
        for item in latest.values():
            effective += item["recruiter_score"] - float(item.get("ai_score") or 0)

        profile["score"] = round(effective, 2)
        profile["normalized_percentage"] = round(effective / profile["maximum"] * 100, 2) if profile["maximum"] else 0
        complete = bool(technical and meeting)
        final = effective + float((technical or {}).get("weighted_score", 0)) + float((meeting or {}).get("weighted_score", 0))

        decision = app.get("final_decision") or app.get("finalDecision") or pending_decision()
        cand_id = app.get("userId") or app.get("candidateId")
        candidate_profile = db.candidate_profiles.find_one({"$or": [{"id": cand_id}, {"user_id": cand_id}]}) or {}
        candidate = {
            "skills": candidate_profile.get("skills", []),
            "experience": candidate_profile.get("experience", []),
            "projects": candidate_profile.get("projects", []),
            "education": candidate_profile.get("education", []),
            "certifications": candidate_profile.get("certifications", []),
            "languages": candidate_profile.get("languages", [])
        }
        eligibility = evaluate_eligibility(candidate, job.get("must_have_requirements", []))

        return {
            "application": clean(app),
            "stage": "recruiter_review" if complete else "in_progress",
            "eligibility": eligibility,
            "ai_evaluation": clean(evaluation),
            "profile": profile,
            "technical_assessment": clean(technical) or {"status": "pending", "max_score": weights.technical_assessment},
            "structured_interview": clean(meeting) or {"status": "pending", "max_score": weights.structured_interview},
            "overrides": overrides,
            "pre_interview_score": profile["score"],
            "final_score": round(final, 2) if complete else None,
            "match_assessment": recommendation(final, job.get("recommendation_bands", DEFAULT_BANDS)) if complete else recommendation(profile["normalized_percentage"], job.get("recommendation_bands", DEFAULT_BANDS)),
            "final_decision": clean(decision),
            "disclaimer": "AI-Assisted Match Assessment. A human makes the final hiring decision."
        }

    @router.post("/applications/{application_id}/decision")
    def final_decision(application_id: str, payload: dict, token: str):
        user = require_session(token)
        app = get_application(user, application_id)
        if user["role"] != "recruiter":
            raise HTTPException(403, "Only authorized recruiters can make a final decision.")

        decision = payload.get("decision")
        reason = str(payload.get("reason", "")).strip()
        if decision not in DECISIONS or not reason:
            raise HTTPException(422, "A valid human decision and reason are required.")

        item = {
            "id": identifier(),
            "application_id": application_id,
            "status": "completed",
            "decision": decision,
            "decision_by": user["id"],
            "reason": reason,
            "decided_at": utcnow()
        }

        db.applications.update_one(
            {"id": application_id},
            {"$set": {"final_decision": item, "finalDecision": item, "status": f"Decision: {decision}"}}
        )
        audit(db, "final_human_decision", user["id"], "application", application_id, {"decision_id": item["id"], "decision": decision})
        return clean(item)

    return router
