"""MongoDB repository for unified candidate_profiles collection."""

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

    def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.db.candidate_profiles.find_one({"$or": [{"user_id": user_id}, {"id": user_id}]})

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower() if email else ""
        if not clean_email:
            return None
        doc = self.db.candidate_profiles.find_one({"personal_info.email": clean_email})
        if not doc:
            user = self.db.users.find_one({"email": clean_email, "role": "candidate"})
            if user:
                return self.find_by_user_id(user["id"])
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
            # Merge dictionary fields safely
            merged_info = {**(existing.get("personal_info") or {}), **(profile_data.get("personal_info") or {})}
            merged_links = {**(existing.get("social_links") or {}), **(profile_data.get("social_links") or {})}
            merged_prefs = {**(existing.get("career_preferences") or {}), **(profile_data.get("career_preferences") or {})}
            
            doc_to_set["personal_info"] = merged_info
            doc_to_set["social_links"] = merged_links
            doc_to_set["career_preferences"] = merged_prefs

            # Keep existing lists if not provided in new profile_data
            for array_field in ("skills", "experience", "education", "projects", "certifications", "languages"):
                if array_field not in profile_data and array_field in existing:
                    doc_to_set[array_field] = existing[array_field]

            result = self.db.candidate_profiles.find_one_and_update(
                {"$or": [{"id": candidate_id}, {"user_id": candidate_id}]},
                {"$set": doc_to_set},
                return_document=ReturnDocument.AFTER,
                upsert=True
            )
            return result
        else:
            doc_to_set["created_at"] = stamp
            self.db.candidate_profiles.insert_one(doc_to_set)
            return doc_to_set

    def get_candidate_skills(self, candidate_id: str) -> List[Dict[str, Any]]:
        profile = self.find_by_user_id(candidate_id) or {}
        return profile.get("skills", [])

    def get_candidate_experience(self, candidate_id: str) -> List[Dict[str, Any]]:
        profile = self.find_by_user_id(candidate_id) or {}
        return sorted(profile.get("experience", []), key=lambda x: str(x.get("start_date", "")), reverse=True)

    def get_candidate_education(self, candidate_id: str) -> List[Dict[str, Any]]:
        profile = self.find_by_user_id(candidate_id) or {}
        return profile.get("education", [])

    def get_candidate_projects(self, candidate_id: str) -> List[Dict[str, Any]]:
        profile = self.find_by_user_id(candidate_id) or {}
        return profile.get("projects", [])

    def get_candidate_certifications(self, candidate_id: str) -> List[Dict[str, Any]]:
        profile = self.find_by_user_id(candidate_id) or {}
        return profile.get("certifications", [])

    def get_candidate_languages(self, candidate_id: str) -> List[Dict[str, Any]]:
        profile = self.find_by_user_id(candidate_id) or {}
        return profile.get("languages", [])
