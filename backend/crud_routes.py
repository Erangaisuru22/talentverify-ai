"""
TalentVerify AI - RESTful CRUD Operations Router
Provides complete findAll, findOne, save (create), update, deleteOne, and deleteAll operations:
1. Specific resource endpoints: /api/jobs, /api/applications, /api/candidate-profiles, /api/users
2. Universal generic CRUD: /api/crud/{collection} for all 8 collections:
   - users, candidate_profiles, jobs, applications, cv_documents, evidence_snapshots, audit_logs, analysis_runs
3. Full Postman compatibility with Bearer token, query token, or header token.
"""

from datetime import datetime, timezone
import hashlib
import secrets
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request, status
from pymongo import ReturnDocument

from database import db
from domain import audit, utcnow

crud_router = APIRouter(tags=["CRUD Operations"])

ALLOWED_COLLECTIONS = {
    "users",
    "candidate_profiles",
    "jobs",
    "applications",
    "cv_documents",
    "evidence_snapshots",
    "audit_logs",
    "analysis_runs",
}

COLLECTION_PREFIX_MAP = {
    "users": "USER",
    "candidate_profiles": "CAND",
    "jobs": "JOB",
    "applications": "APP",
    "cv_documents": "CV",
    "evidence_snapshots": "SNAP",
    "audit_logs": "AUDIT",
    "analysis_runs": "RUN",
}


def public_document(document):
    """Recursively clean MongoDB ObjectId and sensitive credentials for JSON serialization."""
    if document is None:
        return None
    if isinstance(document, ObjectId):
        return str(document)
    if isinstance(document, dict):
        return {key: public_document(value) for key, value in document.items() if key not in {"_id", "passwordHash"}}
    if isinstance(document, (list, tuple)):
        return [public_document(value) for value in document]
    return document


def resolve_token(request: Request, token: Optional[str] = None) -> Optional[str]:
    """Extract auth token from query parameter, Authorization header (Bearer or plain), or X-Auth-Token."""
    if token and str(token).strip():
        return str(token).strip()
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    if auth.strip():
        return auth.strip()
    x_token = request.headers.get("X-Auth-Token")
    if x_token and x_token.strip():
        return x_token.strip()
    q_token = request.query_params.get("token")
    if q_token and q_token.strip():
        return q_token.strip()
    return None


def get_current_user(request: Request, token: Optional[str] = None, required: bool = False) -> Optional[Dict[str, Any]]:
    """Retrieve session user if token is provided; raises 401 only if required is True."""
    resolved = resolve_token(request, token)
    if not resolved:
        if required:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required. Please provide a token.")
        return None
    user = db.users.find_one({"$or": [{"token": resolved}, {"id": resolved}]})
    if not user and required:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    return public_document(user) if user else None


def generate_custom_id(collection_name: str, prefix: Optional[str] = None) -> str:
    """Generate clean sequential identifier (e.g., JOB-008, APP-005, CAND-005)."""
    pfx = prefix or COLLECTION_PREFIX_MAP.get(collection_name, "DOC")
    col = db[collection_name]
    count = col.count_documents({}) + 1
    custom_id = f"{pfx}-{count:03d}"
    while col.find_one({"$or": [{"_id": custom_id}, {"id": custom_id}]}):
        count += 1
        custom_id = f"{pfx}-{count:03d}"
    return custom_id


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210000).hex()
    return f"{salt}${digest}"


# =============================================================================
# 1. UNIVERSAL GENERIC CRUD: /api/crud/{collection}
# =============================================================================

