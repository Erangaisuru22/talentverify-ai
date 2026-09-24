"""MongoDB repository for GitHub evidence using the unified evidence_snapshots collection."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pymongo.database import Database
from pymongo import ReturnDocument


def utcnow():
    return datetime.now(timezone.utc)


class GithubRepository:
    def __init__(self, db: Database):
        self.db = db

    def ensure_indexes(self):
        self.db.evidence_snapshots.create_index("id", unique=True)
        self.db.evidence_snapshots.create_index([("candidate_id", 1), ("platform", 1), ("scanned_at", -1)])
        self.db.evidence_snapshots.create_index([("candidate_id", 1), ("platform", 1)])

    def save_github_snapshot(self, candidate_id: str, snapshot_doc: Dict[str, Any]) -> Dict[str, Any]:
        snapshot_id = snapshot_doc.get("id") or snapshot_doc.get("_id")
        snapshot_doc["candidate_id"] = candidate_id
        snapshot_doc["platform"] = "github"
        snapshot_doc["_id"] = snapshot_id
        snapshot_doc["id"] = snapshot_id
        snapshot_doc["created_at"] = snapshot_doc.get("created_at") or utcnow()

        # Save snapshot into unified evidence_snapshots collection
        self.db.evidence_snapshots.update_one({"_id": snapshot_id}, {"$set": snapshot_doc}, upsert=True)

        # Update candidate_profiles with latest verified github summary
        github_summary = {
            "github_url": snapshot_doc.get("github_url"),
            "username": snapshot_doc.get("username"),
            "latest_snapshot_id": snapshot_id,
            "last_verified_at": snapshot_doc.get("scanned_at"),
            "verification_status": snapshot_doc.get("verification_status", "verified"),
            "profile": snapshot_doc.get("profile", {}),
            "repositories": snapshot_doc.get("repositories", []),
            "detected_skills": snapshot_doc.get("detected_skills", []),
            "skill_evidence": snapshot_doc.get("skill_evidence", []),
            "cv_consistency": snapshot_doc.get("cv_consistency", {}),
            "analysis": snapshot_doc.get("analysis", {}),
            "github_score": snapshot_doc.get("github_score", {}),
        }
        self.db.candidate_profiles.update_one(
            {"$or": [{"id": candidate_id}, {"user_id": candidate_id}]},
            {"$set": {"github": github_summary, "social_links.github_url": snapshot_doc.get("github_url"), "updated_at": utcnow()}},
            upsert=True
        )

        return snapshot_doc

    def get_latest_github_profile(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        # Query latest GitHub snapshot from unified evidence_snapshots collection
        doc = self.db.evidence_snapshots.find_one(
            {"candidate_id": candidate_id, "platform": "github"},
            sort=[("scanned_at", -1)]
        )
        if not doc:
            # Fallback to candidate_profiles.github
            profile = self.db.candidate_profiles.find_one({"$or": [{"id": candidate_id}, {"user_id": candidate_id}]}) or {}
            return profile.get("github")
        return doc

    def get_all_snapshots(self, candidate_id: str) -> List[Dict[str, Any]]:
        return list(self.db.evidence_snapshots.find(
            {"candidate_id": candidate_id, "platform": "github"}
        ).sort("scanned_at", -1))

    def get_github_evidence_by_skill(self, candidate_id: str, skill_name: str) -> Optional[Dict[str, Any]]:
        latest = self.get_latest_github_profile(candidate_id)
        if not latest:
            return None
        clean_skill = skill_name.strip().casefold()
        for item in latest.get("skill_evidence", []):
            if item.get("skill", "").strip().casefold() == clean_skill:
                return item
        return None
