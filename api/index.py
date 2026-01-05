from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


# -------------------------
# Config
# -------------------------
load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://kompetchn_db_user:4qlSudh0QgCrVV0u@cluster0.32mpebf.mongodb.net/?appName=Cluster0"
)
DB_NAME = "doctor_roster_system"
COLLECTION_NAME = "doctors"
SHIFT_COLLECTION = "shift_requests"

# -------------------------
# Database
# -------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
doctor_collection = db[COLLECTION_NAME]
shift_collection = db[SHIFT_COLLECTION]

# -------------------------
# FastAPI
# -------------------------
app = FastAPI(title="BUD Doctor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Model
# -------------------------
class Doctor(BaseModel):
    id: Optional[str] = Field(None, alias="_id")

    ipus: Optional[str] = None
    department: Optional[str] = None

    care_provider_code: Optional[str] = None
    medical_license: Optional[str] = None

    english_title: Optional[str] = None
    english_first_name: Optional[str] = None
    english_last_name: Optional[str] = None

    thai_title: Optional[str] = None
    thai_first_name: Optional[str] = None
    thai_last_name: Optional[str] = None
    thai_full_name: Optional[str] = None

    # 🔹 Contact
    phone: Optional[str] = None
    line_id: Optional[str] = None
    email: Optional[str] = None

    work_type: Optional[str] = None
    work_type_group: Optional[str] = None

    department_group: Optional[str] = None

    specialties: Optional[List[str]] = []
    sub_specialties: Optional[List[str]] = []

    status: Optional[str] = None

class ShiftRequest(BaseModel):
    doctor_id: str
    thai_full_name: str
    care_provider_code: str
    department: Optional[str] = None

    date: str  # YYYY-MM-DD
    shift: str  # morning | afternoon | night


# -------------------------
# Helper
# -------------------------
def doctor_helper(doc) -> dict:
    return {
        "_id": str(doc["_id"]),
        "ipus": doc.get("ipus"),
        "department": doc.get("department"),
        "care_provider_code": doc.get("care_provider_code"),
        "medical_license": doc.get("medical_license"),
        "english_title": doc.get("english_title"),
        "english_first_name": doc.get("english_first_name"),
        "english_last_name": doc.get("english_last_name"),
        "thai_title": doc.get("thai_title"),
        "thai_first_name": doc.get("thai_first_name"),
        "thai_last_name": doc.get("thai_last_name"),
        "thai_full_name": doc.get("thai_full_name"),
        # 🔹 Contact
        "phone": doc.get("phone"),
        "line_id": doc.get("line_id"),
        "email": doc.get("email"),
        
        "work_type": doc.get("work_type"),
        "work_type_group": doc.get("work_type_group"),
        "department_group": doc.get("department_group"),
        "specialties": doc.get("specialties", []),
        "sub_specialties": doc.get("sub_specialties", []),
        "status": doc.get("status"),
    }

# -------------------------
# Create Doctor
# -------------------------
@app.post("/doctors")
def create_doctor(payload: Dict[str, Any] = Body(...)):
    result = doctor_collection.insert_one(payload)
    new_doc = doctor_collection.find_one({"_id": result.inserted_id})
    new_doc["_id"] = str(new_doc["_id"])
    return new_doc

# -------------------------
# Get All Doctors
# -------------------------
@app.get("/doctors")
def get_doctors():
    docs = []
    for doc in doctor_collection.find():
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs

# -------------------------
# Get Doctor by ID
# -------------------------
@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    doc = doctor_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doc["_id"] = str(doc["_id"])
    return doc

# -------------------------
# Update Doctor
# -------------------------
@app.put("/doctors/{doctor_id}")
def update_doctor(
    doctor_id: str,
    payload: Dict[str, Any] = Body(...)
):
    result = doctor_collection.update_one(
        {"_id": ObjectId(doctor_id)},
        {"$set": payload}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doc = doctor_collection.find_one({"_id": ObjectId(doctor_id)})
    doc["_id"] = str(doc["_id"])
    return doc

# -------------------------
# Delete Doctor
# -------------------------
@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: str):
    result = doctor_collection.delete_one({"_id": ObjectId(doctor_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"message": "Doctor deleted successfully"}

# -------------------------
# Create Doctor Request
# -------------------------
@app.post("/shift-requests")
def create_shift_request(payload: ShiftRequest):
    doc = payload.dict()
    doc["status"] = "pending"
    doc["requested_at"] = datetime.utcnow()

    shift_collection.insert_one(doc)

    return {"message": "Shift request submitted"}

@app.get("/shift-requests")
def get_shift_requests(
    status: Optional[str] = None,
    date: Optional[str] = None
):
    query = {}
    if status:
        query["status"] = status
    if date:
        query["date"] = date

    results = []
    for doc in shift_collection.find(query).sort("date", 1):
        doc["_id"] = str(doc["_id"])
        results.append(doc)

    return results

