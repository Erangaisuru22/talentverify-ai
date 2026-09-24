"""MongoDB repository for candidate and application evaluations using candidate_profiles and applications."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pymongo.database import Database


def utcnow():
    return datetime.now(timezone.utc)


class AnalysisRepository:
    def __init__(self, db: Database):
        self.db = db

    def ensure_indexes(self):
        # All evaluation data is embedded in applications and candidate_profiles
        pass

    def record_analysis_run(self, run_doc: Dict[str, Any]) -> Dict[str, Any]:
        stamp = utcnow()
        candidate_id = run_doc.get("candidate_id")
        app_id = run_doc.get("application_id")
        job_id = run_doc.get("job_id")

        # If related to an application, embed into applications
        if app_id:
            self.db.applications.update_one(
                {"id": app_id},
                {
                    "$set": {
                        "latest_analysis_run_id": run_doc.get("id"),
                        "analysis_timestamp": stamp,
                        "jobMatchScore": run_doc.get("job_match_score"),
                        "candidateProfileScore": run_doc.get("candidate_profile_score"),
                        "individual_score_components": run_doc.get("individual_score_components"),
                    },
                    "$push": {
                        "analysis_history": {
                            "$each": [run_doc],
                            "$slice": -10  # Keep last 10 evaluation runs
                        }
                    }
                }
            )

        # Update candidate profile scores inside candidate_profiles
        if candidate_id and "candidate_profile_score" in run_doc:
            self.db.candidate_profiles.update_one(
                {"$or": [{"id": candidate_id}, {"user_id": candidate_id}]},
                {
                    "$set": {
                        "candidate_profile_score": run_doc.get("candidate_profile_score"),
                        "score_breakdown": run_doc.get("individual_score_components", {}),
                        "scoring_rules_version": run_doc.get("scoring_rules_version", "2.5"),
                        "last_scored_at": stamp,
                    },
                    "$push": {
                        "profile_score_history": {
                            "$each": [{
                                "analysis_run_id": run_doc.get("id"),
                                "score": run_doc.get("candidate_profile_score"),
                                "timestamp": stamp,
                            }],
                            "$slice": -10
                        }
                    }
                }
            )

        # Persist directly into analysis_runs collection
        try:
            analysis_entry = {
                **run_doc,
                "_id": run_doc.get("id"),
                "id": run_doc.get("id"),
                "candidateId": candidate_id,
                "jobId": job_id,
                "applicationId": app_id,
                "cvDocumentId": run_doc.get("cv_document_id"),
                "createdAt": stamp,
            }
            self.db.analysis_runs.insert_one(analysis_entry)
        except Exception:
            pass

        return run_doc

    def get_candidate_analysis_history(self, candidate_id: str) -> List[Dict[str, Any]]:
        # Retrieve analysis history from applications and candidate profile
        apps = list(self.db.applications.find(
            {"$or": [{"userId": candidate_id}, {"candidateId": candidate_id}]},
            {"analysis_history": 1, "enterpriseEvaluation": 1, "appliedAt": 1, "jobId": 1}
        ))
        history = []
        for app in apps:
            for item in app.get("analysis_history", []):
                history.append(item)
            if not app.get("analysis_history") and app.get("enterpriseEvaluation"):
                history.append({
                    "id": f"eval_{app.get('_id')}",
                    "job_id": app.get("jobId"),
                    "job_match_score": app.get("jobMatchScore") or app.get("score"),
                    "analysis_timestamp": app.get("appliedAt"),
                })
        return sorted(history, key=lambda x: str(x.get("analysis_timestamp", "")), reverse=True)

    def get_candidate_job_match(self, candidate_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        return self.db.applications.find_one(
            {"$or": [{"userId": candidate_id}, {"candidateId": candidate_id}], "jobId": job_id}
        )
