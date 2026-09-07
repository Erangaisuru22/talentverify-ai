"""MongoDB repository for jobs, requirements, applications, and evaluations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pymongo.database import Database


def utcnow():
    return datetime.now(timezone.utc)


class JobRepository:
    def __init__(self, db: Database):
        self.db = db

    def ensure_indexes(self):
        self.db.jobs.create_index("id", unique=True)
        self.db.jobs.create_index("recruiterId")
        self.db.job_requirements.create_index("job_id", unique=True)
        self.db.applications.create_index([("userId", 1), ("jobId", 1)], unique=True)
        self.db.applications.create_index("id", unique=True)

    def find_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.db.jobs.find_one({"id": job_id})

    def find_all_jobs(self) -> List[Dict[str, Any]]:
        return list(self.db.jobs.find().sort("createdAt", -1))

    def save_application(self, application_doc: Dict[str, Any]) -> Dict[str, Any]:
        self.db.applications.update_one({"id": application_doc["id"]}, {"$set": application_doc}, upsert=True)
        return application_doc

    def get_application_by_id(self, application_id: str) -> Optional[Dict[str, Any]]:
        return self.db.applications.find_one({"id": application_id})
