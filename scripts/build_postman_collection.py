import json
from pathlib import Path

collection = {
    "info": {
        "_postman_id": "talentverify-8-collections-crud-v3",
        "name": "TalentVerify AI - 8 Collections CRUD API",
        "description": "Production Postman Collection for TalentVerify AI. Contains exact CRUD operations (findAll, findOne, save, update, deleteOne, deleteAll) for all 8 collections.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "http://127.0.0.1:8000", "type": "string"},
        {"key": "token", "value": "REC-001", "type": "string"},
        {"key": "userId", "value": "REC-001", "type": "string"},
        {"key": "candidateId", "value": "CAND-001", "type": "string"},
        {"key": "jobId", "value": "JOB-001", "type": "string"},
        {"key": "applicationId", "value": "APP-001", "type": "string"},
        {"key": "cvId", "value": "CV-001", "type": "string"},
        {"key": "snapshotId", "value": "SNAP-001", "type": "string"},
        {"key": "auditId", "value": "AUDIT-001", "type": "string"},
        {"key": "runId", "value": "RUN-APP-001", "type": "string"}
    ],
    "item": []
}

# 0. Authentication & Session
collection["item"].append({
    "name": "0. Authentication & Session",
    "item": [
        {
            "name": "Health Check",
            "request": {
                "method": "GET",
                "url": {
                    "raw": "{{baseUrl}}/api/health",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", "health"]
                }
            }
        },
        {
            "name": "Login Recruiter (Auto Token Save)",
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({"mode": "login", "email": "recruiter@gmail.com", "password": "abcd123@"}, indent=2)
                },
                "url": {
                    "raw": "{{baseUrl}}/api/auth",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", "auth"]
                }
            },
            "event": [{
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "var data = pm.response.json();",
                        "if (data.token) {",
                        "    pm.collectionVariables.set('token', data.token);",
                        "    pm.collectionVariables.set('userId', data.user.id);",
                        "}"
                    ]
                }
            }]
        },
        {
            "name": "Login Candidate (Auto Token Save)",
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({"mode": "login", "email": "candidate@gmail.com", "password": "abcd123@"}, indent=2)
                },
                "url": {
                    "raw": "{{baseUrl}}/api/auth",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", "auth"]
                }
            },
            "event": [{
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "var data = pm.response.json();",
                        "if (data.token) {",
                        "    pm.collectionVariables.set('token', data.token);",
                        "    pm.collectionVariables.set('candidateId', data.user.id);",
                        "}"
                    ]
                }
            }]
        },
        {
            "name": "Get Current App Data",
            "request": {
                "method": "GET",
                "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
                "url": {
                    "raw": "{{baseUrl}}/api/app-data?token={{token}}",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", "app-data"],
                    "query": [{"key": "token", "value": "{{token}}"}]
                }
            }
        }
    ]
})

