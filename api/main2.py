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

    ipus: str
    department: str

    care_provider_code: str
    medical_license: str

    english_title: str
    english_first_name: str
    english_last_name: str

    thai_title: str
    thai_first_name: str
    thai_last_name: str
    thai_full_name: str

    work_type: str
    work_type_group: str

    department_group: str

    specialties: List[str]
    sub_specialties: List[str]

    status: str

# -------------------------
# Helper
# -------------------------
def doctor_helper(doc) -> dict:
    return {
        "_id": str(doc["_id"]),
        "ipus": doc["ipus"],
        "department": doc["department"],
        "care_provider_code": doc["care_provider_code"],
        "medical_license": doc["medical_license"],
        "english_title": doc["english_title"],
        "english_first_name": doc["english_first_name"],
        "english_last_name": doc["english_last_name"],
        "thai_title": doc["thai_title"],
        "thai_first_name": doc["thai_first_name"],
        "thai_last_name": doc["thai_last_name"],
        "thai_full_name": doc["thai_full_name"],
        "work_type": doc["work_type"],
        "work_type_group": doc["work_type_group"],
        "department_group": doc["department_group"],
        "specialties": doc["specialties"],
        "sub_specialties": doc["sub_specialties"],
        "status": doc["status"],
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
