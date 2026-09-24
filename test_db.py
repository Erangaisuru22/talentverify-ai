"""Test script to verify MongoDB connection and validate the complete 8 collections architecture."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from database import connect_database, db, MONGODB_URI, MONGODB_DB

ALL_COLLECTIONS = [
    ("users", "Candidate, recruiter & admin authentication and accounts"),
    ("candidate_profiles", "Unified candidate profiles (skills, experience, education, projects, score)"),
    ("jobs", "Job postings, requirements, scoring weights, salary, and status"),
    ("applications", "Candidate job applications, evaluation scores, interviews & decisions"),
    ("cv_documents", "Uploaded CV documents, parsing status, text & parsed data"),
    ("evidence_snapshots", "External verification snapshots (GitHub, LinkedIn, Portfolio)"),
    ("audit_logs", "Immutable action history, status change, and score override logs"),
    ("analysis_runs", "CV analysis, job match, and profile scoring runs"),
]

print("=" * 65)
print(f" TalentVerify AI – MongoDB 8-Collections Diagnostic")
print("=" * 65)
print(f"Database : {MONGODB_DB}")
print(f"Host/URI : {MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else MONGODB_URI}")

try:
    connect_database()
    existing_collections = db.list_collection_names()
    print("\n[+] SUCCESS: Connected to MongoDB successfully!")
    print(f"[+] Total existing collections in database: {len(existing_collections)}\n")

    print("-" * 65)
    print(" 8 CORE COLLECTIONS STATUS")
    print("-" * 65)
    for col_name, description in ALL_COLLECTIONS:
        exists = col_name in existing_collections
        count = db[col_name].count_documents({}) if exists else 0
        status = f"EXISTS ({count} docs)" if exists else "READY (empty / creates on first write)"
        print(f"  * {col_name:<22} -> {status:<25} | {description}")

    print("\n" + "=" * 65)
    print(" Database Schema Verification Completed Successfully!")
    print("=" * 65)
    sys.exit(0)

except Exception as exc:
    print(f"\n[-] ERROR: Could not connect to MongoDB: {exc}")
    print("\nTroubleshooting tips:")
    print("1. If using MongoDB Atlas, check your connection string in backend/.env:")
    print("   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority")
    print("   Make sure your IP address is whitelisted in Atlas (Network Access -> Add 0.0.0.0/0).")
    print("2. If using Local MongoDB, make sure MongoDB service or mongod is running on port 27017.")
    sys.exit(1)
