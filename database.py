"""MongoDB connection shared by all FastAPI routes."""

import os

from dotenv import load_dotenv
from pymongo import MongoClient

import certifi

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "talentverifyai")

# Configure client options with TLS support for Atlas connections
client_kwargs = {
    "serverSelectionTimeoutMS": 5000,
    "appname": "TalentVerifyAI",
    "tz_aware": True,
}

if "mongodb+srv" in MONGODB_URI or "tls=true" in MONGODB_URI.lower() or "ssl=true" in MONGODB_URI.lower():
    client_kwargs["tlsCAFile"] = certifi.where()

# Credentials stay in backend/.env and are never sent to the React application.
mongo_client = MongoClient(
    MONGODB_URI,
    **client_kwargs,
)
db = mongo_client[MONGODB_DB]


def connect_database() -> None:
    """Fail fast with a useful error when MongoDB cannot be reached."""
    mongo_client.admin.command("ping")


def close_database() -> None:
    mongo_client.close()
