"""MongoDB repository for candidate profiles and associated domain entities."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pymongo.database import Database
from pymongo import ReturnDocument


def utcnow():
    return datetime.now(timezone.utc)


class CandidateRepository:
    def __init__(self, db: Database):
        self.db = db

    def ensure_indexes(self):
        self.db.candidate_profiles.create_index("user_id", unique=True)
        self.db.candidate_profiles.create_index("id", unique=True)
        self.db.candidate_profiles.create_index("personal_info.email")
        self.db.candidate_skills.create_index([("candidate_id", 1), ("normalized_skill", 1), ("kind", 1)])
        self.db.candidate_experience.create_index("candidate_id")
        self.db.candidate_education.create_index("candidate_id")
        self.db.candidate_projects.create_index("candidate_id")
        self.db.candidate_certifications.create_index("candidate_id")
        self.db.candidate_languages.create_index([("candidate_id", 1), ("language", 1)])

    def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.candidate_profiles.find_one({"user_id": user_id})
        if not doc:
            doc = self.db.candidates.find_one({"user_id": user_id}) or self.db.candidates.find_one({"id": user_id})
        return doc

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower() if email else ""
        if not clean_email:
            return None
        doc = self.db.candidate_profiles.find_one({"personal_info.email": clean_email})
        if not doc:
            doc = self.db.users.find_one({"email": clean_email, "role": "candidate"})
            if doc:
                return self.find_by_user_id(doc["id"])
        return doc

    def save_or_update_profile(self, candidate_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        stamp = utcnow()
        existing = self.find_by_user_id(candidate_id)
        
        doc_to_set = {
            **profile_data,
            "id": candidate_id,
            "user_id": candidate_id,
            "updated_at": stamp,
        }
        
        if existing:
            # Update newly discovered profile information without overwriting existing safe fields unless provided
            merged_info = {**(existing.get("personal_info") or {}), **(profile_data.get("personal_info") or {})}
            merged_links = {**(existing.get("social_links") or {}), **(profile_data.get("social_links") or {})}
            doc_to_set["personal_info"] = merged_info
            doc_to_set["social_links"] = merged_links
            
            result = self.db.candidate_profiles.find_one_and_update(
                {"id": candidate_id},
                {"$set": doc_to_set},
                return_document=ReturnDocument.AFTER,
                upsert=True
            )
            # Also keep legacy candidates collection in sync for backward compatibility
            self.db.candidates.update_one({"id": candidate_id}, {"$set": doc_to_set}, upsert=True)
            return result
        else:
            doc_to_set["created_at"] = stamp
            self.db.candidate_profiles.insert_one(doc_to_set)
            self.db.candidates.update_one({"id": candidate_id}, {"$set": doc_to_set}, upsert=True)
            return doc_to_set

    def get_candidate_skills(self, candidate_id: str) -> List[Dict[str, Any]]:
        return list(self.db.candidate_skills.find({"candidate_id": candidate_id}))

    def get_candidate_experience(self, candidate_id: str) -> List[Dict[str, Any]]:
        return list(self.db.candidate_experience.find({"candidate_id": candidate_id}).sort("start_date", -1))

    def get_candidate_education(self, candidate_id: str) -> List[Dict[str, Any]]:
        return list(self.db.candidate_education.find({"candidate_id": candidate_id}))

    def get_candidate_projects(self, candidate_id: str) -> List[Dict[str, Any]]:
        return list(self.db.candidate_projects.find({"candidate_id": candidate_id}))

    def get_candidate_certifications(self, candidate_id: str) -> List[Dict[str, Any]]:
        return list(self.db.candidate_certifications.find({"candidate_id": candidate_id}))

    def get_candidate_languages(self, candidate_id: str) -> List[Dict[str, Any]]:
        return list(self.db.candidate_languages.find({"candidate_id": candidate_id}))
