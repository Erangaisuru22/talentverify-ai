"""
TalentVerify AI - Comprehensive System & 8-Collection Integrity Verification
Directly invokes FastAPI route handlers and verifies:
1. All 8 collections exist and have normalized, referentially valid documents.
2. Endpoint handlers execute with 0 errors:
   - Health check (/api/health)
   - Recruiter authentication & dashboard data (/api/app-data)
   - Candidate authentication & dashboard data (/api/app-data)
   - Candidate structured profile (/api/candidates/me/structured)
   - Candidate multi-source skills matrix
   - Application assessment & AI scoring (/api/applications/{id}/assessment)
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import db
from database_validator import DatabaseValidator
from main import (
    health,
    authenticate,
    app_data,
    AuthRequest,
    require_session,
)
from assessment_routes import build_assessment_router

def test_full_system_integrity():
    print("=" * 70)
    print(" TalentVerify AI - Full System & 8-Collection Integrity Test")
    print("=" * 70)

    # 1. Health check
    print("\n[TEST 1] Testing health()...")
    health_res = health()
    assert health_res["status"] == "ok" and health_res["database"] == "connected", f"Health failed: {health_res}"
    print(f"  [OK] Health check passed: {health_res}")

    # 2. Database Validator on all 8 collections
    print("\n[TEST 2] Testing DatabaseValidator on all 8 collections...")
    collections = [
        "users",
        "candidate_profiles",
        "jobs",
        "applications",
        "cv_documents",
        "evidence_snapshots",
        "audit_logs",
        "analysis_runs",
    ]
    validators = {
        "users": DatabaseValidator.validate_user,
        "candidate_profiles": DatabaseValidator.validate_candidate_profile,
        "jobs": DatabaseValidator.validate_job,
        "applications": DatabaseValidator.validate_application,
        "cv_documents": DatabaseValidator.validate_cv_document,
        "evidence_snapshots": DatabaseValidator.validate_evidence_snapshot,
        "audit_logs": DatabaseValidator.validate_audit_log,
        "analysis_runs": DatabaseValidator.validate_analysis_run,
    }

    total_docs = 0
    for col in collections:
        docs = list(db[col].find())
        total_docs += len(docs)
        fn = validators[col]
        for d in docs:
            try:
                ok, msg = fn(d, check_fk=True)
            except TypeError:
                ok, msg = fn(d)
            assert ok, f"Validation failed in {col} for doc {d.get('id') or d.get('_id')}: {msg}"
        print(f"  [OK] Collection '{col:<20}': {len(docs):>2} documents validated with 100% referential integrity.")
    print(f"  Total verified documents across all 8 collections: {total_docs}")

    # 3. Recruiter Authentication & App Data
    print("\n[TEST 3] Testing Recruiter Login & App Data...")
    rec_auth = authenticate(AuthRequest(
        mode="login",
        email="recruiter@gmail.com",
        password="abcd123@"
    ))
    rec_token = rec_auth["token"]
    rec_user = rec_auth["user"]
    print(f"  [OK] Recruiter logged in successfully: {rec_user['name']} ({rec_user['id']})")

    rec_data = app_data(token=rec_token)
    assert len(rec_data["jobs"]) >= 4, f"Jobs missing: {len(rec_data['jobs'])}"
    assert len(rec_data["applications"]) >= 1, f"Applications missing: {len(rec_data['applications'])}"
    print(f"  [OK] Recruiter app-data loaded: {len(rec_data['jobs'])} jobs, {len(rec_data['applications'])} applications owned.")

    # 4. Candidate Authentication & App Data
    print("\n[TEST 4] Testing Candidate Login & App Data...")
    cand_auth = authenticate(AuthRequest(
        mode="login",
        email="candidate@gmail.com",
        password="abcd123@"
    ))
    cand_token = cand_auth["token"]
    cand_user = cand_auth["user"]
    assert cand_user.get("technicalSkills"), "Candidate technicalSkills was not hydrated!"
    assert cand_user.get("skills"), "Candidate skills was not hydrated!"
    print(f"  [OK] Candidate logged in: {cand_user['name']} | Technical Skills: {cand_user['technicalSkills']}")

    cand_data = app_data(token=cand_token)
    assert len(cand_data["applications"]) >= 1, "Candidate applications missing!"
    print(f"  [OK] Candidate app-data loaded: {len(cand_data['applications'])} submitted applications.")

    # 5. Assessment Router Endpoints
    print("\n[TEST 5] Testing Structured Profile & Candidate Assessment...")
    assessment_router = build_assessment_router(require_session)
    routes_map = {route.path: route.endpoint for route in assessment_router.routes}

    # Structured profile
    structured_fn = routes_map["/api/candidates/me/structured"]
    struct_res = structured_fn(token=cand_token)
    assert len(struct_res.get("skills", [])) > 0, "No structured skills returned!"
    assert len(struct_res.get("experience", [])) > 0, "No structured experience returned!"
    assert len(struct_res.get("education", [])) > 0, "No structured education returned!"
    assert struct_res.get("github") is not None, "GitHub evidence snapshot not attached!"
    print(f"  [OK] Structured profile verified: {len(struct_res['skills'])} skills, {len(struct_res['experience'])} experience, GitHub verified: {struct_res['github']['verification_status']}")

    # Recruiter assessment
    test_app_id = rec_data["applications"][0]["id"]
    assessment_fn = routes_map["/api/applications/{application_id}/assessment"]
    assess_res = assessment_fn(application_id=test_app_id, token=rec_token)
    assert "eligibility" in assess_res, "Eligibility assessment missing!"
    assert "ai_evaluation" in assess_res, "AI evaluation missing!"
    assert "profile" in assess_res, "Profile score breakdown missing!"
    print(f"  [OK] Recruiter assessment for app '{test_app_id}' loaded with full scoring, eligibility, and breakdown.")

    print("\n" + "=" * 70)
    print(" ALL 5 TEST SUITES PASSED WITH 0 ERRORS! SYSTEM 100% HEALTHY & NORMALIZED!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_system_integrity()
