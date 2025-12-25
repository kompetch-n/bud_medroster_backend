from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

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

# -------------------------
# Database
# -------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
doctor_collection = db[COLLECTION_NAME]

# -------------------------
# FastAPI
# -------------------------
app = FastAPI(title="BUD Doctor API")

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

    work_type: Optional[str] = None
    work_type_group: Optional[str] = None

    department_group: Optional[str] = None

    specialties: Optional[List[str]] = []
    sub_specialties: Optional[List[str]] = []

    status: Optional[str] = None

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
@app.post("/doctors", response_model=Doctor)
def create_doctor(doctor: Doctor):
    data = doctor.dict(by_alias=True, exclude={"id"})
    result = doctor_collection.insert_one(data)
    new_doc = doctor_collection.find_one({"_id": result.inserted_id})
    return doctor_helper(new_doc)

# -------------------------
# Get All Doctors
# -------------------------
@app.get("/doctors", response_model=List[Doctor])
def get_doctors():
    return [doctor_helper(doc) for doc in doctor_collection.find()]

# -------------------------
# Get Doctor by ID
# -------------------------
@app.get("/doctors/{doctor_id}", response_model=Doctor)
def get_doctor(doctor_id: str):
    doc = doctor_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor_helper(doc)

# -------------------------
# Update Doctor
# -------------------------
@app.put("/doctors/{doctor_id}", response_model=Doctor)
def update_doctor(doctor_id: str, doctor: Doctor):
    data = doctor.dict(by_alias=True, exclude={"id"})
    result = doctor_collection.update_one(
        {"_id": ObjectId(doctor_id)},
        {"$set": data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Doctor not found")

    updated_doc = doctor_collection.find_one({"_id": ObjectId(doctor_id)})
    return doctor_helper(updated_doc)

# -------------------------
# Delete Doctor
# -------------------------
@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: str):
    result = doctor_collection.delete_one({"_id": ObjectId(doctor_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"message": "Doctor deleted successfully"}