# All 8 Collections configuration with exact valid document schemas
configs = [
    {
        "folder": "1. Users (users)",
        "col": "users",
        "var": "userId",
        "default_id": "REC-001",
        "save_body": {
            "name": "Nimal Perera",
            "email": "nimal.perera@example.com",
            "role": "candidate",
            "password": "abcd123@",
            "headline": "Full Stack Developer",
            "location": "Colombo, Sri Lanka",
            "phone": "+94 77 111 2222",
            "isActive": True
        },
        "update_body": {
            "headline": "Senior Full Stack Tech Lead",
            "phone": "+94 77 123 4567",
            "location": "Colombo, Sri Lanka"
        },
        "del_all_filter": "role=test"
    },
    {
        "folder": "2. Candidate Profiles (candidate_profiles)",
        "col": "candidate_profiles",
        "var": "candidateId",
        "default_id": "CAND-001",
        "save_body": {
            "user_id": "CAND-001",
            "personal_info": {
                "full_name": "Nuwan Jayasuriya",
                "email": "nuwan.j@example.com",
                "headline": "Senior Cloud Backend Engineer",
                "location": "Kandy, Sri Lanka",
                "phone": "+94 71 555 4321",
                "bio": "Expert in FastAPI, Docker, and Microservices architecture."
            },
            "technical_skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "AWS"],
            "soft_skills": ["Leadership", "Problem Solving", "Communication"],
            "candidate_profile_score": 85.0
        },
        "update_body": {
            "personal_info": {
                "headline": "Principal Architect & Lead Engineer"
            },
            "candidate_profile_score": 90.0
        },
        "del_all_filter": "source=test"
    },
    {
        "folder": "3. Jobs (jobs)",
        "col": "jobs",
        "var": "jobId",
        "default_id": "JOB-001",
        "save_body": {
            "recruiterId": "REC-001",
            "title": "Senior AI Systems Engineer",
            "company": "TalentVerify Technologies",
            "location": "Remote",
            "type": "Full-time",
            "workMode": "Remote",
            "experience": 3,
            "skills": "Python, Machine Learning, TensorFlow, NLP, FastAPI, SQL",
            "description": "Design and build AI validation models, NLP pipelines, and document matching services.",
            "status": "open",
            "salary": {"minimum": 200000, "maximum": 350000, "currency": "LKR"}
        },
        "update_body": {
            "title": "Lead AI Systems Engineer (Updated)",
            "experience": 4,
            "status": "open"
        },
        "del_all_filter": "status=draft"
    },
    {
        "folder": "4. Applications (applications)",
        "col": "applications",
        "var": "applicationId",
        "default_id": "APP-001",
        "save_body": {
            "userId": "CAND-001",
            "jobId": "JOB-001",
            "cvDocumentId": "CV-001",
            "status": "Under review",
            "score": 88.0,
            "analysisType": "job_match",
            "appliedAt": "2026-09-24T12:00:00+00:00"
        },
        "update_body": {
            "status": "Shortlisted",
            "notes": "Candidate passed initial review. Scheduled for technical interview."
        },
        "del_all_filter": "status=Rejected"
    },
    {
        "folder": "5. CV Documents (cv_documents)",
        "col": "cv_documents",
        "var": "cvId",
        "default_id": "CV-001",
        "save_body": {
            "candidate_id": "CAND-001",
            "file_name": "Demo_Candidate_FullStack_CV.pdf",
            "content_type": "application/pdf",
            "file_size": 40398,
            "parsing_status": "completed",
            "extracted_skills": ["React", "FastAPI", "Python", "SQL", "Docker"],
            "structured_profile": {
                "experience_years": 3.0,
                "education_level": "Bachelor's Degree"
            }
        },
        "update_body": {
            "parsing_status": "completed",
            "notes": "CV verified and parsed successfully."
        },
        "del_all_filter": "parsing_status=failed"
    },
    {
        "folder": "6. Evidence Snapshots (evidence_snapshots)",
        "col": "evidence_snapshots",
        "var": "snapshotId",
        "default_id": "SNAP-001",
        "save_body": {
            "candidate_id": "CAND-001",
            "platform": "github",
            "username": "demo-candidate",
            "profile_url": "https://github.com/demo-candidate",
            "verification_status": "verified",
            "verification_score": 92.0,
            "verified_technologies": ["React", "Python", "FastAPI", "TypeScript", "Docker"],
            "verified_at": "2026-09-24T12:00:00+00:00"
        },
        "update_body": {
            "verification_status": "verified",
            "verification_score": 95.0
        },
        "del_all_filter": "platform=test"
    },
    {
        "folder": "7. Audit Logs (audit_logs)",
        "col": "audit_logs",
        "var": "auditId",
        "default_id": "AUDIT-001",
        "save_body": {
            "action": "application_status_updated",
            "userId": "REC-001",
            "performedBy": "REC-001",
            "documentId": "APP-001",
            "collectionName": "applications",
            "details": {
                "previous_status": "Under review",
                "new_status": "Shortlisted"
            }
        },
        "update_body": {
            "notes": "Reviewed and acknowledged by recruiter team."
        },
        "del_all_filter": "action=test_action"
    },
    {
        "folder": "8. Analysis Runs (analysis_runs)",
        "col": "analysis_runs",
        "var": "runId",
        "default_id": "RUN-APP-001",
        "save_body": {
            "candidateId": "CAND-001",
            "jobId": "JOB-001",
            "applicationId": "APP-001",
            "analysisType": "job_match",
            "score": 88.0,
            "breakdown": {
                "skills": 20.0,
                "experience": 15.0,
                "education": 10.0,
                "projects": 10.0
            },
            "runAt": "2026-09-24T12:00:00+00:00"
        },
        "update_body": {
            "score": 90.0,
            "notes": "Score updated after manual skills validation."
        },
        "del_all_filter": "analysisType=test"
    }
]

