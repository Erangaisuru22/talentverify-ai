"""
TalentVerify AI – Complete Database Schema Setup & Validator Script
Configures all 8 collections, JSON schema validations ($jsonSchema), and indexes in MongoDB.

Collections:
1. users
2. candidate_profiles
3. jobs
4. applications
5. cv_documents
6. evidence_snapshots
7. audit_logs
8. analysis_runs
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "talentverifyai")

print(f"Connecting to MongoDB at {MONGODB_URI}, Database: {MONGODB_DB}...")
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client[MONGODB_DB]

# ---------------------------------------------------------------------------
# MongoDB $jsonSchema Definitions for all 8 Collections
# (Allows both BSON objectId and string for IDs to ensure flexibility)
# ---------------------------------------------------------------------------

ID_TYPE = ["objectId", "string"]
DATE_TYPE = ["date", "string", "null"]
NUMBER_TYPE = ["double", "int", "long", "decimal", "null"]

SCHEMAS = {
    # 1. users
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["email", "role"],
            "properties": {
                "_id": {"bsonType": ID_TYPE},
                "role": {
                    "bsonType": "string",
                    "enum": ["candidate", "recruiter", "admin"],
                    "description": "Must be candidate, recruiter, or admin"
                },
                "name": {"bsonType": ["string", "null"]},
                "email": {"bsonType": "string", "pattern": "^.+@.+\\..+$"},
                "passwordHash": {"bsonType": ["string", "null"]},
                "phone": {"bsonType": ["string", "null"]},
                "company": {"bsonType": ["string", "null"]},
                "headline": {"bsonType": ["string", "null"]},
                "location": {"bsonType": ["string", "null"]},
                "profileImage": {"bsonType": ["string", "null"]},
                "refreshTokenHash": {"bsonType": ["string", "null"]},
                "isActive": {"bsonType": ["bool", "null"]},
                "createdAt": {"bsonType": DATE_TYPE},
                "updatedAt": {"bsonType": DATE_TYPE}
            }
        }
    },

    # 2. candidate_profiles
    "candidate_profiles": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user_id"],
            "properties": {
                "_id": {"bsonType": ID_TYPE},
                "user_id": {"bsonType": ID_TYPE, "description": "FK -> users._id"},
                "personal_info": {
                    "bsonType": "object",
                    "properties": {
                        "full_name": {"bsonType": ["string", "null"]},
                        "email": {"bsonType": ["string", "null"]},
                        "phone": {"bsonType": ["string", "null"]},
                        "location": {"bsonType": ["string", "null"]},
                        "summary": {"bsonType": ["string", "null"]}
                    }
                },
                "social_links": {
                    "bsonType": "object",
                    "properties": {
                        "linkedin": {"bsonType": ["string", "null"]},
                        "github": {"bsonType": ["string", "null"]},
                        "portfolio": {"bsonType": ["string", "null"]}
                    }
                },
                "skills": {"bsonType": ["array", "null"], "items": {"bsonType": ["object", "string"]}},
                "technical_skills": {"bsonType": ["array", "null"], "items": {"bsonType": ["string", "object"]}},
                "soft_skills": {"bsonType": ["array", "null"], "items": {"bsonType": ["string", "object"]}},
                "experience": {
                    "bsonType": ["array", "null"],
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "job_title": {"bsonType": ["string", "null"]},
                            "company": {"bsonType": ["string", "null"]},
                            "start_date": {"bsonType": DATE_TYPE},
                            "end_date": {"bsonType": DATE_TYPE},
                            "currently_working": {"bsonType": ["bool", "null"]},
                            "description": {"bsonType": ["string", "null"]}
                        }
                    }
                },
                "education": {
                    "bsonType": ["array", "null"],
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "institution": {"bsonType": ["string", "null"]},
                            "degree": {"bsonType": ["string", "null"]},
                            "field_of_study": {"bsonType": ["string", "null"]},
                            "start_year": {"bsonType": NUMBER_TYPE},
                            "end_year": {"bsonType": NUMBER_TYPE},
                            "grade": {"bsonType": ["string", "null"]}
                        }
                    }
                },
                "projects": {
                    "bsonType": ["array", "null"],
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "title": {"bsonType": ["string", "null"]},
                            "description": {"bsonType": ["string", "null"]},
                            "technologies": {"bsonType": ["array", "null"], "items": {"bsonType": ["string", "null"]}},
                            "project_url": {"bsonType": ["string", "null"]},
                            "github_url": {"bsonType": ["string", "null"]}
                        }
                    }
                },
                "certifications": {
                    "bsonType": ["array", "null"],
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "name": {"bsonType": ["string", "null"]},
                            "organization": {"bsonType": ["string", "null"]},
                            "issued_date": {"bsonType": DATE_TYPE},
                            "credential_url": {"bsonType": ["string", "null"]}
                        }
                    }
                },
                "languages": {
                    "bsonType": ["array", "null"],
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "language": {"bsonType": ["string", "null"]},
                            "proficiency": {"bsonType": ["string", "null"]}
                        }
                    }
                },
                "candidate_profile_score": {"bsonType": NUMBER_TYPE},
                "createdAt": {"bsonType": DATE_TYPE},
                "updatedAt": {"bsonType": DATE_TYPE}
            }
        }
    },

    # 3. jobs
    "jobs": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title"],
            "properties": {
                "_id": {"bsonType": ID_TYPE},
                "recruiterId": {"bsonType": ID_TYPE, "description": "FK -> users._id"},
                "title": {"bsonType": "string"},
                "company": {"bsonType": ["string", "null"]},
                "location": {"bsonType": ["string", "null"]},
                "type": {"bsonType": ["string", "null"]},
                "workMode": {"bsonType": ["string", "null"]},
                "experience": {"bsonType": ["string", "double", "int", "long", "null"]},
                "skills": {"bsonType": ["array", "string", "null"], "items": {"bsonType": "string"}},
                "description": {"bsonType": ["string", "null"]},
                "must_have_requirements": {"bsonType": ["array", "null"], "items": {"bsonType": ["object", "string"]}},
                "scoring_weights": {
                    "bsonType": ["object", "null"],
                    "properties": {
                        "skills": {"bsonType": NUMBER_TYPE},
                        "experience": {"bsonType": NUMBER_TYPE},
                        "education": {"bsonType": NUMBER_TYPE},
                        "projects": {"bsonType": NUMBER_TYPE},
                        "certifications": {"bsonType": NUMBER_TYPE}
                    }
                },
                "salary": {
                    "bsonType": ["object", "null"],
                    "properties": {
                        "minimum": {"bsonType": NUMBER_TYPE},
                        "maximum": {"bsonType": NUMBER_TYPE},
                        "currency": {"bsonType": ["string", "null"]}
                    }
                },
                "status": {
                    "bsonType": ["string", "null"],
                    "enum": ["draft", "open", "closed", "published", None],
                    "description": "draft | open | closed | published"
                },
                "applicationDeadline": {"bsonType": DATE_TYPE},
                "createdAt": {"bsonType": DATE_TYPE},
                "updatedAt": {"bsonType": DATE_TYPE}
            }
        }
    },

    # 4. applications
    "applications": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["userId", "jobId"],
            "properties": {
                "_id": {"bsonType": ID_TYPE},
                "userId": {"bsonType": ID_TYPE, "description": "FK -> users._id"},
                "jobId": {"bsonType": ID_TYPE, "description": "FK -> jobs._id"},
                "cvDocumentId": {"bsonType": ID_TYPE, "description": "FK -> cv_documents._id"},
                "status": {
                    "bsonType": ["string", "null"]
                },
                "jobMatchScore": {"bsonType": NUMBER_TYPE},
                "candidateProfileScore": {"bsonType": NUMBER_TYPE},
                "candidate_snapshot": {"bsonType": ["object", "null"]},
                "job_snapshot": {"bsonType": ["object", "null"]},
                "analysis": {"bsonType": ["object", "null"]},
                "enterpriseEvaluation": {"bsonType": ["object", "null"]},
                "score_breakdown": {
                    "bsonType": ["object", "null"],
                    "properties": {
                        "skills_score": {"bsonType": NUMBER_TYPE},
                        "experience_score": {"bsonType": NUMBER_TYPE},
                        "education_score": {"bsonType": NUMBER_TYPE},
                        "projects_score": {"bsonType": NUMBER_TYPE},
                        "certifications_score": {"bsonType": NUMBER_TYPE}
                    }
                },
                "interviews_history": {
                    "bsonType": ["array", "null"],
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "interview_date": {"bsonType": DATE_TYPE},
                            "interview_type": {"bsonType": ["string", "null"]},
                            "interviewerId": {"bsonType": ID_TYPE},
                            "score": {"bsonType": NUMBER_TYPE},
                            "feedback": {"bsonType": ["string", "null"]},
                            "result": {"bsonType": ["string", "null"]}
                        }
                    }
                },
                "technical_assessments_history": {
                    "bsonType": ["array", "null"],
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "assessment_name": {"bsonType": ["string", "null"]},
                            "score": {"bsonType": NUMBER_TYPE},
                            "maximum_score": {"bsonType": NUMBER_TYPE},
                            "submitted_at": {"bsonType": DATE_TYPE},
                            "result": {"bsonType": ["string", "null"]}
                        }
                    }
                },
                "final_decision": {
                    "bsonType": "object",
                    "properties": {
                        "decision": {"bsonType": ["string", "null"], "enum": ["hired", "rejected", "pending", None]},
                        "reason": {"bsonType": ["string", "null"]},
                        "decided_by": {"bsonType": ID_TYPE},
                        "decided_at": {"bsonType": DATE_TYPE}
                    }
                },
                "appliedAt": {"bsonType": DATE_TYPE},
                "updatedAt": {"bsonType": DATE_TYPE}
            }
        }
    },

    # 5. cv_documents
    "cv_documents": {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {
                "_id": {"bsonType": ID_TYPE},
                "candidate_id": {"bsonType": ID_TYPE, "description": "FK -> users._id"},
                "file_name": {"bsonType": ["string", "null"]},
                "original_name": {"bsonType": ["string", "null"]},
                "content_type": {"bsonType": ["string", "null"]},
                "file_size": {"bsonType": NUMBER_TYPE},
                "content": {"bsonType": ["binData", "string", "null"]},
                "file_url": {"bsonType": ["string", "null"]},
                "extracted_text": {"bsonType": ["string", "null"]},
                "parsing_status": {
                    "bsonType": ["string", "null"],
                    "enum": ["pending", "processing", "completed", "failed", None]
                },
                "parsing_error": {"bsonType": ["string", "null"]},
                "raw_gemini_result": {"bsonType": ["object", "null"]},
                "parsed_data": {"bsonType": ["object", "null"]},
                "uploaded_at": {"bsonType": DATE_TYPE},
                "createdAt": {"bsonType": DATE_TYPE},
                "updatedAt": {"bsonType": DATE_TYPE}
            }
        }
    },

    # 6. evidence_snapshots
    "evidence_snapshots": {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {
                "_id": {"bsonType": ID_TYPE},
                "candidate_id": {"bsonType": ID_TYPE, "description": "FK -> users._id"},
                "platform": {
                    "bsonType": ["string", "null"],
                    "enum": ["github", "linkedin", "portfolio", None]
                },
                "profile_url": {"bsonType": ["string", "null"]},
                "username": {"bsonType": ["string", "null"]},
                "verification_status": {
                    "bsonType": ["string", "null"],
                    "enum": ["verified", "partial", "partially_verified", "verified_content", "verified_url", "not_connected", "failed", "success", "error", None]
                },
                "verified_at": {"bsonType": DATE_TYPE},
                "repos": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "name": {"bsonType": ["string", "null"]},
                            "url": {"bsonType": ["string", "null"]},
                            "description": {"bsonType": ["string", "null"]},
                            "language": {"bsonType": ["string", "null"]},
                            "stars": {"bsonType": NUMBER_TYPE},
                            "last_updated": {"bsonType": DATE_TYPE}
                        }
                    }
                },
                "top_languages": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "language": {"bsonType": ["string", "null"]},
                            "percentage": {"bsonType": NUMBER_TYPE}
                        }
                    }
                },
                "detected_skills": {"bsonType": "array", "items": {"bsonType": "string"}},
                "verification_score": {"bsonType": NUMBER_TYPE},
                "raw_response": {"bsonType": ["object", "null"]},
                "createdAt": {"bsonType": DATE_TYPE}
            }
        }
    },

    # 7. audit_logs
    "audit_logs": {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {
                "_id": {"bsonType": ID_TYPE},
                "userId": {"bsonType": ID_TYPE, "description": "FK -> users._id"},
                "performedBy": {"bsonType": ID_TYPE, "description": "FK -> users._id"},
                "documentId": {"bsonType": ID_TYPE, "description": "Changed document ID"},
                "action": {"bsonType": ["string", "null"]},
                "collectionName": {"bsonType": ["string", "null"]},
                "oldValue": {"bsonType": ["object", "null"]},
                "newValue": {"bsonType": ["object", "null"]},
                "reason": {"bsonType": ["string", "null"]},
                "ipAddress": {"bsonType": ["string", "null"]},
                "userAgent": {"bsonType": ["string", "null"]},
                "createdAt": {"bsonType": DATE_TYPE}
            }
        }
    },

    # 8. analysis_runs
    "analysis_runs": {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {
                "_id": {"bsonType": ID_TYPE},
                "candidateId": {"bsonType": ID_TYPE, "description": "FK -> users._id"},
                "jobId": {"bsonType": ID_TYPE, "description": "FK -> jobs._id"},
                "applicationId": {"bsonType": ID_TYPE, "description": "FK -> applications._id"},
                "cvDocumentId": {"bsonType": ID_TYPE, "description": "FK -> cv_documents._id"},
                "analysisType": {
                    "bsonType": ["string", "null"],
                    "enum": ["cv_analysis", "job_match", "profile_score", None]
                },
                "model": {"bsonType": ["string", "null"]},
                "promptVersion": {"bsonType": ["string", "null"]},
                "input_snapshot": {
                    "bsonType": ["object", "null"],
                    "properties": {
                        "candidate_skills": {"bsonType": "array", "items": {"bsonType": "string"}},
                        "job_requirements": {"bsonType": "array", "items": {"bsonType": "string"}},
                        "cv_text": {"bsonType": ["string", "null"]}
                    }
                },
                "result": {
                    "bsonType": ["object", "null"],
                    "properties": {
                        "total_score": {"bsonType": NUMBER_TYPE},
                        "skills_score": {"bsonType": NUMBER_TYPE},
                        "experience_score": {"bsonType": NUMBER_TYPE},
                        "education_score": {"bsonType": NUMBER_TYPE},
                        "strengths": {"bsonType": "array", "items": {"bsonType": "string"}},
                        "weaknesses": {"bsonType": "array", "items": {"bsonType": "string"}},
                        "missing_skills": {"bsonType": "array", "items": {"bsonType": "string"}},
                        "recommendation": {"bsonType": ["string", "null"]}
                    }
                },
                "status": {
                    "bsonType": ["string", "null"],
                    "enum": ["pending", "completed", "failed", None]
                },
                "error_message": {"bsonType": ["string", "null"]},
                "processing_time_ms": {"bsonType": NUMBER_TYPE},
                "createdAt": {"bsonType": DATE_TYPE}
            }
        }
    }
}


def setup_collections_and_schemas():
    """Create collections and apply JSON Schema validators."""
    existing = db.list_collection_names()
    print("=" * 65)
    print(" TalentVerify AI – Complete 8-Collection Database Schema Setup")
    print("=" * 65)
    
    for col_name, schema in SCHEMAS.items():
        if col_name not in existing:
            db.create_collection(
                col_name,
                validator=schema,
                validationLevel="moderate",
                validationAction="warn"
            )
            print(f"[+] Created collection with validator: {col_name}")
        else:
            try:
                db.command(
                    "collMod",
                    col_name,
                    validator=schema,
                    validationLevel="moderate",
                    validationAction="warn"
                )
                print(f"[OK] Updated schema validator: {col_name}")
            except Exception as e:
                print(f"[!] Warning updating validator for {col_name}: {e}")

    print("\n" + "=" * 65)
    print(" Configuring Primary, Foreign Key, Unique & Compound Indexes")
    print("=" * 65)

    def safe_index(collection, keys, **kwargs):
        try:
            collection.create_index(keys, **kwargs)
        except Exception as e:
            # Continue if index exists with similar parameters
            pass

    # 1. users
    # PK: _id, Unique: email
    safe_index(db.users, [("email", ASCENDING)], unique=True)
    safe_index(db.users, [("id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.users, [("role", ASCENDING)])
    print("  -> users: email (UNIQUE), id (sparse unique), role")

    # 2. candidate_profiles
    # PK: _id, FK: user_id -> users._id, Unique: user_id
    safe_index(db.candidate_profiles, [("user_id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.candidate_profiles, [("id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.candidate_profiles, [("personal_info.email", ASCENDING)])
    print("  -> candidate_profiles: user_id (UNIQUE FK), id (sparse unique), personal_info.email")

    # 3. jobs
    # PK: _id, FK: recruiterId -> users._id
    safe_index(db.jobs, [("id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.jobs, [("recruiterId", ASCENDING)])
    safe_index(db.jobs, [("status", ASCENDING)])
    safe_index(db.jobs, [("createdAt", DESCENDING)])
    print("  -> jobs: recruiterId (FK), status, createdAt, id (sparse unique)")

    # 4. applications
    # PK: _id, FK: userId, jobId, cvDocumentId
    # Unique Compound: userId + jobId
    safe_index(db.applications, [("userId", ASCENDING), ("jobId", ASCENDING)], unique=True, sparse=True)
    safe_index(db.applications, [("id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.applications, [("userId", ASCENDING)])
    safe_index(db.applications, [("jobId", ASCENDING)])
    safe_index(db.applications, [("cvDocumentId", ASCENDING)])
    safe_index(db.applications, [("status", ASCENDING)])
    print("  -> applications: (userId + jobId) (UNIQUE COMPOUND), userId (FK), jobId (FK), cvDocumentId (FK), status")

    # 5. cv_documents
    # PK: _id, FK: candidate_id -> users._id
    safe_index(db.cv_documents, [("id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.cv_documents, [("candidate_id", ASCENDING)])
    safe_index(db.cv_documents, [("uploaded_at", DESCENDING)])
    safe_index(db.cv_documents, [("parsing_status", ASCENDING)])
    print("  -> cv_documents: candidate_id (FK), uploaded_at, parsing_status, id (sparse unique)")

    # 6. evidence_snapshots
    # PK: _id, FK: candidate_id -> users._id
    # Compound: candidate_id + platform + verified_at
    safe_index(db.evidence_snapshots, [("id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.evidence_snapshots, [
        ("candidate_id", ASCENDING),
        ("platform", ASCENDING),
        ("verified_at", DESCENDING)
    ])
    safe_index(db.evidence_snapshots, [("candidate_id", ASCENDING), ("platform", ASCENDING)])
    print("  -> evidence_snapshots: (candidate_id + platform + verified_at) (COMPOUND), candidate_id (FK)")

    # 7. audit_logs
    # PK: _id, FK: userId, performedBy
    # Logical reference: documentId + collectionName
    safe_index(db.audit_logs, [("id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.audit_logs, [("userId", ASCENDING)])
    safe_index(db.audit_logs, [("performedBy", ASCENDING)])
    safe_index(db.audit_logs, [
        ("collectionName", ASCENDING),
        ("documentId", ASCENDING),
        ("createdAt", DESCENDING)
    ])
    print("  -> audit_logs: userId (FK), performedBy (FK), (collectionName + documentId + createdAt) (COMPOUND)")

    # 8. analysis_runs
    # PK: _id, FK: candidateId, jobId, applicationId, cvDocumentId
    safe_index(db.analysis_runs, [("id", ASCENDING)], unique=True, sparse=True)
    safe_index(db.analysis_runs, [("candidateId", ASCENDING)])
    safe_index(db.analysis_runs, [("jobId", ASCENDING)])
    safe_index(db.analysis_runs, [("applicationId", ASCENDING)])
    safe_index(db.analysis_runs, [("cvDocumentId", ASCENDING)])
    safe_index(db.analysis_runs, [("createdAt", DESCENDING)])
    print("  -> analysis_runs: candidateId (FK), jobId (FK), applicationId (FK), cvDocumentId (FK), createdAt")

    print("\n" + "=" * 65)
    print(" Summary of Configured Collections:")
    print("=" * 65)
    for col in sorted(SCHEMAS.keys()):
        count = db[col].count_documents({})
        indexes = list(db[col].index_information().keys())
        print(f"  * {col:<22} : {count:>3} docs | {len(indexes)} indexes {indexes}")
    
    print("\n[SUCCESS] TalentVerify AI complete schema and indexes configured successfully!")


if __name__ == "__main__":
    setup_collections_and_schemas()
