"""
TalentVerify AI - Database Schema & Foreign Key Validator Module
Enforces Foreign Key (FK) referential integrity and schema rules across all 8 collections.

Since MongoDB does not natively enforce Foreign Key constraints, this backend
validator guarantees data integrity before inserts and updates.
"""

from typing import Dict, Any, Optional, Tuple, List
from bson import ObjectId
from database import db


def to_object_id_or_str(value: Any) -> Any:
    """Helper to handle both ObjectId and string representations."""
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    return value


def document_exists(collection_name: str, doc_id: Any) -> bool:
    """Check if a document exists by _id (ObjectId or string) or by 'id' field."""
    if not doc_id:
        return False
    
    col = db[collection_name]
    queries = [{"id": str(doc_id)}]
    
    if isinstance(doc_id, ObjectId):
        queries.append({"_id": doc_id})
    elif isinstance(doc_id, str):
        queries.append({"_id": doc_id})
        if ObjectId.is_valid(doc_id):
            queries.append({"_id": ObjectId(doc_id)})
            
    return col.find_one({"$or": queries}, {"_id": 1}) is not None


class SchemaValidationError(Exception):
    """Raised when backend validation fails (Schema, Type, or Foreign Key constraint)."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.field = field


class DatabaseValidator:
    """Backend validator ensuring Foreign Key referential integrity and valid schemas."""

    @staticmethod
    def validate_user(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate 1. users collection requirements."""
        if not data.get("email"):
            return False, "User 'email' is required."
        
        role = data.get("role")
        if role and role not in ["candidate", "recruiter", "admin"]:
            return False, f"Invalid user role: '{role}'. Must be candidate, recruiter, or admin."

        return True, None

    @staticmethod
    def validate_candidate_profile(data: Dict[str, Any], check_fk: bool = True) -> Tuple[bool, Optional[str]]:
        """Validate 2. candidate_profiles collection & FK -> users._id."""
        user_id = data.get("user_id")
        if not user_id:
            return False, "Candidate profile requires 'user_id'."
            
        if check_fk and not document_exists("users", user_id):
            return False, f"Foreign Key violation: Referenced user_id '{user_id}' does not exist in 'users' collection."

        return True, None

    @staticmethod
    def validate_job(data: Dict[str, Any], check_fk: bool = True) -> Tuple[bool, Optional[str]]:
        """Validate 3. jobs collection & FK -> recruiterId (users._id)."""
        if not data.get("title"):
            return False, "Job 'title' is required."

        recruiter_id = data.get("recruiterId")
        if recruiter_id and check_fk:
            if not document_exists("users", recruiter_id):
                return False, f"Foreign Key violation: recruiterId '{recruiter_id}' does not exist in 'users' collection."

        status = data.get("status")
        if status and status not in ["draft", "open", "closed"]:
            return False, f"Invalid job status: '{status}'. Must be draft, open, or closed."

        return True, None

    @staticmethod
    def validate_application(data: Dict[str, Any], check_fk: bool = True) -> Tuple[bool, Optional[str]]:
        """Validate 4. applications collection & FKs -> userId, jobId, cvDocumentId."""
        user_id = data.get("userId")
        job_id = data.get("jobId")
        cv_doc_id = data.get("cvDocumentId")

        if not user_id or not job_id:
            return False, "Application requires both 'userId' and 'jobId'."

        if check_fk:
            if not document_exists("users", user_id):
                return False, f"Foreign Key violation: userId '{user_id}' does not exist in 'users' collection."
            if not document_exists("jobs", job_id):
                return False, f"Foreign Key violation: jobId '{job_id}' does not exist in 'jobs' collection."
            if cv_doc_id and not document_exists("cv_documents", cv_doc_id):
                return False, f"Foreign Key violation: cvDocumentId '{cv_doc_id}' does not exist in 'cv_documents' collection."

        status = data.get("status")
        valid_statuses = [
            "submitted", "Submitted",
            "Under review", "under_review",
            "reviewing", "Reviewing",
            "shortlisted", "Shortlisted",
            "rejected", "Rejected",
            "hired", "Hired",
            "Selected", "selected",
            "Withdrawn", "Application Withdrawn",
            "pending"
        ]
        if status and status not in valid_statuses:
            return False, f"Invalid application status '{status}'. Must be one of {valid_statuses}."

        return True, None

    @staticmethod
    def validate_cv_document(data: Dict[str, Any], check_fk: bool = True) -> Tuple[bool, Optional[str]]:
        """Validate 5. cv_documents collection & FK -> candidate_id (users._id)."""
        candidate_id = data.get("candidate_id")
        if candidate_id and check_fk:
            if not document_exists("users", candidate_id):
                return False, f"Foreign Key violation: candidate_id '{candidate_id}' does not exist in 'users' collection."

        parsing_status = data.get("parsing_status")
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if parsing_status and parsing_status not in valid_statuses:
            return False, f"Invalid parsing_status '{parsing_status}'. Must be one of {valid_statuses}."

        return True, None

    @staticmethod
    def validate_evidence_snapshot(data: Dict[str, Any], check_fk: bool = True) -> Tuple[bool, Optional[str]]:
        """Validate 6. evidence_snapshots collection & FK -> candidate_id (users._id)."""
        candidate_id = data.get("candidate_id")
        if candidate_id and check_fk:
            if not document_exists("users", candidate_id):
                return False, f"Foreign Key violation: candidate_id '{candidate_id}' does not exist in 'users' collection."

        platform = data.get("platform")
        if platform and platform not in ["github", "linkedin", "portfolio"]:
            return False, f"Invalid platform '{platform}'. Must be github, linkedin, or portfolio."

        status = data.get("verification_status")
        if status and status not in ["verified", "partial", "failed"]:
            return False, f"Invalid verification_status '{status}'. Must be verified, partial, or failed."

        return True, None

    @staticmethod
    def validate_audit_log(data: Dict[str, Any], check_fk: bool = True) -> Tuple[bool, Optional[str]]:
        """Validate 7. audit_logs collection & FKs -> userId, performedBy."""
        user_id = data.get("userId")
        performed_by = data.get("performedBy")

        if check_fk:
            if user_id and not document_exists("users", user_id):
                return False, f"Foreign Key violation: userId '{user_id}' does not exist in 'users' collection."
            if performed_by and not document_exists("users", performed_by):
                return False, f"Foreign Key violation: performedBy '{performed_by}' does not exist in 'users' collection."

        return True, None

    @staticmethod
    def validate_analysis_run(data: Dict[str, Any], check_fk: bool = True) -> Tuple[bool, Optional[str]]:
        """Validate 8. analysis_runs collection & FKs -> candidateId, jobId, applicationId, cvDocumentId."""
        candidate_id = data.get("candidateId")
        job_id = data.get("jobId")
        app_id = data.get("applicationId")
        cv_doc_id = data.get("cvDocumentId")

        if check_fk:
            if candidate_id and not document_exists("users", candidate_id):
                return False, f"Foreign Key violation: candidateId '{candidate_id}' does not exist in 'users' collection."
            if job_id and not document_exists("jobs", job_id):
                return False, f"Foreign Key violation: jobId '{job_id}' does not exist in 'jobs' collection."
            if app_id and not document_exists("applications", app_id):
                return False, f"Foreign Key violation: applicationId '{app_id}' does not exist in 'applications' collection."
            if cv_doc_id and not document_exists("cv_documents", cv_doc_id):
                return False, f"Foreign Key violation: cvDocumentId '{cv_doc_id}' does not exist in 'cv_documents' collection."

        analysis_type = data.get("analysisType")
        valid_types = ["cv_analysis", "job_match", "profile_score"]
        if analysis_type and analysis_type not in valid_types:
            return False, f"Invalid analysisType '{analysis_type}'. Must be one of {valid_types}."

        return True, None


def validate_before_insert(collection_name: str, document: Dict[str, Any], check_fk: bool = True):
    """
    Convenience method to validate a document before inserting into any of the 8 collections.
    Raises SchemaValidationError if validation or Foreign Key check fails.
    """
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

    validator_fn = validators.get(collection_name)
    if not validator_fn:
        return True

    # Call validator (with check_fk if supported)
    try:
        is_valid, error_msg = validator_fn(document, check_fk=check_fk)
    except TypeError:
        is_valid, error_msg = validator_fn(document)

    if not is_valid:
        raise SchemaValidationError(f"Validation failed for collection '{collection_name}': {error_msg}")

    return True
