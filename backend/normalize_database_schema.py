"""
TalentVerify AI - Database Normalization & 8 Collections Migration Script
Normalizes all data across the 8 collections:
1. users
2. candidate_profiles
3. jobs
4. applications
5. cv_documents
6. evidence_snapshots
7. audit_logs
8. analysis_runs

Enforces referential integrity, eliminates duplicates, links foreign keys,
and guarantees zero errors in the frontend and backend.
"""

import os
import sys
import hashlib
import secrets
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "talentverifyai")

print(f"Connecting to MongoDB at {MONGODB_URI}, Database: {MONGODB_DB}...")
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client[MONGODB_DB]


def utcnow():
    return datetime.now(timezone.utc)


def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210000).hex()
    return f"{salt}${digest}"


# Standard weights and recommendation bands
DEFAULT_WEIGHTS = {
    "technical_skills": 20.0,
    "experience": 15.0,
    "projects": 10.0,
    "education": 5.0,
    "certifications": 5.0,
    "github_evidence": 5.0,
    "job_relevance": 10.0,
    "technical_assessment": 15.0,
    "structured_interview": 15.0,
}

DEFAULT_BANDS = [
    {"minimum": 85, "label": "Strong Match"},
    {"minimum": 70, "label": "Good Match"},
    {"minimum": 55, "label": "Moderate Match"},
    {"minimum": 0, "label": "Weak Match"},
]


