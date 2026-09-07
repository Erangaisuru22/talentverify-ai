from fastapi import APIRouter, HTTPException
from database import db
from domain import AI_CATEGORIES, DEFAULT_WEIGHTS, PROFILE_CATEGORIES, ScoreWeights, audit, duration_months, identifier, normalized, utcnow
from enterprise_evaluation import (DECISIONS, DEFAULT_BANDS, evaluate_eligibility, normalized_stage,
                                   pending_decision, profile_totals, recommendation, score_interview)

def clean(value): return {k: v for k, v in value.items() if k != "_id"} if value else None

def deduplicated(records, key_fields):
    """Return one UI record per normalized identity while preserving every source."""
    merged = {}
    for raw in records:
        item = clean(raw); key = "|".join(normalized(item.get(field)) for field in key_fields)
        if not key.strip("|"): key = item.get("id", "")
        if key not in merged:
            item["sources"] = [item.get("source")] if item.get("source") else []
            merged[key] = item; continue
        current = merged[key]
        if item.get("source") and item["source"] not in current["sources"]: current["sources"].append(item["source"])
        for field, value in item.items():
            if field in {"_id", "source", "sources"}: continue
            if isinstance(value, list):
                existing = current.get(field) if isinstance(current.get(field), list) else []
                current[field] = list(dict.fromkeys([*existing, *value]))
            elif value not in (None, "", 0, False) and current.get(field) in (None, "", 0, False): current[field] = value
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
        if not item: raise HTTPException(404, "Application not found.")
        if user["role"] == "candidate" and item.get("userId") != user["id"]: raise HTTPException(404, "Application not found.")
        if user["role"] == "recruiter" and not db.jobs.find_one({"id": item["jobId"], "recruiterId": user["id"]}): raise HTTPException(404, "Application not found.")
        return item

    @router.get("/candidates/me/structured")
    def structured_profile(token: str):
        user = require_session(token); cid = user["id"]
        return {
            "candidate": clean(db.candidates.find_one({"id": cid})),
            "skills": deduplicated(db.candidate_skills.find({"candidate_id": cid}), ("normalized_skill", "kind")),
            "experience": deduplicated(db.candidate_experience.find({"candidate_id": cid}), ("company", "position", "start_date")),
            "projects": deduplicated(db.candidate_projects.find({"candidate_id": cid}), ("name",)),
            "education": deduplicated(db.candidate_education.find({"candidate_id": cid}), ("qualification", "institution", "field")),
            "certifications": deduplicated(db.candidate_certifications.find({"candidate_id": cid}), ("name", "issuer")),
            "languages": deduplicated(db.candidate_languages.find({"candidate_id": cid}), ("language",)),
            "cv_analyses": [clean(x) for x in db.cv_documents.find({"candidate_id": cid}, {"_id": 0, "content": 0, "raw_gemini_result": 0}).sort("uploaded_at", -1)],
            "github": clean(db.candidate_github.find_one({"candidate_id": cid})),
            "linkedin": clean(db.linkedin_evidence_snapshots.find_one({"candidate_id": cid}, sort=[("verified_at", -1)])),
            "linkedin_history": [clean(x) for x in db.linkedin_evidence_snapshots.find(
                {"candidate_id": cid}).sort("verified_at", -1).limit(10)],
            "portfolio": clean(db.portfolio_evidence_snapshots.find_one({"candidate_id": cid}, sort=[("verified_at", -1)]))
        }

    @router.post("/candidates/me/{section}")
    def add_profile_record(section: str, payload: dict, token: str):
        user = require_session(token)
        if user["role"] != "candidate": raise HTTPException(403, "Only candidates can edit profile records.")
        collections = {
            "experience": "candidate_experience",
            "education": "candidate_education",
            "projects": "candidate_projects",
            "certifications": "candidate_certifications",
            "languages": "candidate_languages",
        }
        required = {
            "experience": "company",
            "education": "qualification",
            "projects": "name",
            "certifications": "name",
            "languages": "language",
        }
        if section not in collections: raise HTTPException(404, "Profile section not found.")
        value = str(payload.get(required[section], "")).strip()
        if not value: raise HTTPException(422, f"{required[section]} is required")
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

        existing = db[collections[section]].find_one({"candidate_id": user["id"], **identity})
        prior_source = (existing or {}).get("source")
        sources = list(dict.fromkeys([*((existing or {}).get("sources") or ([prior_source] if prior_source else [])), "candidate_manual"]))
        item.update({
            "id": (existing or {}).get("id", identifier()),
            "candidate_id": user["id"],
            "source": "candidate_manual",
            "sources": sources,
            "confidence": 1.0,
            "updated_at": utcnow()
        })
        if not existing: item["created_at"] = utcnow()
        db[collections[section]].update_one({"candidate_id": user["id"], **identity}, {"$set": item}, upsert=True)
        audit(db, "profile_record_added", user["id"], "candidate", user["id"], {"section": section, "record_id": item["id"]})
        return clean(item)

    @router.delete("/candidates/me/{section}/{record_id}")
    def delete_profile_record(section: str, record_id: str, token: str):
        user = require_session(token)
        collections = {
            "experience": "candidate_experience",
            "education": "candidate_education",
            "projects": "candidate_projects",
            "certifications": "candidate_certifications",
            "languages": "candidate_languages",
        }
        if section not in collections: raise HTTPException(404, "Profile section not found.")
        result = db[collections[section]].delete_one({"id": record_id, "candidate_id": user["id"], "source": "candidate_manual"})
        if not result.deleted_count: raise HTTPException(404, "Editable profile record not found.")
        audit(db, "profile_record_deleted", user["id"], "candidate", user["id"], {"section": section, "record_id": record_id})
        return {"ok": True}

    @router.post("/candidates/{candidate_id}/skills")
    def add_skill(candidate_id: str, payload: dict, token: str):
        user = require_session(token)
        if user["role"] == "candidate" and user["id"] != candidate_id: raise HTTPException(403, "Not allowed.")
        if user["role"] == "recruiter":
            jobs = [x["id"] for x in db.jobs.find({"recruiterId": user["id"]}, {"id": 1})]
            if not db.applications.find_one({"userId": candidate_id, "jobId": {"$in": jobs}}): raise HTTPException(403, "Candidate is not linked to your jobs.")
        skill = str(payload.get("skill", "")).strip()
        if not skill: raise HTTPException(422, "skill is required")
        source = "candidate_manual" if user["role"] == "candidate" else "recruiter_manual"
        item = {"id": identifier(), "candidate_id": candidate_id, "skill": skill, "normalized_skill": normalized(skill), "kind": payload.get("kind", "technical"), "source": source, "entered_by": user["id"], "evidence": [], "created_at": utcnow()}
        db.candidate_skills.update_one({"candidate_id": candidate_id, "normalized_skill": item["normalized_skill"], "source": source}, {"$set": item}, upsert=True)
        audit(db, "manual_skill_saved", user["id"], "candidate", candidate_id, {"skill": skill, "source": source})
        return clean(item)

    @router.delete("/candidates/me/skills")
    def delete_own_skill(skill: str, kind: str, token: str):
        """Delete CV-extracted or manually entered skill evidence and synchronize profile views."""
        user = require_session(token)
        if user["role"] != "candidate": raise HTTPException(403, "Only candidates can delete their skills.")
        key = normalized(skill); kind = normalized(kind)
        if not key or kind not in {"technical", "soft"}: raise HTTPException(422, "A valid skill and kind are required.")
        result = db.candidate_skills.delete_many({"candidate_id": user["id"], "normalized_skill": key, "kind": kind})

        tech = [x.strip() for x in str(user.get("technicalSkills") or "").split(",") if x.strip() and normalized(x) != key]
        soft = [x.strip() for x in str(user.get("softSkills") or "").split(",") if x.strip() and normalized(x) != key]
        combined = list(dict.fromkeys([*tech, *soft]))
        db.users.update_one({"id": user["id"]}, {"$set": {"technicalSkills": ", ".join(tech), "softSkills": ", ".join(soft), "skills": ", ".join(combined)}})

        candidate_update = {"skills_summary.technical_skills": tech, "skills_summary.soft_skills": soft,
                            "skills_summary.all_skills": combined, "updated_at": utcnow()}
        db.candidates.update_one({"id": user["id"]}, {"$set": candidate_update})
        profile = db.candidate_profiles.find_one({"id": user["id"]}) or {}
        profile_tech = [x for x in profile.get("technical_skills", []) if normalized(x) != key]
        programming = [x for x in profile.get("programming_languages", []) if normalized(x) != key]
        profile_soft = [x for x in profile.get("soft_skills", []) if normalized(x) != key]
        db.candidate_profiles.update_one({"id": user["id"]}, {"$set": {"technical_skills": profile_tech,
            "programming_languages": programming, "soft_skills": profile_soft, "updated_at": utcnow()}})
        audit(db, "candidate_skill_deleted", user["id"], "candidate", user["id"],
              {"skill": skill, "kind": kind, "structured_records_deleted": result.deleted_count})
        return {"ok": True, "skill": skill, "kind": kind, "structured_records_deleted": result.deleted_count,
                "technicalSkills": ", ".join(tech), "softSkills": ", ".join(soft), "skills": ", ".join(combined)}

    @router.get("/candidates/{candidate_id}/github/snapshots")
    def get_github_snapshots(candidate_id: str, token: str):
        user = require_session(token)
        candidate_id = resolve_candidate_id(user, candidate_id)
        snapshots = [clean(x) for x in db.github_evidence_snapshots.find({"candidate_id": candidate_id}).sort("scanned_at", -1)]
        return snapshots

    @router.get("/candidates/{candidate_id}/github/snapshots/{snapshot_id}")
    def get_github_snapshot(candidate_id: str, snapshot_id: str, token: str):
        user = require_session(token)
        candidate_id = resolve_candidate_id(user, candidate_id)
        snapshot = db.github_evidence_snapshots.find_one({"id": snapshot_id, "candidate_id": candidate_id})
        if not snapshot:
            raise HTTPException(404, "GitHub snapshot not found.")
        return clean(snapshot)

    @router.get("/candidates/{candidate_id}/github/compare")
    def compare_snapshots_endpoint(candidate_id: str, from_id: str, to_id: str, token: str):
        user = require_session(token)
        candidate_id = resolve_candidate_id(user, candidate_id)
        snap1 = db.github_evidence_snapshots.find_one({"id": from_id, "candidate_id": candidate_id})
        snap2 = db.github_evidence_snapshots.find_one({"id": to_id, "candidate_id": candidate_id})
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
        candidate_profile = db.candidate_profiles.find_one({"id": candidate_id}, {"social_links": 1}) or {}
        social_links = candidate_profile.get("social_links") or {}
        portfolio_url = candidate_user.get("portfolioUrl") or social_links.get("portfolio_url")
        linkedin_url = candidate_user.get("linkedinUrl") or social_links.get("linkedin_url")
        skills = list(db.candidate_skills.find({"candidate_id": candidate_id}))
        experience_items = list(db.candidate_experience.find({"candidate_id": candidate_id}))
        project_items = list(db.candidate_projects.find({"candidate_id": candidate_id}))
        latest_github = db.candidate_github.find_one({"candidate_id": candidate_id}) or {}
        latest_portfolio = db.portfolio_evidence_snapshots.find_one({"candidate_id": candidate_id}, sort=[("verified_at", -1)]) or {}
        portfolio_skill_items = {normalized(item.get("skill")): item for item in latest_portfolio.get("matched_skills", [])}
        github_skill_items = {s.get("skill", "").casefold(): s for s in latest_github.get("skill_evidence", [])}

        # Matrix rows represent only skills explicitly saved on the profile.
        # Other sources may confirm a row, but may never create extra rows.
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
            
            # Check GitHub evidence
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
        get_application(user, application_id)
        evaluations = [clean(x) for x in db.ai_evaluations.find({"application_id": application_id}).sort("created_at", -1)]
        return evaluations

    @router.post("/applications/{application_id}/interviews")
    def interview(application_id: str, payload: dict, token: str):
        user = require_session(token); app = get_application(user, application_id)
        if user["role"] != "recruiter": raise HTTPException(403, "Only recruiters can record interviews.")
        job = db.jobs.find_one({"id": app["jobId"]}); maximum = ScoreWeights.model_validate(job.get("scoring_weights", DEFAULT_WEIGHTS)).structured_interview
        try:
            if payload.get("scorecard"):
                stage = score_interview(payload["scorecard"], maximum)
            else: # compatibility with the old marks input
                old = float(payload.get("final_interview_score", 0)); stage = normalized_stage(old / maximum * 100 if maximum else 0, maximum)
        except (TypeError, ValueError) as exc: raise HTTPException(422, str(exc)) from exc
        version = db.interviews.count_documents({"application_id": application_id}) + 1
        item = {**payload, **stage, "id": identifier(), "application_id": application_id, "interviewer_id": user["id"],
                "interview_scorecard_version": version, "created_at": utcnow()}
        db.interviews.insert_one(item); audit(db, "structured_interview_saved", user["id"], "application", application_id, {"interview_id": item["id"], "version": version}); return clean(item)

    @router.post("/applications/{application_id}/technical-assessments")
    def technical_assessment(application_id: str, payload: dict, token: str):
        user = require_session(token); app = get_application(user, application_id)
        if user["role"] != "recruiter": raise HTTPException(403, "Only recruiters can record technical assessments.")
        job = db.jobs.find_one({"id": app["jobId"]}); maximum = ScoreWeights.model_validate(job.get("scoring_weights", DEFAULT_WEIGHTS)).technical_assessment
        try: stage = normalized_stage(payload.get("normalized_percentage", payload.get("raw_score")), maximum)
        except (TypeError, ValueError) as exc: raise HTTPException(422, str(exc)) from exc
        version = db.technical_assessments.count_documents({"application_id": application_id}) + 1
        item = {**payload, **stage, "id": identifier(), "application_id": application_id, "assessment_version": version,
                "recorded_by": user["id"], "created_at": utcnow()}
        db.technical_assessments.insert_one(item); audit(db, "technical_assessment_saved", user["id"], "application", application_id, {"assessment_id": item["id"], "version": version}); return clean(item)

    @router.post("/applications/{application_id}/overrides")
    def override(application_id: str, payload: dict, token: str):
        user = require_session(token); app = get_application(user, application_id)
        if user["role"] != "recruiter": raise HTTPException(403, "Only recruiters can override scores.")
        category = payload.get("category"); reason = str(payload.get("override_reason", "")).strip()
        evaluation = db.ai_evaluations.find_one({"application_id": application_id}, sort=[("created_at", -1)]) or {}
        original = evaluation.get("scores", app.get("scores", {})).get(category, {})
        if category not in AI_CATEGORIES or not reason: raise HTTPException(422, "Valid category and override reason are required.")
        maximum = float(original.get("maximum_score", 0)); score = float(payload.get("recruiter_score", -1))
        if not 0 <= score <= maximum: raise HTTPException(422, f"Recruiter score must be between 0 and {maximum}.")
        item = {"id": identifier(), "application_id": application_id, "category": category, "ai_score": original.get("weighted_score"), "recruiter_score": score, "override": True, "override_reason": reason, "updated_by": user["id"], "updated_at": utcnow()}
        db.score_overrides.insert_one(item)
        audit(db, "score_overridden", user["id"], "application", application_id, {"override_id": item["id"], "category": category}); return clean(item)

    @router.get("/applications/{application_id}/assessment")
    def assessment(application_id: str, token: str):
        user = require_session(token); app = get_application(user, application_id)
        evaluation = db.ai_evaluations.find_one({"application_id": application_id}, sort=[("created_at", -1)]); meeting = db.interviews.find_one({"application_id": application_id}, sort=[("created_at", -1)])
        technical = db.technical_assessments.find_one({"application_id": application_id}, sort=[("created_at", -1)])
        job = db.jobs.find_one({"id": app["jobId"]}) or {}; weights = ScoreWeights.model_validate(job.get("scoring_weights", DEFAULT_WEIGHTS))
        overrides = [clean(x) for x in db.score_overrides.find({"application_id": application_id}).sort("updated_at", 1)]
        scores = (evaluation or {}).get("scores", app.get("scores", {})); profile = profile_totals(scores, weights); effective = profile["score"]; latest = {}
        for item in overrides: latest[item["category"]] = item
        for item in latest.values(): effective += item["recruiter_score"] - float(item.get("ai_score") or 0)
        profile["score"] = round(effective, 2); profile["normalized_percentage"] = round(effective / profile["maximum"] * 100, 2) if profile["maximum"] else 0
        complete = bool(technical and meeting); final = effective + float((technical or {}).get("weighted_score", 0)) + float((meeting or {}).get("weighted_score", 0))
        decision = db.final_decisions.find_one({"application_id": application_id}, sort=[("decided_at", -1)]) or app.get("finalDecision") or pending_decision()
        candidate = {"skills": list(db.candidate_skills.find({"candidate_id": app["userId"]})), "experience": list(db.candidate_experience.find({"candidate_id": app["userId"]})), "projects": list(db.candidate_projects.find({"candidate_id": app["userId"]})), "education": list(db.candidate_education.find({"candidate_id": app["userId"]})), "certifications": list(db.candidate_certifications.find({"candidate_id": app["userId"]})), "languages": list(db.candidate_languages.find({"candidate_id": app["userId"]}))}
        eligibility = evaluate_eligibility(candidate, job.get("must_have_requirements", []))
        return {"application": clean(app), "stage": "recruiter_review" if complete else "in_progress", "eligibility": eligibility,
                "ai_evaluation": clean(evaluation), "profile": profile, "technical_assessment": clean(technical) or {"status": "pending", "max_score": weights.technical_assessment},
                "structured_interview": clean(meeting) or {"status": "pending", "max_score": weights.structured_interview}, "overrides": overrides,
                "pre_interview_score": profile["score"], "final_score": round(final, 2) if complete else None,
                "match_assessment": recommendation(final, job.get("recommendation_bands", DEFAULT_BANDS)) if complete else recommendation(profile["normalized_percentage"], job.get("recommendation_bands", DEFAULT_BANDS)),
                "final_decision": clean(decision), "disclaimer": "AI-Assisted Match Assessment. A human makes the final hiring decision."}

    @router.post("/applications/{application_id}/decision")
    def final_decision(application_id: str, payload: dict, token: str):
        user = require_session(token); get_application(user, application_id)
        if user["role"] != "recruiter": raise HTTPException(403, "Only authorized recruiters can make a final decision.")
        decision = payload.get("decision"); reason = str(payload.get("reason", "")).strip()
        if decision not in DECISIONS or not reason: raise HTTPException(422, "A valid human decision and reason are required.")
        item = {"id": identifier(), "application_id": application_id, "status": "completed", "decision": decision,
                "decision_by": user["id"], "reason": reason, "decided_at": utcnow()}
        db.final_decisions.insert_one(item); db.applications.update_one({"id": application_id}, {"$set": {"finalDecision": item}})
        audit(db, "final_human_decision", user["id"], "application", application_id, {"decision_id": item["id"], "decision": decision}); return clean(item)
    return router
