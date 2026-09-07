"""MongoDB repository for analysis runs, candidate scores, and job matches."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pymongo.database import Database


def utcnow():
    return datetime.now(timezone.utc)


class AnalysisRepository:
    def __init__(self, db: Database):
        self.db = db

    def ensure_indexes(self):
        self.db.analysis_runs.create_index([("candidate_id", 1), ("analysis_timestamp", -1)])
        self.db.analysis_runs.create_index([("candidate_id", 1), ("job_id", 1)])
        self.db.candidate_scores.create_index("candidate_id")
        self.db.candidate_job_matches.create_index([("candidate_id", 1), ("job_id", 1)], unique=True)

    def record_analysis_run(self, run_doc: Dict[str, Any]) -> Dict[str, Any]:
        stamp = utcnow()
        run_doc.setdefault("analysis_timestamp", stamp)
        # Store immutable analysis run record
        self.db.analysis_runs.insert_one(run_doc)
        
        candidate_id = run_doc.get("candidate_id")
        
        # Save profile score history in candidate_scores collection
        if candidate_id and "candidate_profile_score" in run_doc:
            score_entry = {
                "candidate_id": candidate_id,
                "analysis_run_id": run_doc.get("id"),
                "overall_score": run_doc.get("candidate_profile_score"),
                "score_breakdown": run_doc.get("individual_score_components", {}),
                "scoring_rules_version": run_doc.get("scoring_rules_version", "2.5"),
                "created_at": stamp,
            }
            self.db.candidate_scores.insert_one(score_entry)
            
        # Save job match in candidate_job_matches collection if applicable
        if candidate_id and run_doc.get("job_id"):
            job_match_entry = {
                "candidate_id": candidate_id,
                "job_id": run_doc.get("job_id"),
                "analysis_run_id": run_doc.get("id"),
                "job_match_score": run_doc.get("job_match_score"),
                "candidate_profile_score": run_doc.get("candidate_profile_score"),
                "recommended_decision": run_doc.get("recommended_decision"),
                "score_breakdown": run_doc.get("individual_score_components", {}),
                "updated_at": stamp,
            }
            self.db.candidate_job_matches.update_one(
                {"candidate_id": candidate_id, "job_id": run_doc.get("job_id")},
                {"$set": job_match_entry},
                upsert=True
            )

        return run_doc

    def get_candidate_analysis_history(self, candidate_id: str) -> List[Dict[str, Any]]:
        return list(self.db.analysis_runs.find({"candidate_id": candidate_id}).sort("analysis_timestamp", -1))

    def get_candidate_job_match(self, candidate_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        return self.db.candidate_job_matches.find_one({"candidate_id": candidate_id, "job_id": job_id})