for cfg in configs:
    c_name = cfg["col"]
    v_name = cfg["var"]
    f_name = cfg["folder"]

    folder_item = {
        "name": f_name,
        "item": [
            {
                "name": f"1. findAll {c_name}",
                "request": {
                    "method": "GET",
                    "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
                    "url": {
                        "raw": "{{baseUrl}}/api/crud/" + c_name + "?limit=50&skip=0",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "crud", c_name],
                        "query": [{"key": "limit", "value": "50"}, {"key": "skip", "value": "0"}]
                    }
                }
            },
            {
                "name": f"2. findOne {c_name} by ID",
                "request": {
                    "method": "GET",
                    "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
                    "url": {
                        "raw": "{{baseUrl}}/api/crud/" + c_name + "/{{" + v_name + "}}",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "crud", c_name, "{{" + v_name + "}}"]
                    }
                }
            },
            {
                "name": f"3. save (create) {c_name}",
                "request": {
                    "method": "POST",
                    "header": [
                        {"key": "Content-Type", "value": "application/json"},
                        {"key": "Authorization", "value": "Bearer {{token}}"}
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps(cfg["save_body"], indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/crud/" + c_name,
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "crud", c_name]
                    }
                },
                "event": [{
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": [
                            "var res = pm.response.json();",
                            "if (res.id) { pm.collectionVariables.set('" + v_name + "', res.id); }"
                        ]
                    }
                }]
            },
            {
                "name": f"4. update {c_name} by ID",
                "request": {
                    "method": "PUT",
                    "header": [
                        {"key": "Content-Type", "value": "application/json"},
                        {"key": "Authorization", "value": "Bearer {{token}}"}
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps(cfg["update_body"], indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/crud/" + c_name + "/{{" + v_name + "}}",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "crud", c_name, "{{" + v_name + "}}"]
                    }
                }
            },
            {
                "name": f"5. deleteOne {c_name} by ID",
                "request": {
                    "method": "DELETE",
                    "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
                    "url": {
                        "raw": "{{baseUrl}}/api/crud/" + c_name + "/{{" + v_name + "}}",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "crud", c_name, "{{" + v_name + "}}"]
                    }
                }
            },
            {
                "name": f"6. deleteAll {c_name} (Safety: confirm=true)",
                "request": {
                    "method": "DELETE",
                    "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
                    "url": {
                        "raw": "{{baseUrl}}/api/crud/" + c_name + "?confirm=true&" + cfg["del_all_filter"],
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "crud", c_name],
                        "query": [{"key": "confirm", "value": "true"}]
                    }
                }
            }
        ]
    }
    collection["item"].append(folder_item)

# Save collection files
Path("postman/collections").mkdir(parents=True, exist_ok=True)
with open("TalentVerify_CRUD_API.postman_collection.json", "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=2)
with open("postman/collections/TalentVerify_CRUD_API.postman_collection.json", "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=2)

print("SUCCESS: 8 Collections Postman Collection built with", len(collection["item"]), "folders!")
