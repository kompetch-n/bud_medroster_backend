import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://kompetchn_db_user:4qlSudh0QgCrVV0u@cluster0.32mpebf.mongodb.net/?appName=Cluster0"
)

DB_NAME = "doctor_roster_system"

COLLECTIONS = {
    "doctors": "doctors",
    "shifts": "shift_requests",
    "departments": "departments"
}