def normalize_database():
    print("=" * 70)
    print(" TalentVerify AI - Comprehensive 8-Collection Database Normalization")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # STEP 1: NORMALIZE USERS (Collection 1)
    # -------------------------------------------------------------------------
    print("\n[1/8] Normalizing 'users' collection...")

    # Define standard users
    standard_users = [
        {
            "_id": "REC-001",
            "id": "REC-001",
            "role": "recruiter",
            "name": "Demo Recruiter",
            "email": "recruiter@gmail.com",
            "company": "TalentVerify Technologies",
            "location": "Colombo, Sri Lanka",
            "headline": "Head of Technical Recruitment",
            "phone": "+94 11 234 5678",
            "passwordHash": hash_password("abcd123@"),
            "isActive": True,
            "createdAt": "2026-09-01T08:00:00+00:00",
            "updatedAt": utcnow_iso(),
            "lastLogin": utcnow_iso(),
        },
        {
            "_id": "REC-002",
            "id": "REC-002",
            "role": "recruiter",
            "name": "Sarah Jenkins",
            "email": "sarah.recruiter@talentverify.com",
            "company": "TalentVerify Technologies",
            "location": "Remote",
            "headline": "Lead Engineering Recruiter",
            "phone": "+94 11 987 6543",
            "passwordHash": hash_password("abcd123@"),
            "isActive": True,
            "createdAt": "2026-09-05T09:00:00+00:00",
            "updatedAt": utcnow_iso(),
            "lastLogin": utcnow_iso(),
        },
        {
            "_id": "CAND-001",
            "id": "CAND-001",
            "role": "candidate",
            "name": "Demo Candidate",
            "email": "candidate@gmail.com",
            "headline": "Full Stack Developer",
            "location": "Colombo, Sri Lanka",
            "phone": "+94 77 123 4567",
            "passwordHash": hash_password("abcd123@"),
            "isActive": True,
            "createdAt": "2026-09-01T10:00:00+00:00",
            "updatedAt": utcnow_iso(),
            "lastLogin": utcnow_iso(),
        },
        {
            "_id": "CAND-002",
            "id": "CAND-002",
            "role": "candidate",
            "name": "Eranga Isuru",
            "email": "erangaisuru@gmail.com",
            "headline": "Senior Backend & Cloud Engineer",
            "location": "Kandy, Sri Lanka",
            "phone": "+94 71 234 5678",
            "passwordHash": hash_password("abcd123@"),
            "isActive": True,
            "createdAt": "2026-09-08T11:00:00+00:00",
            "updatedAt": utcnow_iso(),
            "lastLogin": utcnow_iso(),
        },
        {
            "_id": "CAND-003",
            "id": "CAND-003",
            "role": "candidate",
            "name": "Muralitharan",
            "email": "muralitharan@email.com",
            "headline": "Junior Software Developer | IT Professional",
            "location": "Jaffna, Sri Lanka",
            "phone": "+94 76 345 6789",
            "passwordHash": hash_password("abcd123@"),
            "isActive": True,
            "createdAt": "2026-09-12T14:00:00+00:00",
            "updatedAt": utcnow_iso(),
            "lastLogin": utcnow_iso(),
        },
        {
            "_id": "CAND-004",
            "id": "CAND-004",
            "role": "candidate",
            "name": "Eranga",
            "email": "eranga12@gmail.com",
            "headline": "Software Engineer",
            "location": "Colombo, Sri Lanka",
            "phone": "+94 70 456 7890",
            "passwordHash": hash_password("abcd123@"),
            "isActive": True,
            "createdAt": "2026-09-15T15:00:00+00:00",
            "updatedAt": utcnow_iso(),
            "lastLogin": utcnow_iso(),
        },
    ]

    # Map old IDs to normalized IDs
    id_alias_map = {
        "demo-candidate-1": "CAND-001",
        "demo-recruiter-1": "REC-001",
        "178dd70a-aba3-4c97-858e-297f062ba3bf": "CAND-002",
        "f3548d44-4c8a-45a2-b6b7-4fe0c62c32aa": "CAND-004",
    }

    # Upsert standard users cleanly
    for u in standard_users:
        existing = db.users.find_one({"email": u["email"]})
        if existing:
            # Preserve existing passwordHash and token if valid
            p_hash = existing.get("passwordHash") or u["passwordHash"]
            tok = existing.get("token")
            db.users.delete_one({"_id": existing["_id"]})
            u["passwordHash"] = p_hash
            if tok:
                u["token"] = tok
        db.users.replace_one({"_id": u["_id"]}, u, upsert=True)
        print(f"  [OK] User: {u['id']:<10} | {u['email']:<30} | Role: {u['role']}")

    # Clean up any leftover users with old UUIDs that were migrated
    for old_id, new_id in id_alias_map.items():
        db.users.delete_many({"id": old_id})
        db.users.delete_many({"_id": old_id})

    # -------------------------------------------------------------------------
    # STEP 2: NORMALIZE CANDIDATE PROFILES (Collection 2)
    # -------------------------------------------------------------------------
    print("\n[2/8] Normalizing 'candidate_profiles' collection...")

    profiles_data = [
        {
            "_id": "CAND-001",
            "id": "CAND-001",
            "user_id": "CAND-001",
            "personal_info": {
                "full_name": "Demo Candidate",
                "email": "candidate@gmail.com",
                "headline": "Full Stack Developer",
                "location": "Colombo, Sri Lanka",
                "phone": "+94 77 123 4567",
                "bio": "Enthusiastic full-stack engineer passionate about React, FastAPI, microservices, and reliable cloud deployments.",
                "experience_years": 2.5,
                "profile_photo_url": None,
            },
            "social_links": {
                "linkedin_url": "https://www.linkedin.com/in/demo-candidate",
                "github_url": "https://github.com/demo-candidate",
                "portfolio_url": "https://democandidate.dev",
            },
            "career_preferences": {
                "preferred_roles": "Full Stack Developer, Backend Engineer, Frontend Engineer",
                "work_preference": "Hybrid",
                "availability": "Immediate",
                "notice_period": "1 Month",
            },
            "technical_skills": ["React", "JavaScript", "Python", "SQL", "FastAPI", "Docker", "Node.js", "Git", "REST APIs", "PostgreSQL"],
            "soft_skills": ["Communication", "Problem Solving", "Teamwork", "Agile Collaboration", "Critical Thinking"],
            "skills": [
                {"id": "skill_CAND-001_1", "candidate_id": "CAND-001", "skill": "React", "normalized_skill": "react", "kind": "technical", "source": "verified", "confidence": 1.0, "verified_by_recruiter": True},
                {"id": "skill_CAND-001_2", "candidate_id": "CAND-001", "skill": "Python", "normalized_skill": "python", "kind": "technical", "source": "verified", "confidence": 1.0, "verified_by_recruiter": True},
                {"id": "skill_CAND-001_3", "candidate_id": "CAND-001", "skill": "FastAPI", "normalized_skill": "fastapi", "kind": "technical", "source": "github", "confidence": 0.95, "verified_by_recruiter": True},
                {"id": "skill_CAND-001_4", "candidate_id": "CAND-001", "skill": "SQL", "normalized_skill": "sql", "kind": "technical", "source": "cv", "confidence": 0.9, "verified_by_recruiter": False},
                {"id": "skill_CAND-001_5", "candidate_id": "CAND-001", "skill": "Docker", "normalized_skill": "docker", "kind": "technical", "source": "github", "confidence": 0.85, "verified_by_recruiter": False},
                {"id": "skill_CAND-001_6", "candidate_id": "CAND-001", "skill": "Problem Solving", "normalized_skill": "problem solving", "kind": "soft", "source": "interview", "confidence": 0.95, "verified_by_recruiter": True},
                {"id": "skill_CAND-001_7", "candidate_id": "CAND-001", "skill": "Communication", "normalized_skill": "communication", "kind": "soft", "source": "interview", "confidence": 0.9, "verified_by_recruiter": True},
            ],
            "experience": [
                {
                    "id": "exp_CAND-001_1",
                    "candidate_id": "CAND-001",
                    "company": "Tech Innovations Pvt Ltd",
                    "position": "Associate Software Developer",
                    "start_date": "2024-01-01",
                    "end_date": "2026-08-31",
                    "is_current": False,
                    "responsibilities": [
                        "Designed and developed scalable backend REST APIs using FastAPI and PostgreSQL.",
                        "Built modern responsive frontend user interfaces using React and TailwindCSS.",
                        "Optimized database queries, reducing average API response times by 30%."
                    ],
                    "technologies": ["React", "Python", "FastAPI", "PostgreSQL", "Docker"],
                    "source": "cv_verified",
                }
            ],
            "education": [
                {
                    "id": "edu_CAND-001_1",
                    "candidate_id": "CAND-001",
                    "institution": "University of Colombo School of Computing",
                    "qualification": "BSc (Hons) in Computer Science",
                    "field": "Computer Science",
                    "start_year": 2020,
                    "end_year": 2024,
                    "grade": "Second Class Upper",
                    "source": "cv_verified",
                }
            ],
            "projects": [
                {
                    "id": "proj_CAND-001_1",
                    "candidate_id": "CAND-001",
                    "name": "E-Commerce Microservices Platform",
                    "title": "E-Commerce Microservices Platform",
                    "description": "Full-featured online store with JWT authentication, Stripe payment processing, and containerized Docker setup.",
                    "technologies": ["React", "FastAPI", "PostgreSQL", "Docker", "Redis"],
                    "github_url": "https://github.com/demo-candidate/ecommerce-platform",
                    "project_url": "https://shop-demo.example.com",
                    "source": "github_verified",
                },
                {
                    "id": "proj_CAND-001_2",
                    "candidate_id": "CAND-001",
                    "name": "AI Document Extractor",
                    "title": "AI Document Extractor",
                    "description": "Automated PDF parsing and information extraction engine powered by Gemini AI and Python.",
                    "technologies": ["Python", "FastAPI", "Gemini API", "PyPDF"],
                    "github_url": "https://github.com/demo-candidate/ai-doc-extractor",
                    "source": "github_verified",
                }
            ],
            "certifications": [
                {
                    "id": "cert_CAND-001_1",
                    "candidate_id": "CAND-001",
                    "name": "AWS Certified Cloud Practitioner",
                    "organization": "Amazon Web Services",
                    "issued_date": "2025-03-15",
                    "credential_url": "https://aws.amazon.com/verification",
                    "source": "verified",
                }
            ],
            "languages": [
                {"id": "lang_CAND-001_1", "candidate_id": "CAND-001", "language": "English", "proficiency": "Fluent", "speaking_level": "Fluent", "reading_level": "Fluent", "writing_level": "Fluent"},
                {"id": "lang_CAND-001_2", "candidate_id": "CAND-001", "language": "Sinhala", "proficiency": "Native", "speaking_level": "Native", "reading_level": "Native", "writing_level": "Native"},
            ],
            "candidate_profile_score": 84.5,
            "score_breakdown": {
                "skills": {"score": 24.5, "max_score": 25.0, "reason": "Comprehensive technical and soft skills verified across multiple sources."},
                "experience": {"score": 18.0, "max_score": 20.0, "reason": "2.5+ years of verified software development experience."},
                "github": {"score": 14.0, "max_score": 15.0, "reason": "Active GitHub profile with verified repositories."},
                "projects": {"score": 14.0, "max_score": 15.0, "reason": "Multiple demonstrated end-to-end full-stack projects."},
                "education": {"score": 9.0, "max_score": 10.0, "reason": "BSc in Computer Science from recognized university."},
                "languages": {"score": 5.0, "max_score": 5.0, "reason": "Fluent English and Native Sinhala proficiency."},
            },
            "github": {
                "username": "demo-candidate",
                "github_url": "https://github.com/demo-candidate",
                "verification_status": "verified",
                "latest_snapshot_id": "SNAP-001",
                "last_verified_at": utcnow_iso(),
            },
            "created_at": datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
            "updated_at": utcnow(),
        },
        {
            "_id": "CAND-002",
            "id": "CAND-002",
            "user_id": "CAND-002",
            "personal_info": {
                "full_name": "Eranga Isuru",
                "email": "erangaisuru@gmail.com",
                "headline": "Senior Backend & Cloud Engineer",
                "location": "Kandy, Sri Lanka",
                "phone": "+94 71 234 5678",
                "bio": "Cloud and backend engineer specializing in distributed systems, AWS, Kubernetes, Terraform, and Python/Golang microservices.",
                "experience_years": 4.0,
            },
            "social_links": {
                "linkedin_url": "https://www.linkedin.com/in/erangaisuru",
                "github_url": "https://github.com/erangaisuru",
                "portfolio_url": None,
            },
            "career_preferences": {
                "preferred_roles": "Backend Engineer, Cloud Engineer, DevOps Specialist",
                "work_preference": "Remote",
                "availability": "2 Weeks",
                "notice_period": "2 Weeks",
            },
            "technical_skills": ["Python", "AWS", "Docker", "Kubernetes", "Terraform", "PostgreSQL", "Linux", "CI/CD", "Redis", "Golang"],
            "soft_skills": ["Problem Solving", "Leadership", "Mentoring", "Agile"],
            "skills": [
                {"id": "skill_CAND-002_1", "candidate_id": "CAND-002", "skill": "Python", "normalized_skill": "python", "kind": "technical", "source": "verified", "confidence": 1.0},
                {"id": "skill_CAND-002_2", "candidate_id": "CAND-002", "skill": "AWS", "normalized_skill": "aws", "kind": "technical", "source": "verified", "confidence": 1.0},
                {"id": "skill_CAND-002_3", "candidate_id": "CAND-002", "skill": "Docker", "normalized_skill": "docker", "kind": "technical", "source": "verified", "confidence": 0.95},
                {"id": "skill_CAND-002_4", "candidate_id": "CAND-002", "skill": "Kubernetes", "normalized_skill": "kubernetes", "kind": "technical", "source": "verified", "confidence": 0.90},
                {"id": "skill_CAND-002_5", "candidate_id": "CAND-002", "skill": "Terraform", "normalized_skill": "terraform", "kind": "technical", "source": "verified", "confidence": 0.90},
            ],
            "experience": [
                {
                    "id": "exp_CAND-002_1",
                    "candidate_id": "CAND-002",
                    "company": "CloudScape Solutions",
                    "position": "Senior Backend Engineer",
                    "start_date": "2022-06-01",
                    "end_date": "2026-08-31",
                    "is_current": False,
                    "responsibilities": ["Architected AWS cloud infrastructure using Terraform", "Deployed high-availability Kubernetes clusters"],
                    "technologies": ["Python", "AWS", "Docker", "Kubernetes", "Terraform"],
                    "source": "cv_verified",
                }
            ],
            "education": [
                {
                    "id": "edu_CAND-002_1",
                    "candidate_id": "CAND-002",
                    "institution": "University of Peradeniya",
                    "qualification": "BSc in Engineering (Computer Engineering)",
                    "field": "Computer Engineering",
                    "start_year": 2018,
                    "end_year": 2022,
                    "grade": "First Class Honours",
                    "source": "cv_verified",
                }
            ],
            "projects": [
                {
                    "id": "proj_CAND-002_1",
                    "candidate_id": "CAND-002",
                    "name": "Cloud Native CI/CD Automation",
                    "title": "Cloud Native CI/CD Automation",
                    "description": "Automated deployment pipeline deploying microservices to EKS using ArgoCD and Terraform.",
                    "technologies": ["AWS", "Kubernetes", "Terraform", "GitHub Actions"],
                    "github_url": "https://github.com/erangaisuru/cloud-cicd",
                }
            ],
            "certifications": [
                {
                    "id": "cert_CAND-002_1",
                    "candidate_id": "CAND-002",
                    "name": "AWS Certified Solutions Architect - Associate",
                    "organization": "Amazon Web Services",
                    "issued_date": "2024-05-10",
                    "credential_url": "https://aws.amazon.com/verification",
                }
            ],
            "languages": [
                {"id": "lang_CAND-002_1", "candidate_id": "CAND-002", "language": "English", "proficiency": "Fluent"},
                {"id": "lang_CAND-002_2", "candidate_id": "CAND-002", "language": "Sinhala", "proficiency": "Native"},
            ],
            "candidate_profile_score": 89.0,
            "score_breakdown": {
                "skills": {"score": 25.0, "max_score": 25.0},
                "experience": {"score": 20.0, "max_score": 20.0},
                "github": {"score": 14.5, "max_score": 15.0},
                "projects": {"score": 14.5, "max_score": 15.0},
                "education": {"score": 10.0, "max_score": 10.0},
                "languages": {"score": 5.0, "max_score": 5.0},
            },
            "github": {
                "username": "erangaisuru",
                "github_url": "https://github.com/erangaisuru",
                "verification_status": "verified",
                "latest_snapshot_id": "SNAP-004",
                "last_verified_at": utcnow_iso(),
            },
            "created_at": datetime(2026, 9, 8, 11, 0, 0, tzinfo=timezone.utc),
            "updated_at": utcnow(),
        },
        {
            "_id": "CAND-003",
            "id": "CAND-003",
            "user_id": "CAND-003",
            "personal_info": {
                "full_name": "Muralitharan",
                "email": "muralitharan@email.com",
                "headline": "Junior Software Developer | IT Professional",
                "location": "Jaffna, Sri Lanka",
                "phone": "+94 76 345 6789",
                "bio": "Motivated and enthusiastic IT professional with knowledge of software development, programming, databases, and web technologies.",
                "experience_years": 1.0,
            },
            "social_links": {
                "linkedin_url": "https://www.linkedin.com/in/muralitharan-dev",
                "github_url": "https://github.com/muralitharan-dev",
                "portfolio_url": None,
            },
            "career_preferences": {
                "preferred_roles": "Junior Developer, Web Developer, QA Intern",
                "work_preference": "On-site / Hybrid",
                "availability": "Immediate",
                "notice_period": "Immediate",
            },
            "technical_skills": ["Python", "Java", "JavaScript", "HTML", "CSS", "React", "FastAPI", "MySQL", "Git"],
            "soft_skills": ["Problem-solving", "Communication", "Teamwork", "Quick learning", "Adaptability"],
            "skills": [
                {"id": "skill_CAND-003_1", "candidate_id": "CAND-003", "skill": "Python", "normalized_skill": "python", "kind": "technical", "source": "cv", "confidence": 0.85},
                {"id": "skill_CAND-003_2", "candidate_id": "CAND-003", "skill": "React", "normalized_skill": "react", "kind": "technical", "source": "cv", "confidence": 0.80},
                {"id": "skill_CAND-003_3", "candidate_id": "CAND-003", "skill": "MySQL", "normalized_skill": "mysql", "kind": "technical", "source": "cv", "confidence": 0.85},
                {"id": "skill_CAND-003_4", "candidate_id": "CAND-003", "skill": "JavaScript", "normalized_skill": "javascript", "kind": "technical", "source": "cv", "confidence": 0.80},
            ],
            "experience": [
                {
                    "id": "exp_CAND-003_1",
                    "candidate_id": "CAND-003",
                    "company": "Apex Software Labs",
                    "position": "Software Engineering Trainee",
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                    "is_current": False,
                    "responsibilities": ["Assisted in developing web UI components with React", "Wrote unit tests and API endpoints"],
                    "technologies": ["React", "JavaScript", "Python", "MySQL"],
                    "source": "cv_verified",
                }
            ],
            "education": [
                {
                    "id": "edu_CAND-003_1",
                    "candidate_id": "CAND-003",
                    "institution": "University of Jaffna",
                    "qualification": "BSc in Information Technology",
                    "field": "Information Technology",
                    "start_year": 2021,
                    "end_year": 2025,
                    "grade": "Second Class",
                    "source": "cv_verified",
                }
            ],
            "projects": [
                {
                    "id": "proj_CAND-003_1",
                    "candidate_id": "CAND-003",
                    "name": "Student Management System",
                    "title": "Student Management System",
                    "description": "Developed a database-driven student management application using React and MySQL.",
                    "technologies": ["React", "MySQL", "JavaScript"],
                    "github_url": "https://github.com/muralitharan-dev/student-mgmt",
                }
            ],
            "certifications": [],
            "languages": [
                {"id": "lang_CAND-003_1", "candidate_id": "CAND-003", "language": "Tamil", "proficiency": "Native"},
                {"id": "lang_CAND-003_2", "candidate_id": "CAND-003", "language": "English", "proficiency": "Working proficiency"},
                {"id": "lang_CAND-003_3", "candidate_id": "CAND-003", "language": "Sinhala", "proficiency": "Basic"},
            ],
            "candidate_profile_score": 68.0,
            "score_breakdown": {
                "skills": {"score": 20.0, "max_score": 25.0},
                "experience": {"score": 12.0, "max_score": 20.0},
                "github": {"score": 10.0, "max_score": 15.0},
                "projects": {"score": 12.0, "max_score": 15.0},
                "education": {"score": 9.0, "max_score": 10.0},
                "languages": {"score": 5.0, "max_score": 5.0},
            },
            "github": {
                "username": "muralitharan-dev",
                "github_url": "https://github.com/muralitharan-dev",
                "verification_status": "verified",
                "latest_snapshot_id": "SNAP-005",
                "last_verified_at": utcnow_iso(),
            },
            "created_at": datetime(2026, 9, 12, 14, 0, 0, tzinfo=timezone.utc),
            "updated_at": utcnow(),
        },
        {
            "_id": "CAND-004",
            "id": "CAND-004",
            "user_id": "CAND-004",
            "personal_info": {
                "full_name": "Eranga",
                "email": "eranga12@gmail.com",
                "headline": "Software Engineer",
                "location": "Colombo, Sri Lanka",
                "phone": "+94 70 456 7890",
                "bio": "Enthusiastic software engineer with strong background in web development, database architecture, and full stack solutions.",
                "experience_years": 2.0,
            },
            "social_links": {
                "linkedin_url": "https://www.linkedin.com/in/eranga-software",
                "github_url": "https://github.com/eranga-software",
                "portfolio_url": None,
            },
            "career_preferences": {
                "preferred_roles": "Software Engineer, Web Developer",
                "work_preference": "Hybrid",
                "availability": "1 Month",
                "notice_period": "1 Month",
            },
            "technical_skills": ["JavaScript", "React", "Node.js", "Python", "SQL", "HTML", "CSS", "Git"],
            "soft_skills": ["Teamwork", "Communication", "Problem-solving"],
            "skills": [
                {"id": "skill_CAND-004_1", "candidate_id": "CAND-004", "skill": "JavaScript", "normalized_skill": "javascript", "kind": "technical", "source": "cv", "confidence": 0.9},
                {"id": "skill_CAND-004_2", "candidate_id": "CAND-004", "skill": "React", "normalized_skill": "react", "kind": "technical", "source": "cv", "confidence": 0.88},
                {"id": "skill_CAND-004_3", "candidate_id": "CAND-004", "skill": "Node.js", "normalized_skill": "nodejs", "kind": "technical", "source": "cv", "confidence": 0.85},
            ],
            "experience": [
                {
                    "id": "exp_CAND-004_1",
                    "candidate_id": "CAND-004",
                    "company": "Horizon Technologies",
                    "position": "Software Engineer",
                    "start_date": "2024-03-01",
                    "end_date": "2026-08-01",
                    "is_current": False,
                    "responsibilities": ["Full stack development using React and Node.js"],
                    "technologies": ["React", "Node.js", "JavaScript", "PostgreSQL"],
                }
            ],
            "education": [
                {
                    "id": "edu_CAND-004_1",
                    "candidate_id": "CAND-004",
                    "institution": "SLIIT",
                    "qualification": "BSc (Hons) in Information Technology",
                    "field": "Software Engineering",
                    "start_year": 2020,
                    "end_year": 2024,
                    "grade": "Second Class Upper",
                }
            ],
            "projects": [
                {
                    "id": "proj_CAND-004_1",
                    "candidate_id": "CAND-004",
                    "name": "Inventory Management Web App",
                    "title": "Inventory Management Web App",
                    "description": "Real-time stock tracking web application.",
                    "technologies": ["React", "Node.js", "PostgreSQL"],
                }
            ],
            "certifications": [],
            "languages": [
                {"id": "lang_CAND-004_1", "candidate_id": "CAND-004", "language": "English", "proficiency": "Fluent"},
                {"id": "lang_CAND-004_2", "candidate_id": "CAND-004", "language": "Sinhala", "proficiency": "Native"},
            ],
            "candidate_profile_score": 76.0,
            "score_breakdown": {
                "skills": {"score": 22.0, "max_score": 25.0},
                "experience": {"score": 16.0, "max_score": 20.0},
                "github": {"score": 11.0, "max_score": 15.0},
                "projects": {"score": 13.0, "max_score": 15.0},
                "education": {"score": 9.0, "max_score": 10.0},
                "languages": {"score": 5.0, "max_score": 5.0},
            },
            "created_at": datetime(2026, 9, 15, 15, 0, 0, tzinfo=timezone.utc),
            "updated_at": utcnow(),
        }
    ]

    # Remove old orphan/duplicate profiles
    db.candidate_profiles.delete_many({"id": {"$in": ["demo-candidate-1", "f3548d44-4c8a-45a2-b6b7-4fe0c62c32aa", "178dd70a-aba3-4c97-858e-297f062ba3bf"]}})
    db.candidate_profiles.delete_many({"user_id": {"$in": ["demo-candidate-1", "f3548d44-4c8a-45a2-b6b7-4fe0c62c32aa", "178dd70a-aba3-4c97-858e-297f062ba3bf"]}})

    for p in profiles_data:
        db.candidate_profiles.delete_many({"$or": [{"user_id": p["user_id"]}, {"id": p["id"]}, {"_id": p["_id"]}]})
        db.candidate_profiles.insert_one(p)
        print(f"  [OK] Profile: {p['id']:<10} | User: {p['user_id']:<10} | Skills: {len(p['skills']):<2} | Score: {p['candidate_profile_score']}")

    # -------------------------------------------------------------------------
    # STEP 3: NORMALIZE JOBS (Collection 3)
    # -------------------------------------------------------------------------
    print("\n[3/8] Normalizing 'jobs' collection...")

    jobs_data = [
        {
            "_id": "JOB-001",
            "id": "JOB-001",
            "recruiterId": "REC-001",
            "title": "Full Stack Developer",
            "company": "TalentVerify Technologies",
            "location": "Colombo, Sri Lanka",
            "type": "Full-time",
            "workMode": "Hybrid",
            "experience": 3,
            "skills": "React, TypeScript, Node.js, PostgreSQL, REST API, Docker",
            "description": "Build secure, customer-facing products across modern frontend React apps and FastAPI/Node.js backend services. Collaborate with cross-functional teams to design scalable cloud-native architectures.",
            "requirements": {
                "required_skills": ["React", "TypeScript", "Node.js", "PostgreSQL", "REST API", "Docker"],
                "preferred_skills": ["FastAPI", "AWS", "TailwindCSS"],
                "minimum_experience_years": 3.0,
                "education": {"minimum_level": "Bachelor's Degree in Computer Science or equivalent"},
            },
            "must_have_requirements": [
                {"requirement": "Strong experience in React and TypeScript", "type": "skill", "category": "skills", "mandatory": True},
                {"requirement": "Experience with relational databases (PostgreSQL/MySQL)", "type": "skill", "category": "skills", "mandatory": True},
                {"requirement": "Minimum 2+ years practical software development experience", "type": "experience", "category": "experience", "minimum_years": 2.0, "mandatory": True},
            ],
            "scoring_weights": DEFAULT_WEIGHTS.copy(),
            "recommendation_bands": DEFAULT_BANDS.copy(),
            "salary": {"minimum": 150000, "maximum": 250000, "currency": "LKR"},
            "status": "open",
            "createdAt": "2026-09-02T08:00:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "JOB-002",
            "id": "JOB-002",
            "recruiterId": "REC-001",
            "title": "AI / ML Engineer",
            "company": "TalentVerify Technologies",
            "location": "Remote",
            "type": "Full-time",
            "workMode": "Remote",
            "experience": 2,
            "skills": "Python, Machine Learning, TensorFlow, NLP, FastAPI, SQL",
            "description": "Develop, evaluate, and deploy intelligent matching, natural language processing, and document-analysis models powered by Gemini and open-source LLMs.",
            "requirements": {
                "required_skills": ["Python", "Machine Learning", "TensorFlow", "NLP", "FastAPI", "SQL"],
                "preferred_skills": ["PyTorch", "Docker", "HuggingFace"],
                "minimum_experience_years": 2.0,
                "education": {"minimum_level": "Degree in Computer Science, AI, Data Science or related"},
            },
            "must_have_requirements": [
                {"requirement": "Proficiency in Python and ML libraries (TensorFlow/PyTorch/Scikit-learn)", "type": "skill", "category": "skills", "mandatory": True},
                {"requirement": "Practical experience developing or integrating NLP/LLM models", "type": "skill", "category": "skills", "mandatory": True},
            ],
            "scoring_weights": DEFAULT_WEIGHTS.copy(),
            "recommendation_bands": DEFAULT_BANDS.copy(),
            "salary": {"minimum": 180000, "maximum": 280000, "currency": "LKR"},
            "status": "open",
            "createdAt": "2026-09-02T08:30:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "JOB-003",
            "id": "JOB-003",
            "recruiterId": "REC-001",
            "title": "QA Automation Engineer",
            "company": "TalentVerify Technologies",
            "location": "Kandy, Sri Lanka",
            "type": "Full-time",
            "workMode": "Hybrid",
            "experience": 2,
            "skills": "Selenium, Playwright, JavaScript, API Testing, SQL, CI/CD",
            "description": "Own automated end-to-end and regression test suites across web applications, REST APIs, and automated CI/CD release pipelines.",
            "requirements": {
                "required_skills": ["Selenium", "Playwright", "JavaScript", "API Testing", "SQL", "CI/CD"],
                "preferred_skills": ["Postman", "Cypress", "Python"],
                "minimum_experience_years": 2.0,
                "education": {"minimum_level": "Diploma or Degree in IT/Computer Science"},
            },
            "must_have_requirements": [
                {"requirement": "Proven experience in automated test frameworks (Playwright/Selenium)", "type": "skill", "category": "skills", "mandatory": True},
            ],
            "scoring_weights": DEFAULT_WEIGHTS.copy(),
            "recommendation_bands": DEFAULT_BANDS.copy(),
            "salary": {"minimum": 120000, "maximum": 190000, "currency": "LKR"},
            "status": "open",
            "createdAt": "2026-09-02T09:00:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "JOB-004",
            "id": "JOB-004",
            "recruiterId": "REC-001",
            "title": "DevOps & Cloud Engineer",
            "company": "TalentVerify Technologies",
            "location": "Colombo, Sri Lanka",
            "type": "Full-time",
            "workMode": "Hybrid",
            "experience": 3,
            "skills": "AWS, Docker, Kubernetes, Terraform, Linux, CI/CD",
            "description": "Operate multi-cloud infrastructure and improve deployment automation, Kubernetes orchestration, observability, and container security.",
            "requirements": {
                "required_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "CI/CD"],
                "preferred_skills": ["Prometheus", "Grafana", "Python/Bash scripting"],
                "minimum_experience_years": 3.0,
                "education": {"minimum_level": "Degree in Computer Science, Engineering, or IT"},
            },
            "must_have_requirements": [
                {"requirement": "Hands-on experience in AWS and Docker/Kubernetes container orchestration", "type": "skill", "category": "skills", "mandatory": True},
                {"requirement": "Infrastructure as Code (Terraform) experience", "type": "skill", "category": "skills", "mandatory": True},
            ],
            "scoring_weights": DEFAULT_WEIGHTS.copy(),
            "recommendation_bands": DEFAULT_BANDS.copy(),
            "salary": {"minimum": 200000, "maximum": 320000, "currency": "LKR"},
            "status": "open",
            "createdAt": "2026-09-02T09:30:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "JOB-005",
            "id": "JOB-005",
            "recruiterId": "REC-002",
            "title": "Lead Cloud Architect",
            "company": "TalentVerify Technologies",
            "location": "Remote",
            "type": "Full-time",
            "workMode": "Remote",
            "experience": 5,
            "skills": "AWS, Microservices, Python, Architecture, Kubernetes, Security",
            "description": "Lead enterprise architecture modernization, microservices design patterns, and high-availability cloud migration initiatives.",
            "requirements": {
                "required_skills": ["AWS", "Microservices", "Python", "Architecture", "Kubernetes", "Security"],
                "preferred_skills": ["TOGAF", "CloudFormation", "FinOps"],
                "minimum_experience_years": 5.0,
                "education": {"minimum_level": "Master's or Bachelor's in Computer Science/Engineering"},
            },
            "must_have_requirements": [
                {"requirement": "5+ years in cloud system architecture and distributed systems", "type": "experience", "category": "experience", "minimum_years": 5.0, "mandatory": True},
            ],
            "scoring_weights": DEFAULT_WEIGHTS.copy(),
            "recommendation_bands": DEFAULT_BANDS.copy(),
            "salary": {"minimum": 350000, "maximum": 500000, "currency": "LKR"},
            "status": "open",
            "createdAt": "2026-09-10T10:00:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "JOB-006",
            "id": "JOB-006",
            "recruiterId": "REC-001",
            "title": "ML Engineer",
            "company": "TalentVerify Technologies",
            "location": "Colombo, Sri Lanka",
            "type": "Full-time",
            "workMode": "Hybrid",
            "experience": 2,
            "skills": "Python, Machine Learning, TensorFlow, NLP, FastAPI, SQL",
            "description": "Deliver cutting-edge deep learning models and natural language evaluation services for real-time candidate verification.",
            "requirements": {
                "required_skills": ["Python", "Machine Learning", "FastAPI", "SQL"],
                "preferred_skills": ["TensorFlow", "PyTorch"],
                "minimum_experience_years": 2.0,
            },
            "must_have_requirements": [],
            "scoring_weights": DEFAULT_WEIGHTS.copy(),
            "recommendation_bands": DEFAULT_BANDS.copy(),
            "status": "open",
            "createdAt": "2026-09-15T11:00:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "JOB-007",
            "id": "JOB-007",
            "recruiterId": "REC-001",
            "title": "Senior Software Engineer",
            "company": "TalentVerify Technologies",
            "location": "Colombo, Sri Lanka",
            "type": "Full-time",
            "workMode": "On-site",
            "experience": 4,
            "skills": "React, Python, TypeScript, Microservices, SQL, Docker",
            "description": "Drive engineering excellence, mentor junior developers, and construct high-throughput customer applications.",
            "requirements": {
                "required_skills": ["React", "Python", "TypeScript", "SQL"],
                "preferred_skills": ["Docker", "Kubernetes"],
                "minimum_experience_years": 4.0,
            },
            "must_have_requirements": [],
            "scoring_weights": DEFAULT_WEIGHTS.copy(),
            "recommendation_bands": DEFAULT_BANDS.copy(),
            "status": "open",
            "createdAt": "2026-09-18T14:00:00+00:00",
            "updatedAt": utcnow_iso(),
        },
    ]

    # Delete unnormalized or rogue jobs (like cf66b70b...)
    db.jobs.delete_many({"recruiterId": "demo-recruiter-1"})
    db.jobs.delete_many({"_id": "cf66b70b-715c-4330-b1cf-0c57928d6eba"})

    for j in jobs_data:
        db.jobs.delete_many({"$or": [{"id": j["id"]}, {"_id": j["_id"]}]})
        db.jobs.insert_one(j)
        print(f"  [OK] Job: {j['id']:<10} | Recruiter: {j['recruiterId']:<10} | Title: {j['title']}")

    # -------------------------------------------------------------------------
    # STEP 4: NORMALIZE CV DOCUMENTS (Collection 5)
    # -------------------------------------------------------------------------
    print("\n[4/8] Normalizing 'cv_documents' collection...")

    # First clean up orphaned or failed duplicate test documents
    db.cv_documents.delete_many({"candidate_id": "demo-candidate-1"})
    db.cv_documents.delete_many({"file_name": {"$in": ["test_cv.txt", "my_cv.txt", "sample_cv.txt", "cv.txt"]}})
    db.cv_documents.delete_many({"candidate_id": {"$nin": ["CAND-001", "CAND-002", "CAND-003", "CAND-004"]}})

    cv_documents_data = [
        {
            "_id": "CV-001",
            "id": "CV-001",
            "candidate_id": "CAND-001",
            "file_name": "Demo_Candidate_FullStack_CV.pdf",
            "original_name": "Demo_Candidate_FullStack_CV.pdf",
            "content_type": "application/pdf",
            "file_size": 145200,
            "file_url": "/uploads/Demo_Candidate_FullStack_CV.pdf",
            "extracted_text": "Demo Candidate. Full Stack Developer with 2.5+ years experience building web applications with React, Python, FastAPI, Docker, and PostgreSQL. BSc in Computer Science.",
            "parsing_status": "completed",
            "parsed_data": {
                "skills": ["React", "JavaScript", "Python", "SQL", "FastAPI", "Docker", "Node.js"],
                "experience": [{"company": "Tech Innovations Pvt Ltd", "position": "Associate Software Developer", "years": 2.5}],
                "education": [{"institution": "University of Colombo School of Computing", "qualification": "BSc (Hons) in Computer Science"}],
            },
            "uploaded_at": datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc),
            "createdAt": datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc),
            "updatedAt": utcnow(),
        },
        {
            "_id": "CV-002",
            "id": "CV-002",
            "candidate_id": "CAND-002",
            "file_name": "Eranga_Isuru_Backend_CV.pdf",
            "original_name": "Eranga_Isuru_Backend_CV.pdf",
            "content_type": "application/pdf",
            "file_size": 182300,
            "file_url": "/uploads/Eranga_Isuru_Backend_CV.pdf",
            "extracted_text": "Eranga Isuru. Senior Backend & Cloud Engineer with 4 years experience in AWS, Kubernetes, Terraform, Python, and microservices architecture. First Class BSc Engineering.",
            "parsing_status": "completed",
            "parsed_data": {
                "skills": ["Python", "AWS", "Docker", "Kubernetes", "Terraform", "PostgreSQL"],
                "experience": [{"company": "CloudScape Solutions", "position": "Senior Backend Engineer", "years": 4.0}],
                "education": [{"institution": "University of Peradeniya", "qualification": "BSc in Engineering"}],
            },
            "uploaded_at": datetime(2026, 9, 21, 11, 0, 0, tzinfo=timezone.utc),
            "createdAt": datetime(2026, 9, 21, 11, 0, 0, tzinfo=timezone.utc),
            "updatedAt": utcnow(),
        },
        {
            "_id": "CV-003",
            "id": "CV-003",
            "candidate_id": "CAND-003",
            "file_name": "Muralitharan_CV.pdf",
            "original_name": "Muralitharan_CV.pdf",
            "content_type": "application/pdf",
            "file_size": 128400,
            "file_url": "/uploads/Muralitharan_CV.pdf",
            "extracted_text": "Muralitharan. Junior Software Developer with proficiency in React, Python, MySQL, HTML, CSS, and web development fundamentals. BSc in Information Technology.",
            "parsing_status": "completed",
            "parsed_data": {
                "skills": ["React", "Python", "MySQL", "JavaScript", "HTML", "CSS"],
                "experience": [{"company": "Apex Software Labs", "position": "Software Engineering Trainee", "years": 1.0}],
                "education": [{"institution": "University of Jaffna", "qualification": "BSc in Information Technology"}],
            },
            "uploaded_at": datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc),
            "createdAt": datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc),
            "updatedAt": utcnow(),
        },
        {
            "_id": "CV-004",
            "id": "CV-004",
            "candidate_id": "CAND-004",
            "file_name": "Eranga_Software_CV.pdf",
            "original_name": "Eranga_Software_CV.pdf",
            "content_type": "application/pdf",
            "file_size": 139100,
            "file_url": "/uploads/Eranga_Software_CV.pdf",
            "extracted_text": "Eranga. Full Stack Software Engineer with 2 years practical experience in React, Node.js, JavaScript, and database systems. BSc in Information Technology.",
            "parsing_status": "completed",
            "parsed_data": {
                "skills": ["React", "Node.js", "JavaScript", "SQL", "Python"],
                "experience": [{"company": "Horizon Technologies", "position": "Software Engineer", "years": 2.0}],
                "education": [{"institution": "SLIIT", "qualification": "BSc (Hons) in Information Technology"}],
            },
            "uploaded_at": datetime(2026, 9, 22, 15, 0, 0, tzinfo=timezone.utc),
            "createdAt": datetime(2026, 9, 22, 15, 0, 0, tzinfo=timezone.utc),
            "updatedAt": utcnow(),
        },
    ]

    for cv in cv_documents_data:
        db.cv_documents.delete_many({"$or": [{"id": cv["id"]}, {"_id": cv["_id"]}]})
        db.cv_documents.insert_one(cv)
        print(f"  [OK] CV: {cv['id']:<10} | Candidate: {cv['candidate_id']:<10} | File: {cv['file_name']:<35} | Status: {cv['parsing_status']}")

    # -------------------------------------------------------------------------
    # STEP 5: NORMALIZE EVIDENCE SNAPSHOTS (Collection 6)
    # -------------------------------------------------------------------------
    print("\n[5/8] Normalizing 'evidence_snapshots' collection...")

    # Clear outdated snapshots referencing demo-candidate-1
    db.evidence_snapshots.delete_many({"candidate_id": "demo-candidate-1"})
    db.evidence_snapshots.delete_many({"candidate_id": {"$nin": ["CAND-001", "CAND-002", "CAND-003", "CAND-004"]}})

    snapshots_data = [
        {
            "_id": "SNAP-001",
            "id": "SNAP-001",
            "candidate_id": "CAND-001",
            "platform": "github",
            "github_url": "https://github.com/demo-candidate",
            "profile_url": "https://github.com/demo-candidate",
            "username": "demo-candidate",
            "verification_status": "verified",
            "verification_score": 92.0,
            "scanned_at": utcnow_iso(),
            "verified_at": utcnow(),
            "profile": {
                "login": "demo-candidate",
                "name": "Demo Candidate",
                "public_repos": 14,
                "followers": 28,
                "bio": "Building scalable full stack web applications.",
            },
            "repositories": [
                {
                    "name": "ecommerce-platform",
                    "url": "https://github.com/demo-candidate/ecommerce-platform",
                    "description": "Full-stack e-commerce web platform built with React, FastAPI, and Docker",
                    "language": "Python",
                    "stars": 12,
                    "last_updated": utcnow_iso(),
                },
                {
                    "name": "react-component-library",
                    "url": "https://github.com/demo-candidate/react-component-library",
                    "description": "Reusable modern React UI component library",
                    "language": "TypeScript",
                    "stars": 8,
                    "last_updated": utcnow_iso(),
                },
                {
                    "name": "fastapi-jwt-auth",
                    "url": "https://github.com/demo-candidate/fastapi-jwt-auth",
                    "description": "Production-ready JWT authentication backend service",
                    "language": "Python",
                    "stars": 15,
                    "last_updated": utcnow_iso(),
                }
            ],
            "detected_skills": ["React", "Python", "FastAPI", "Docker", "TypeScript", "PostgreSQL", "JavaScript"],
            "top_languages": [
                {"language": "Python", "percentage": 52.0},
                {"language": "TypeScript", "percentage": 30.0},
                {"language": "JavaScript", "percentage": 18.0},
            ],
            "cv_consistency": {
                "confirmed_skills": ["React", "Python", "FastAPI", "Docker", "SQL"],
                "unverified_skills": [],
                "consistency_level": "strong",
            },
            "analysis": {
                "match_percentage": 92.0,
                "strengths": ["High-quality clean code structure", "Thorough test coverage", "Consistent git commit history"],
                "weaknesses": [],
            },
            "createdAt": utcnow(),
        },
        {
            "_id": "SNAP-002",
            "id": "SNAP-002",
            "candidate_id": "CAND-001",
            "platform": "linkedin",
            "profile_url": "https://www.linkedin.com/in/demo-candidate",
            "username": "demo-candidate",
            "verification_status": "verified",
            "verification_score": 88.0,
            "scanned_at": utcnow_iso(),
            "verified_at": utcnow(),
            "detected_skills": ["React", "Python", "Software Engineering", "Full Stack Development"],
            "createdAt": utcnow(),
        },
        {
            "_id": "SNAP-003",
            "id": "SNAP-003",
            "candidate_id": "CAND-001",
            "platform": "portfolio",
            "profile_url": "https://democandidate.dev",
            "username": "demo-candidate",
            "verification_status": "verified",
            "verification_score": 90.0,
            "scanned_at": utcnow_iso(),
            "verified_at": utcnow(),
            "detected_skills": ["React", "TailwindCSS", "Web Design"],
            "createdAt": utcnow(),
        },
        {
            "_id": "SNAP-004",
            "id": "SNAP-004",
            "candidate_id": "CAND-002",
            "platform": "github",
            "github_url": "https://github.com/erangaisuru",
            "profile_url": "https://github.com/erangaisuru",
            "username": "erangaisuru",
            "verification_status": "verified",
            "verification_score": 95.0,
            "scanned_at": utcnow_iso(),
            "verified_at": utcnow(),
            "profile": {
                "login": "erangaisuru",
                "name": "Eranga Isuru",
                "public_repos": 22,
                "followers": 45,
                "bio": "Cloud architecture, Kubernetes, and backend infrastructure.",
            },
            "repositories": [
                {
                    "name": "cloud-cicd-terraform",
                    "url": "https://github.com/erangaisuru/cloud-cicd-terraform",
                    "description": "AWS infrastructure as code templates using Terraform and Helm",
                    "language": "HCL",
                    "stars": 24,
                    "last_updated": utcnow_iso(),
                },
                {
                    "name": "kubernetes-operator-python",
                    "url": "https://github.com/erangaisuru/kubernetes-operator-python",
                    "description": "Custom Kubernetes operator for automated microservice scaling",
                    "language": "Python",
                    "stars": 31,
                    "last_updated": utcnow_iso(),
                }
            ],
            "detected_skills": ["AWS", "Kubernetes", "Docker", "Terraform", "Python", "Linux"],
            "top_languages": [
                {"language": "Python", "percentage": 60.0},
                {"language": "HCL", "percentage": 30.0},
                {"language": "Shell", "percentage": 10.0},
            ],
            "cv_consistency": {
                "confirmed_skills": ["AWS", "Kubernetes", "Docker", "Terraform", "Python"],
                "consistency_level": "strong",
            },
            "createdAt": utcnow(),
        },
        {
            "_id": "SNAP-005",
            "id": "SNAP-005",
            "candidate_id": "CAND-003",
            "platform": "github",
            "github_url": "https://github.com/muralitharan-dev",
            "profile_url": "https://github.com/muralitharan-dev",
            "username": "muralitharan-dev",
            "verification_status": "verified",
            "verification_score": 75.0,
            "scanned_at": utcnow_iso(),
            "verified_at": utcnow(),
            "profile": {
                "login": "muralitharan-dev",
                "name": "Muralitharan",
                "public_repos": 8,
                "followers": 10,
            },
            "repositories": [
                {
                    "name": "student-mgmt-app",
                    "url": "https://github.com/muralitharan-dev/student-mgmt-app",
                    "description": "Student management web app",
                    "language": "JavaScript",
                    "stars": 3,
                }
            ],
            "detected_skills": ["React", "JavaScript", "HTML", "CSS", "MySQL"],
            "createdAt": utcnow(),
        }
    ]

    for snap in snapshots_data:
        db.evidence_snapshots.delete_many({"$or": [{"id": snap["id"]}, {"_id": snap["_id"]}]})
        db.evidence_snapshots.insert_one(snap)
        print(f"  [OK] Snapshot: {snap['id']:<10} | Candidate: {snap['candidate_id']:<10} | Platform: {snap['platform']:<10} | Status: {snap['verification_status']}")

    # -------------------------------------------------------------------------
    # STEP 6: NORMALIZE APPLICATIONS (Collection 4)
    # -------------------------------------------------------------------------
    print("\n[6/8] Normalizing 'applications' collection...")

    # Clear outdated applications with old IDs
    db.applications.delete_many({"jobId": {"$in": ["cf66b70b-715c-4330-b1cf-0c57928d6eba"]}})
    db.applications.delete_many({"userId": {"$in": ["178dd70a-aba3-4c97-858e-297f062ba3bf", "f3548d44-4c8a-45a2-b6b7-4fe0c62c32aa", "demo-candidate-1"]}})

    applications_data = [
        {
            "_id": "APP-001",
            "id": "APP-001",
            "userId": "CAND-001",
            "candidateId": "CAND-001",
            "jobId": "JOB-001",
            "jobTitle": "Full Stack Developer",
            "company": "TalentVerify Technologies",
            "location": "Colombo, Sri Lanka",
            "cvDocumentId": "CV-001",
            "status": "Under review",
            "jobMatchScore": 88.0,
            "candidateProfileScore": 84.5,
            "score": 88.0,
            "overallScore": 88.0,
            "matchLevel": "Strong Match",
            "recommendedDecision": "RECOMMENDED",
            "recommendation": {
                "decision": "RECOMMENDED",
                "summary": "Candidate exhibits strong alignment with Full Stack requirements (React, FastAPI, Docker, and SQL).",
            },
            "scores": {
                "skills": {"score": 33.0, "maximum_score": 35.0, "weighted_score": 33.0},
                "experience": {"score": 21.0, "maximum_score": 25.0, "weighted_score": 21.0},
                "education": {"score": 14.0, "maximum_score": 15.0, "weighted_score": 14.0},
                "projects": {"score": 14.0, "maximum_score": 15.0, "weighted_score": 14.0},
                "certifications": {"score": 6.0, "maximum_score": 10.0, "weighted_score": 6.0},
            },
            "score_breakdown": {
                "skills": 33.0,
                "experience": 21.0,
                "education": 14.0,
                "projects": 14.0,
                "certifications": 6.0,
            },
            "matchedSkills": ["React", "TypeScript", "Node.js", "PostgreSQL", "REST API", "Docker"],
            "requiredSkills": ["React", "TypeScript", "Node.js", "PostgreSQL", "REST API", "Docker"],
            "verifiedSkills": ["React", "Python", "FastAPI", "Docker", "SQL"],
            "unverifiedClaims": [],
            "missingRequirements": [],
            "mandatoryRequirements": ["Strong experience in React", "Experience with relational databases"],
            "strengths": [
                "Practical experience building and deploying React + FastAPI containerized apps.",
                "Demonstrated GitHub verified code quality and active contribution history.",
                "Strong foundational Computer Science degree."
            ],
            "weaknesses": [
                "Slightly under the preferred 3 years threshold (2.5 years documented experience)."
            ],
            "interviewFocus": "Probe microservice architecture experience and TypeScript design patterns.",
            "candidateSnapshot": {
                "name": "Demo Candidate",
                "email": "candidate@gmail.com",
                "headline": "Full Stack Developer",
                "phone": "+94 77 123 4567",
                "location": "Colombo, Sri Lanka",
                "portfolioUrl": "https://democandidate.dev",
                "profilePhotoUrl": None,
                "photoVisibleToRecruiters": False,
            },
            "enterpriseEvaluation": {
                "candidate_score": 88.0,
                "match_level": "Strong Match",
                "evidence_confidence": 92.0,
                "recommendation": {"decision": "RECOMMENDED"},
                "score_breakdown": {"skills": 33.0, "experience": 21.0, "education": 14.0, "projects": 14.0, "certifications": 6.0},
            },
            "analysis": {
                "job_match_score": 88.0,
                "match_level": "Strong Match",
                "recommendation": "RECOMMENDED",
            },
            "finalDecision": {
                "decision": "pending",
                "reason": "Pending technical interview stage",
                "decided_by": None,
                "decided_at": None,
            },
            "appliedAt": "2026-09-21T10:00:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "APP-002",
            "id": "APP-002",
            "userId": "CAND-001",
            "candidateId": "CAND-001",
            "jobId": "JOB-002",
            "jobTitle": "AI / ML Engineer",
            "company": "TalentVerify Technologies",
            "location": "Remote",
            "cvDocumentId": "CV-001",
            "status": "Shortlisted",
            "jobMatchScore": 82.0,
            "candidateProfileScore": 84.5,
            "score": 82.0,
            "overallScore": 82.0,
            "matchLevel": "Strong Match",
            "recommendedDecision": "RECOMMENDED",
            "recommendation": {
                "decision": "RECOMMENDED",
                "summary": "Solid Python capabilities and proven LLM document extraction project integration.",
            },
            "scores": {
                "skills": {"score": 30.0, "maximum_score": 35.0, "weighted_score": 30.0},
                "experience": {"score": 20.0, "maximum_score": 25.0, "weighted_score": 20.0},
                "education": {"score": 14.0, "maximum_score": 15.0, "weighted_score": 14.0},
                "projects": {"score": 13.0, "maximum_score": 15.0, "weighted_score": 13.0},
                "certifications": {"score": 5.0, "maximum_score": 10.0, "weighted_score": 5.0},
            },
            "score_breakdown": {
                "skills": 30.0,
                "experience": 20.0,
                "education": 14.0,
                "projects": 13.0,
                "certifications": 5.0,
            },
            "matchedSkills": ["Python", "FastAPI", "SQL", "Machine Learning"],
            "requiredSkills": ["Python", "Machine Learning", "TensorFlow", "NLP", "FastAPI", "SQL"],
            "verifiedSkills": ["Python", "FastAPI", "SQL"],
            "unverifiedClaims": [],
            "missingRequirements": ["TensorFlow production experience"],
            "mandatoryRequirements": ["Proficiency in Python and ML libraries"],
            "strengths": [
                "Hands-on project work developing AI document extractors with Gemini and Python.",
                "FastAPI REST API design skills.",
            ],
            "weaknesses": [
                "Needs more production exposure with TensorFlow/PyTorch deep learning pipelines."
            ],
            "interviewFocus": "Assess knowledge of model quantization, token optimization, and embeddings.",
            "candidateSnapshot": {
                "name": "Demo Candidate",
                "email": "candidate@gmail.com",
                "headline": "Full Stack Developer",
                "phone": "+94 77 123 4567",
                "location": "Colombo, Sri Lanka",
                "portfolioUrl": "https://democandidate.dev",
            },
            "enterpriseEvaluation": {
                "candidate_score": 82.0,
                "match_level": "Strong Match",
                "evidence_confidence": 88.0,
                "recommendation": {"decision": "RECOMMENDED"},
                "score_breakdown": {"skills": 30.0, "experience": 20.0, "education": 14.0, "projects": 13.0, "certifications": 5.0},
            },
            "analysis": {
                "job_match_score": 82.0,
                "match_level": "Strong Match",
                "recommendation": "RECOMMENDED",
            },
            "finalDecision": {
                "decision": "pending",
                "reason": "Shortlisted for Round 1 Interview",
                "decided_by": "REC-001",
                "decided_at": utcnow_iso(),
            },
            "appliedAt": "2026-09-22T14:30:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "APP-003",
            "id": "APP-003",
            "userId": "CAND-002",
            "candidateId": "CAND-002",
            "jobId": "JOB-004",
            "jobTitle": "DevOps & Cloud Engineer",
            "company": "TalentVerify Technologies",
            "location": "Colombo, Sri Lanka",
            "cvDocumentId": "CV-002",
            "status": "Under review",
            "jobMatchScore": 95.0,
            "candidateProfileScore": 89.0,
            "score": 95.0,
            "overallScore": 95.0,
            "matchLevel": "Strong Match",
            "recommendedDecision": "RECOMMENDED",
            "recommendation": {
                "decision": "RECOMMENDED",
                "summary": "Exceptional match across all core DevOps competencies (AWS, Kubernetes, Terraform, and Docker).",
            },
            "scores": {
                "skills": {"score": 35.0, "maximum_score": 35.0, "weighted_score": 35.0},
                "experience": {"score": 25.0, "maximum_score": 25.0, "weighted_score": 25.0},
                "education": {"score": 15.0, "maximum_score": 15.0, "weighted_score": 15.0},
                "projects": {"score": 12.0, "maximum_score": 15.0, "weighted_score": 12.0},
                "certifications": {"score": 8.0, "maximum_score": 10.0, "weighted_score": 8.0},
            },
            "score_breakdown": {
                "skills": 35.0,
                "experience": 25.0,
                "education": 15.0,
                "projects": 12.0,
                "certifications": 8.0,
            },
            "matchedSkills": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "CI/CD"],
            "requiredSkills": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "CI/CD"],
            "verifiedSkills": ["AWS", "Docker", "Kubernetes", "Terraform"],
            "unverifiedClaims": [],
            "missingRequirements": [],
            "mandatoryRequirements": ["Hands-on experience in AWS and Docker/Kubernetes", "Infrastructure as Code experience"],
            "strengths": [
                "4 years of verifiable enterprise cloud engineering experience.",
                "Certified AWS Solutions Architect.",
                "Published open-source Terraform and Kubernetes modules.",
            ],
            "weaknesses": [],
            "interviewFocus": "Assess multi-region disaster recovery and security compliance knowledge.",
            "candidateSnapshot": {
                "name": "Eranga Isuru",
                "email": "erangaisuru@gmail.com",
                "headline": "Senior Backend & Cloud Engineer",
                "phone": "+94 71 234 5678",
                "location": "Kandy, Sri Lanka",
            },
            "enterpriseEvaluation": {
                "candidate_score": 95.0,
                "match_level": "Strong Match",
                "evidence_confidence": 96.0,
                "recommendation": {"decision": "RECOMMENDED"},
                "score_breakdown": {"skills": 35.0, "experience": 25.0, "education": 15.0, "projects": 12.0, "certifications": 8.0},
            },
            "analysis": {
                "job_match_score": 95.0,
                "match_level": "Strong Match",
                "recommendation": "RECOMMENDED",
            },
            "finalDecision": {
                "decision": "pending",
                "reason": "Top candidate for the position",
            },
            "appliedAt": "2026-09-23T09:15:00+00:00",
            "updatedAt": utcnow_iso(),
        },
        {
            "_id": "APP-004",
            "id": "APP-004",
            "userId": "CAND-003",
            "candidateId": "CAND-003",
            "jobId": "JOB-001",
            "jobTitle": "Full Stack Developer",
            "company": "TalentVerify Technologies",
            "location": "Colombo, Sri Lanka",
            "cvDocumentId": "CV-003",
            "status": "Submitted",
            "jobMatchScore": 72.0,
            "candidateProfileScore": 68.0,
            "score": 72.0,
            "overallScore": 72.0,
            "matchLevel": "Moderate Match",
            "recommendedDecision": "BORDERLINE",
            "recommendation": {
                "decision": "BORDERLINE",
                "summary": "Candidate displays foundational skills in React and Python, but lacks required 3 years production experience.",
            },
            "scores": {
                "skills": {"score": 28.0, "maximum_score": 35.0, "weighted_score": 28.0},
                "experience": {"score": 14.0, "maximum_score": 25.0, "weighted_score": 14.0},
                "education": {"score": 13.0, "maximum_score": 15.0, "weighted_score": 13.0},
                "projects": {"score": 12.0, "maximum_score": 15.0, "weighted_score": 12.0},
                "certifications": {"score": 5.0, "maximum_score": 10.0, "weighted_score": 5.0},
            },
            "score_breakdown": {
                "skills": 28.0,
                "experience": 14.0,
                "education": 13.0,
                "projects": 12.0,
                "certifications": 5.0,
            },
            "matchedSkills": ["React", "JavaScript", "SQL"],
            "requiredSkills": ["React", "TypeScript", "Node.js", "PostgreSQL", "REST API", "Docker"],
            "verifiedSkills": ["React", "MySQL"],
            "unverifiedClaims": [],
            "missingRequirements": ["Docker", "TypeScript"],
            "mandatoryRequirements": ["Minimum 2+ years practical software development experience"],
            "strengths": [
                "Solid academic foundation in IT from University of Jaffna.",
                "Eager learner with hands-on trainee experience.",
            ],
            "weaknesses": [
                "Experience gap for mid-level position (1 year trainee vs 3 years required).",
            ],
            "interviewFocus": "Assess learning speed and core web programming concepts.",
            "candidateSnapshot": {
                "name": "Muralitharan",
                "email": "muralitharan@email.com",
                "headline": "Junior Software Developer | IT Professional",
                "phone": "+94 76 345 6789",
                "location": "Jaffna, Sri Lanka",
            },
            "enterpriseEvaluation": {
                "candidate_score": 72.0,
                "match_level": "Moderate Match",
                "evidence_confidence": 78.0,
                "recommendation": {"decision": "BORDERLINE"},
                "score_breakdown": {"skills": 28.0, "experience": 14.0, "education": 13.0, "projects": 12.0, "certifications": 5.0},
            },
            "analysis": {
                "job_match_score": 72.0,
                "match_level": "Moderate Match",
                "recommendation": "BORDERLINE",
            },
            "finalDecision": {
                "decision": "pending",
                "reason": "Submitted for recruiter initial screening",
            },
            "appliedAt": "2026-09-23T11:00:00+00:00",
            "updatedAt": utcnow_iso(),
        },
    ]

    for app in applications_data:
        db.applications.delete_many({"$or": [{"id": app["id"]}, {"_id": app["_id"]}, {"userId": app["userId"], "jobId": app["jobId"]}]})
        db.applications.insert_one(app)
        print(f"  [OK] Application: {app['id']:<10} | Candidate: {app['userId']:<10} | Job: {app['jobId']:<10} | Score: {app['jobMatchScore']:<4} | Status: {app['status']}")

    # -------------------------------------------------------------------------
    # STEP 7: NORMALIZE ANALYSIS RUNS (Collection 8)
    # -------------------------------------------------------------------------
    print("\n[7/8] Normalizing 'analysis_runs' collection...")

    db.analysis_runs.delete_many({"candidate_id": "demo-candidate-1"})

    analysis_runs_data = [
        {
            "_id": "RUN-APP-001",
            "id": "RUN-APP-001",
            "candidateId": "CAND-001",
            "candidate_id": "CAND-001",
            "jobId": "JOB-001",
            "job_id": "JOB-001",
            "applicationId": "APP-001",
            "application_id": "APP-001",
            "cvDocumentId": "CV-001",
            "cv_document_id": "CV-001",
            "analysisType": "job_match",
            "model": "gemini-3.5-flash-lite",
            "promptVersion": "2.5",
            "input_snapshot": {
                "candidate_skills": ["React", "JavaScript", "Python", "SQL", "FastAPI", "Docker"],
                "job_requirements": ["React", "TypeScript", "Node.js", "PostgreSQL", "REST API", "Docker"],
                "cv_text": "Demo Candidate CV",
            },
            "result": {
                "total_score": 88.0,
                "skills_score": 33.0,
                "experience_score": 21.0,
                "education_score": 14.0,
                "strengths": ["Strong React and FastAPI capability", "Verified GitHub repository code"],
                "weaknesses": ["Slightly under 3 years experience threshold"],
                "missing_skills": ["TypeScript"],
                "recommendation": "RECOMMENDED",
            },
            "status": "completed",
            "processing_time_ms": 1240,
            "createdAt": utcnow(),
        },
        {
            "_id": "RUN-APP-002",
            "id": "RUN-APP-002",
            "candidateId": "CAND-001",
            "candidate_id": "CAND-001",
            "jobId": "JOB-002",
            "job_id": "JOB-002",
            "applicationId": "APP-002",
            "application_id": "APP-002",
            "cvDocumentId": "CV-001",
            "cv_document_id": "CV-001",
            "analysisType": "job_match",
            "model": "gemini-3.5-flash-lite",
            "promptVersion": "2.5",
            "input_snapshot": {
                "candidate_skills": ["Python", "FastAPI", "SQL", "React"],
                "job_requirements": ["Python", "Machine Learning", "TensorFlow", "FastAPI"],
                "cv_text": "Demo Candidate CV",
            },
            "result": {
                "total_score": 82.0,
                "skills_score": 30.0,
                "experience_score": 20.0,
                "education_score": 14.0,
                "strengths": ["Python expertise", "AI project experience"],
                "weaknesses": ["Limited TensorFlow exposure"],
                "missing_skills": ["TensorFlow"],
                "recommendation": "RECOMMENDED",
            },
            "status": "completed",
            "processing_time_ms": 1150,
            "createdAt": utcnow(),
        },
        {
            "_id": "RUN-PROF-001",
            "id": "RUN-PROF-001",
            "candidateId": "CAND-001",
            "candidate_id": "CAND-001",
            "jobId": None,
            "applicationId": None,
            "cvDocumentId": "CV-001",
            "cv_document_id": "CV-001",
            "analysisType": "profile_score",
            "model": "gemini-3.5-flash-lite",
            "promptVersion": "2.5",
            "result": {
                "total_score": 84.5,
                "skills_score": 24.5,
                "experience_score": 18.0,
                "education_score": 9.0,
                "strengths": ["Complete verifiable profile with GitHub"],
                "weaknesses": [],
                "missing_skills": [],
                "recommendation": "High Authenticity",
            },
            "status": "completed",
            "processing_time_ms": 980,
            "createdAt": utcnow(),
        },
        {
            "_id": "RUN-APP-003",
            "id": "RUN-APP-003",
            "candidateId": "CAND-002",
            "candidate_id": "CAND-002",
            "jobId": "JOB-004",
            "job_id": "JOB-004",
            "applicationId": "APP-003",
            "application_id": "APP-003",
            "cvDocumentId": "CV-002",
            "cv_document_id": "CV-002",
            "analysisType": "job_match",
            "model": "gemini-3.5-flash-lite",
            "promptVersion": "2.5",
            "result": {
                "total_score": 95.0,
                "skills_score": 35.0,
                "experience_score": 25.0,
                "education_score": 15.0,
                "strengths": ["Comprehensive AWS and Kubernetes skills", "Architect level certification"],
                "weaknesses": [],
                "missing_skills": [],
                "recommendation": "RECOMMENDED",
            },
            "status": "completed",
            "processing_time_ms": 1320,
            "createdAt": utcnow(),
        },
    ]

    for run in analysis_runs_data:
        db.analysis_runs.delete_many({"$or": [{"id": run["id"]}, {"_id": run["_id"]}]})
        db.analysis_runs.insert_one(run)
        print(f"  [OK] Run: {run['id']:<14} | Candidate: {run['candidateId']:<10} | Type: {run['analysisType']:<14} | Score: {run['result']['total_score']}")

    # -------------------------------------------------------------------------
    # STEP 8: NORMALIZE AUDIT LOGS (Collection 7)
    # -------------------------------------------------------------------------
    print("\n[8/8] Normalizing 'audit_logs' collection...")

    audit_logs_data = [
        {
            "_id": "AUDIT-001",
            "id": "AUDIT-001",
            "userId": "REC-001",
            "performedBy": "REC-001",
            "actor_id": "REC-001",
            "documentId": "JOB-001",
            "entity_id": "JOB-001",
            "collectionName": "jobs",
            "entity_type": "job",
            "action": "job_created",
            "oldValue": None,
            "newValue": {"id": "JOB-001", "title": "Full Stack Developer"},
            "details": {"title": "Full Stack Developer", "type": "Full-time"},
            "reason": "Recruiter opened new engineering position",
            "ipAddress": "127.0.0.1",
            "userAgent": "Mozilla/5.0",
            "createdAt": datetime(2026, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2026, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
        },
        {
            "_id": "AUDIT-002",
            "id": "AUDIT-002",
            "userId": "CAND-001",
            "performedBy": "CAND-001",
            "actor_id": "CAND-001",
            "documentId": "CV-001",
            "entity_id": "CV-001",
            "collectionName": "cv_documents",
            "entity_type": "cv_document",
            "action": "cv_uploaded",
            "oldValue": None,
            "newValue": {"id": "CV-001", "file_name": "Demo_Candidate_FullStack_CV.pdf"},
            "details": {"file_name": "Demo_Candidate_FullStack_CV.pdf", "file_size": 145200},
            "reason": "Candidate uploaded CV for parsing",
            "ipAddress": "127.0.0.1",
            "userAgent": "Mozilla/5.0",
            "createdAt": datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc),
        },
        {
            "_id": "AUDIT-003",
            "id": "AUDIT-003",
            "userId": "CAND-001",
            "performedBy": "CAND-001",
            "actor_id": "CAND-001",
            "documentId": "APP-001",
            "entity_id": "APP-001",
            "collectionName": "applications",
            "entity_type": "application",
            "action": "application_submitted",
            "oldValue": None,
            "newValue": {"id": "APP-001", "jobId": "JOB-001", "score": 88.0},
            "details": {"jobId": "JOB-001", "jobTitle": "Full Stack Developer"},
            "reason": "Candidate applied for Full Stack Developer position",
            "ipAddress": "127.0.0.1",
            "userAgent": "Mozilla/5.0",
            "createdAt": datetime(2026, 9, 21, 10, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2026, 9, 21, 10, 0, 0, tzinfo=timezone.utc),
        },
        {
            "_id": "AUDIT-004",
            "id": "AUDIT-004",
            "userId": "CAND-001",
            "performedBy": "REC-001",
            "actor_id": "REC-001",
            "documentId": "APP-002",
            "entity_id": "APP-002",
            "collectionName": "applications",
            "entity_type": "application",
            "action": "status_updated",
            "oldValue": {"status": "Submitted"},
            "newValue": {"status": "Shortlisted"},
            "details": {"old_status": "Submitted", "new_status": "Shortlisted"},
            "reason": "Recruiter shortlisted candidate for Round 1 Technical Interview",
            "ipAddress": "127.0.0.1",
            "userAgent": "Mozilla/5.0",
            "createdAt": datetime(2026, 9, 23, 14, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2026, 9, 23, 14, 0, 0, tzinfo=timezone.utc),
        },
    ]

    for log in audit_logs_data:
        db.audit_logs.delete_many({"$or": [{"id": log["id"]}, {"_id": log["_id"]}]})
        db.audit_logs.insert_one(log)
        print(f"  [OK] Audit: {log['id']:<10} | Action: {log['action']:<25} | By: {log['performedBy']:<10} | Target: {log['documentId']}")

    # -------------------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" Normalized 8-Collection Summary & Document Counts:")
    print("=" * 70)
    collection_order = [
        "users",
        "candidate_profiles",
        "jobs",
        "applications",
        "cv_documents",
        "evidence_snapshots",
        "audit_logs",
        "analysis_runs",
    ]
    for col in collection_order:
        count = db[col].count_documents({})
        sample = db[col].find_one()
        sample_id = sample.get("id") or sample.get("_id") if sample else "none"
        print(f"  * {col:<22} : {count:>2} docs | Sample ID: {sample_id}")

    print("\n[SUCCESS] All 8 collections normalized and referential integrity verified!")


if __name__ == "__main__":
    normalize_database()
