from fastapi import APIRouter, HTTPException, Body
from bson import ObjectId
from typing import Dict, Any

from core.database import doctor_collection
from utils.helpers import doctor_helper

router = APIRouter(prefix="/doctors", tags=["Doctors"])

@router.post("")
def create_doctor(payload: Dict[str, Any] = Body(...)):
    result = doctor_collection.insert_one(payload)
    doc = doctor_collection.find_one({"_id": result.inserted_id})
    return doctor_helper(doc)

@router.get("")
def get_doctors():
    return [doctor_helper(d) for d in doctor_collection.find()]

@router.get("/{doctor_id}")
def get_doctor(doctor_id: str):
    doc = doctor_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doc:
        raise HTTPException(404, "Doctor not found")
    return doctor_helper(doc)

@router.put("/{doctor_id}")
def update_doctor(doctor_id: str, payload: Dict[str, Any]):
    payload.pop("_id", None)
    payload.pop("id", None)

    result = doctor_collection.update_one(
        {"_id": ObjectId(doctor_id)},
        {"$set": payload}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Doctor not found")

    return doctor_helper(
        doctor_collection.find_one({"_id": ObjectId(doctor_id)})
    )

@router.delete("/{doctor_id}")
def delete_doctor(doctor_id: str):
    result = doctor_collection.delete_one({"_id": ObjectId(doctor_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Doctor not found")
    return {"message": "Doctor deleted successfully"}
