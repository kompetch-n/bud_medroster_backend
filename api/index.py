from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

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
DEPARTMENT_COLLECTION = "departments"

# -------------------------
# Database
# -------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
doctor_collection = db[COLLECTION_NAME]
shift_collection = db[SHIFT_COLLECTION]
department_collection = db[DEPARTMENT_COLLECTION]

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

    date: str              # YYYY-MM-DD
    start_time: str        # HH:mm
    end_time: str          # HH:mm
    remark: str | None = None

class Shift(BaseModel):
    name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class SubDepartment(BaseModel):
    name: str
    shifts: List[Shift] = []


class Department(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    department: str
    sub_departments: List[SubDepartment] = []



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

def department_helper(doc) -> dict:
    return {
        "_id": str(doc["_id"]),
        "department": doc.get("department"),
        "sub_departments": doc.get("sub_departments", []),
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

# -------------------------
# Department
# -------------------------
@app.post("/departments")
def create_department(payload: Department):
    doc = payload.dict(by_alias=True, exclude={"id"})
    result = department_collection.insert_one(doc)
    new_doc = department_collection.find_one({"_id": result.inserted_id})
    return department_helper(new_doc)

@app.get("/departments")
def get_departments():
    results = []
    for doc in department_collection.find().sort("department", 1):
        results.append(department_helper(doc))
    return results

@app.get("/departments/{department_id}")
def get_department(department_id: str):
    doc = department_collection.find_one({"_id": ObjectId(department_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Department not found")
    return department_helper(doc)

@app.put("/departments/{department_id}")
def update_department(
    department_id: str,
    payload: Department
):
    update_data = payload.dict(by_alias=True, exclude={"id"})

    result = department_collection.update_one(
        {"_id": ObjectId(department_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")

    doc = department_collection.find_one({"_id": ObjectId(department_id)})
    return department_helper(doc)

@app.delete("/departments/{department_id}")
def delete_department(department_id: str):
    result = department_collection.delete_one(
        {"_id": ObjectId(department_id)}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"message": "Department deleted successfully"}

@app.patch("/departments/{department_id}/sub-departments")
def add_sub_department(
    department_id: str,
    payload: SubDepartment
):
    result = department_collection.update_one(
        {"_id": ObjectId(department_id)},
        {"$push": {"sub_departments": payload.dict()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")

    doc = department_collection.find_one({"_id": ObjectId(department_id)})
    return department_helper(doc)

@app.patch("/departments/{department_id}/sub-departments/{sub_name}/shifts")
def add_shift(
    department_id: str,
    sub_name: str,
    payload: Shift
):
    result = department_collection.update_one(
        {
            "_id": ObjectId(department_id),
            "sub_departments.name": sub_name
        },
        {
            "$push": {
                "sub_departments.$.shifts": payload.dict()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Department or Sub-department not found"
        )

    doc = department_collection.find_one({"_id": ObjectId(department_id)})
    return department_helper(doc)