@crud_router.get("/api/crud/{collection}")
def generic_find_all(
    collection: str,
    request: Request,
    token: Optional[str] = None,
    limit: int = Query(50, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("createdAt", description="Field to sort by"),
    order: int = Query(-1, description="-1 for descending, 1 for ascending"),
):
    """
    [findAll] Retrieve all documents from any of the 8 collections with optional filtering & pagination.
    Pass any collection field as query parameter to filter (e.g., ?role=candidate or ?status=open).
    """
    if collection not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Collection '{collection}' is not valid. Allowed: {list(ALLOWED_COLLECTIONS)}")

    # Extract dynamic query filter from request params
    reserved_keys = {"token", "limit", "skip", "sort_by", "order"}
    query_filter: Dict[str, Any] = {}
    for key, val in request.query_params.items():
        if key not in reserved_keys:
            # Type coercion for booleans / numbers
            if val.lower() == "true":
                query_filter[key] = True
            elif val.lower() == "false":
                query_filter[key] = False
            elif val.isdigit():
                query_filter[key] = int(val)
            else:
                query_filter[key] = val

    col = db[collection]
    total = col.count_documents(query_filter)
    
    # Check if sort_by exists in collection documents, fallback to _id
    sort_field = sort_by
    sample = col.find_one()
    if sample and sort_by not in sample:
        if "created_at" in sample:
            sort_field = "created_at"
        elif "createdAt" in sample:
            sort_field = "createdAt"
        else:
            sort_field = "_id"

    cursor = col.find(query_filter).sort(sort_field, order).skip(skip).limit(limit)
    items = [public_document(doc) for doc in cursor]

    return {
        "ok": True,
        "operation": "findAll",
        "collection": collection,
        "total": total,
        "count": len(items),
        "skip": skip,
        "limit": limit,
        "data": items,
    }


@crud_router.get("/api/crud/{collection}/{item_id}")
def generic_find_one(collection: str, item_id: str, request: Request, token: Optional[str] = None):
    """[findOne] Retrieve a single document by ID from any of the 8 collections."""
    if collection not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Collection '{collection}' is not valid. Allowed: {list(ALLOWED_COLLECTIONS)}")

    col = db[collection]
    doc = col.find_one({"$or": [{"id": item_id}, {"_id": item_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID '{item_id}' not found in '{collection}'.")

    return {
        "ok": True,
        "operation": "findOne",
        "collection": collection,
        "id": item_id,
        "data": public_document(doc),
    }


@crud_router.post("/api/crud/{collection}", status_code=status.HTTP_201_CREATED)
def generic_save(collection: str, payload: Dict[str, Any], request: Request, token: Optional[str] = None):
    """[save / create] Insert a new document into any of the 8 collections."""
    if collection not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Collection '{collection}' is not valid. Allowed: {list(ALLOWED_COLLECTIONS)}")

    user = get_current_user(request, token)
    actor_id = user["id"] if user else "REC-001"
    col = db[collection]

    # Assign clean ID if not provided
    doc = dict(payload)
    item_id = doc.get("id") or doc.get("_id") or generate_custom_id(collection)
    doc["_id"] = item_id
    doc["id"] = item_id

    # If saving a user with plain password, hash it
    if collection == "users" and "password" in doc and "passwordHash" not in doc:
        doc["passwordHash"] = hash_password(doc.pop("password"))

    # Set timestamps
    now_iso = datetime.now(timezone.utc).isoformat()
    doc.setdefault("createdAt", now_iso)
    doc.setdefault("created_at", utcnow())
    doc.setdefault("updatedAt", now_iso)

    col.insert_one(doc)
    audit(db, f"crud_{collection}_created", actor_id, collection, item_id, {"source": "postman_crud"})

    return {
        "ok": True,
        "operation": "save",
        "collection": collection,
        "id": item_id,
        "message": f"Document '{item_id}' successfully saved in '{collection}'.",
        "data": public_document(doc),
    }


@crud_router.put("/api/crud/{collection}/{item_id}")
@crud_router.patch("/api/crud/{collection}/{item_id}")
def generic_update(collection: str, item_id: str, payload: Dict[str, Any], request: Request, token: Optional[str] = None):
    """[update] Update an existing document by ID in any of the 8 collections."""
    if collection not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Collection '{collection}' is not valid. Allowed: {list(ALLOWED_COLLECTIONS)}")

    user = get_current_user(request, token)
    actor_id = user["id"] if user else "REC-001"
    col = db[collection]

    existing = col.find_one({"$or": [{"id": item_id}, {"_id": item_id}]})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Document with ID '{item_id}' not found in '{collection}'.")

    changes = dict(payload)
    changes.pop("_id", None)
    changes.pop("id", None)

    # Hash password if updated on user
    if collection == "users" and "password" in changes:
        changes["passwordHash"] = hash_password(changes.pop("password"))

    now_iso = datetime.now(timezone.utc).isoformat()
    changes["updatedAt"] = now_iso
    changes["updated_at"] = utcnow()

    updated = col.find_one_and_update(
        {"$or": [{"id": item_id}, {"_id": item_id}]},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    audit(db, f"crud_{collection}_updated", actor_id, collection, item_id, {"fields": list(changes.keys())})

    return {
        "ok": True,
        "operation": "update",
        "collection": collection,
        "id": item_id,
        "message": f"Document '{item_id}' successfully updated in '{collection}'.",
        "data": public_document(updated),
    }


@crud_router.delete("/api/crud/{collection}/{item_id}")
def generic_delete_one(collection: str, item_id: str, request: Request, token: Optional[str] = None):
    """[deleteOne] Delete a single document by ID from any of the 8 collections."""
    if collection not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Collection '{collection}' is not valid. Allowed: {list(ALLOWED_COLLECTIONS)}")

    user = get_current_user(request, token)
    actor_id = user["id"] if user else "SYSTEM_POSTMAN"
    col = db[collection]

    doc = col.find_one({"$or": [{"id": item_id}, {"_id": item_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID '{item_id}' not found in '{collection}'.")

    result = col.delete_one({"$or": [{"id": item_id}, {"_id": item_id}]})
    audit(db, f"crud_{collection}_deleted", actor_id, collection, item_id, {"count": result.deleted_count})

    return {
        "ok": True,
        "operation": "deleteOne",
        "collection": collection,
        "id": item_id,
        "message": f"Document '{item_id}' deleted successfully from '{collection}'.",
    }


@crud_router.delete("/api/crud/{collection}")
def generic_delete_all(
    collection: str,
    request: Request,
    confirm: bool = Query(False, description="Must be true to prevent accidental bulk deletion"),
    token: Optional[str] = None,
):
    """
    [deleteAll] Bulk delete documents from any of the 8 collections.
    Requires `confirm=true` as safety confirmation. Supports query filters (e.g. ?status=archived).
    """
    if collection not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Collection '{collection}' is not valid. Allowed: {list(ALLOWED_COLLECTIONS)}")

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Safety confirmation required. Please pass '?confirm=true' in query parameter to proceed with bulk delete.",
        )

    user = get_current_user(request, token)
    actor_id = user["id"] if user else "SYSTEM_POSTMAN"
    col = db[collection]

    # Optional dynamic filters
    reserved_keys = {"token", "confirm"}
    query_filter: Dict[str, Any] = {}
    for key, val in request.query_params.items():
        if key not in reserved_keys:
            query_filter[key] = val

    result = col.delete_many(query_filter)
    audit(db, f"crud_{collection}_bulk_deleted", actor_id, collection, "ALL", {"deleted_count": result.deleted_count, "filter": query_filter})

    return {
        "ok": True,
        "operation": "deleteAll",
        "collection": collection,
        "deleted_count": result.deleted_count,
        "message": f"Successfully deleted {result.deleted_count} documents from '{collection}'.",
    }


# =============================================================================
# 2. DEDICATED RESOURCE CRUD: /api/applications
# =============================================================================

@crud_router.get("/api/applications")
def list_applications_crud(
    request: Request,
    token: Optional[str] = None,
    jobId: Optional[str] = None,
    userId: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = 50,
    skip: int = 0,
):
    """[findAll] List job applications with optional candidate/job/status filters."""
    query: Dict[str, Any] = {}
    if jobId:
        query["jobId"] = jobId
    if userId:
        query["userId"] = userId
    if status_filter:
        query["status"] = status_filter

    user = get_current_user(request, token)
    # If candidate, restrict to their applications unless token is recruiter
    if user and user.get("role") == "candidate":
        query["userId"] = user["id"]

    cursor = db.applications.find(query).sort("appliedAt", -1).skip(skip).limit(limit)
    items = [public_document(doc) for doc in cursor]
    return {
        "ok": True,
        "total": db.applications.count_documents(query),
        "count": len(items),
        "data": items,
    }


@crud_router.get("/api/applications/{application_id}")
def get_application_crud(application_id: str, request: Request, token: Optional[str] = None):
    """[findOne] Retrieve a single application by ID."""
    doc = db.applications.find_one({"$or": [{"id": application_id}, {"_id": application_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Application not found.")
    return {"ok": True, "data": public_document(doc)}


@crud_router.put("/api/applications/{application_id}")
def update_application_crud(application_id: str, payload: Dict[str, Any], request: Request, token: Optional[str] = None):
    """[update] Update an application's status, notes, or interview details."""
    user = get_current_user(request, token)
    actor_id = user["id"] if user else "SYSTEM_POSTMAN"

    changes = dict(payload)
    changes.pop("_id", None)
    changes.pop("id", None)
    changes["updatedAt"] = datetime.now(timezone.utc).isoformat()

    updated = db.applications.find_one_and_update(
        {"$or": [{"id": application_id}, {"_id": application_id}]},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found.")

    audit(db, "application_updated", actor_id, "application", application_id, {"fields": list(changes.keys())})
    return {"ok": True, "message": "Application updated successfully.", "data": public_document(updated)}


@crud_router.delete("/api/applications")
def delete_all_applications_crud(
    request: Request,
    confirm: bool = Query(False),
    jobId: Optional[str] = None,
    token: Optional[str] = None,
):
    """[deleteAll] Delete applications with `confirm=true`."""
    if not confirm:
        raise HTTPException(status_code=400, detail="Must pass '?confirm=true' parameter to confirm bulk delete.")
    query = {"jobId": jobId} if jobId else {}
    result = db.applications.delete_many(query)
    return {"ok": True, "message": f"Deleted {result.deleted_count} applications.", "deleted_count": result.deleted_count}


# =============================================================================
# 3. DEDICATED RESOURCE CRUD: /api/candidate-profiles & /api/candidates
# =============================================================================

@crud_router.get("/api/candidate-profiles")
@crud_router.get("/api/candidates")
def list_candidates_crud(request: Request, token: Optional[str] = None, limit: int = 50, skip: int = 0):
    """[findAll] List candidate profiles."""
    cursor = db.candidate_profiles.find().sort("candidate_profile_score", -1).skip(skip).limit(limit)
    items = [public_document(doc) for doc in cursor]
    return {
        "ok": True,
        "total": db.candidate_profiles.count_documents({}),
        "count": len(items),
        "data": items,
    }


@crud_router.get("/api/candidate-profiles/{candidate_id}")
@crud_router.get("/api/candidates/{candidate_id}")
def get_candidate_profile_crud(candidate_id: str, request: Request, token: Optional[str] = None):
    """[findOne] Retrieve candidate profile by candidate ID or user ID."""
    doc = db.candidate_profiles.find_one({"$or": [{"id": candidate_id}, {"user_id": candidate_id}, {"_id": candidate_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    return {"ok": True, "data": public_document(doc)}


@crud_router.post("/api/candidate-profiles", status_code=status.HTTP_201_CREATED)
@crud_router.post("/api/candidates", status_code=status.HTTP_201_CREATED)
def save_candidate_profile_crud(payload: Dict[str, Any], request: Request, token: Optional[str] = None):
    """[save / create] Create a new candidate profile."""
    cand_id = payload.get("id") or payload.get("user_id") or generate_custom_id("candidate_profiles", "CAND")
    doc = dict(payload)
    doc["_id"] = cand_id
    doc["id"] = cand_id
    doc["user_id"] = cand_id
    doc.setdefault("created_at", utcnow())
    doc.setdefault("updated_at", utcnow())

    db.candidate_profiles.insert_one(doc)
    return {"ok": True, "message": "Candidate profile created.", "data": public_document(doc)}


@crud_router.put("/api/candidate-profiles/{candidate_id}")
@crud_router.patch("/api/candidate-profiles/{candidate_id}")
@crud_router.put("/api/candidates/{candidate_id}")
@crud_router.patch("/api/candidates/{candidate_id}")
def update_candidate_profile_crud(candidate_id: str, payload: Dict[str, Any], request: Request, token: Optional[str] = None):
    """[update] Update an existing candidate profile."""
    changes = dict(payload)
    changes.pop("_id", None)
    changes.pop("id", None)
    changes["updated_at"] = utcnow()

    updated = db.candidate_profiles.find_one_and_update(
        {"$or": [{"id": candidate_id}, {"user_id": candidate_id}, {"_id": candidate_id}]},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    return {"ok": True, "message": "Candidate profile updated.", "data": public_document(updated)}


@crud_router.delete("/api/candidate-profiles/{candidate_id}")
@crud_router.delete("/api/candidates/{candidate_id}")
def delete_candidate_profile_crud(candidate_id: str, request: Request, token: Optional[str] = None):
    """[deleteOne] Delete candidate profile by ID."""
    result = db.candidate_profiles.delete_one({"$or": [{"id": candidate_id}, {"user_id": candidate_id}, {"_id": candidate_id}]})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    return {"ok": True, "message": f"Candidate profile '{candidate_id}' deleted."}


@crud_router.delete("/api/candidate-profiles")
@crud_router.delete("/api/candidates")
def delete_all_candidate_profiles_crud(request: Request, confirm: bool = Query(False), token: Optional[str] = None):
    """[deleteAll] Delete all candidate profiles with `confirm=true`."""
    if not confirm:
        raise HTTPException(status_code=400, detail="Must pass '?confirm=true' parameter to confirm bulk delete.")
    result = db.candidate_profiles.delete_many({})
    return {"ok": True, "message": f"Deleted {result.deleted_count} candidate profiles.", "deleted_count": result.deleted_count}


# =============================================================================
# 4. DEDICATED RESOURCE CRUD: /api/users
# =============================================================================

@crud_router.get("/api/users")
def list_users_crud(
    request: Request,
    token: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    """[findAll] List users with optional role filter."""
    query = {"role": role} if role else {}
    cursor = db.users.find(query).sort("createdAt", -1).skip(skip).limit(limit)
    items = [public_document(doc) for doc in cursor]
    return {
        "ok": True,
        "total": db.users.count_documents(query),
        "count": len(items),
        "data": items,
    }


@crud_router.get("/api/users/{user_id}")
def get_user_crud(user_id: str, request: Request, token: Optional[str] = None):
    """[findOne] Retrieve user by user ID or email."""
    doc = db.users.find_one({"$or": [{"id": user_id}, {"_id": user_id}, {"email": user_id.lower().strip()}]})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"ok": True, "data": public_document(doc)}


@crud_router.post("/api/users", status_code=status.HTTP_201_CREATED)
def save_user_crud(payload: Dict[str, Any], request: Request, token: Optional[str] = None):
    """[save / create] Create a new user account."""
    email = str(payload.get("email", "")).strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="User email is required.")
    if db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail=f"User with email '{email}' already exists.")

    role = payload.get("role", "candidate")
    prefix = "REC" if role == "recruiter" else "CAND"
    user_id = payload.get("id") or generate_custom_id("users", prefix)

    doc = dict(payload)
    doc["_id"] = user_id
    doc["id"] = user_id
    doc["email"] = email
    doc["role"] = role
    doc.setdefault("name", payload.get("name") or email.split("@")[0].capitalize())
    doc.setdefault("isActive", True)

    raw_password = doc.pop("password", "abcd123@")
    doc["passwordHash"] = hash_password(raw_password)

    now_iso = datetime.now(timezone.utc).isoformat()
    doc.setdefault("createdAt", now_iso)
    doc.setdefault("updatedAt", now_iso)

    db.users.insert_one(doc)
    return {"ok": True, "message": f"User '{user_id}' created successfully.", "data": public_document(doc)}


@crud_router.put("/api/users/{user_id}")
@crud_router.patch("/api/users/{user_id}")
def update_user_crud(user_id: str, payload: Dict[str, Any], request: Request, token: Optional[str] = None):
    """[update] Update user details by ID."""
    changes = dict(payload)
    changes.pop("_id", None)
    changes.pop("id", None)

    if "password" in changes:
        changes["passwordHash"] = hash_password(changes.pop("password"))

    changes["updatedAt"] = datetime.now(timezone.utc).isoformat()
    updated = db.users.find_one_and_update(
        {"$or": [{"id": user_id}, {"_id": user_id}]},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"ok": True, "message": f"User '{user_id}' updated successfully.", "data": public_document(updated)}


@crud_router.delete("/api/users/{user_id}")
def delete_user_crud(user_id: str, request: Request, token: Optional[str] = None):
    """[deleteOne] Delete user by ID."""
    result = db.users.delete_one({"$or": [{"id": user_id}, {"_id": user_id}]})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"ok": True, "message": f"User '{user_id}' deleted successfully."}


@crud_router.delete("/api/users")
def delete_all_users_crud(request: Request, confirm: bool = Query(False), token: Optional[str] = None):
    """[deleteAll] Delete users with `confirm=true` (preserves demo accounts by default)."""
    if not confirm:
        raise HTTPException(status_code=400, detail="Must pass '?confirm=true' parameter to confirm bulk delete.")
    # Protect demo accounts unless explicit force query
    query = {"id": {"$nin": ["REC-001", "CAND-001"]}}
    result = db.users.delete_many(query)
    return {"ok": True, "message": f"Deleted {result.deleted_count} non-demo users.", "deleted_count": result.deleted_count}


# =============================================================================
# 5. POSTMAN 1-CLICK IMPORT ENDPOINTS
# =============================================================================

@crud_router.get("/api/postman/collection")
def get_postman_collection_http():
    """Serves the Postman Collection JSON directly for Postman's 'Import from Link'."""
    import json
    from pathlib import Path
    from fastapi.responses import JSONResponse

    root_dir = Path(__file__).resolve().parent.parent
    col_path = root_dir / "TalentVerify_CRUD_API.postman_collection.json"
    if not col_path.exists():
        col_path = root_dir / "postman" / "collections" / "TalentVerify_CRUD_API.postman_collection.json"
    if not col_path.exists():
        raise HTTPException(status_code=404, detail="Collection file not found.")
    with open(col_path, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))


@crud_router.get("/api/postman/environment")
def get_postman_environment_http():
    """Serves the Postman Environment JSON directly for Postman's 'Import from Link'."""
    import json
    from pathlib import Path
    from fastapi.responses import JSONResponse

    root_dir = Path(__file__).resolve().parent.parent
    env_path = root_dir / "TalentVerify_Local.postman_environment.json"
    if not env_path.exists():
        env_path = root_dir / "postman" / "environments" / "TalentVerify_Local.postman_environment.json"
    if not env_path.exists():
        raise HTTPException(status_code=404, detail="Environment file not found.")
    with open(env_path, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))

