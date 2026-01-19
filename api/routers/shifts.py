from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from typing import Optional

from core.database import shift_collection
from models.shift import ShiftRequest

router = APIRouter(prefix="/shift-requests", tags=["Shifts"])

@router.post("")
def create_shift_request(payload: ShiftRequest):
    doc = payload.dict()
    doc["status"] = "pending"
    doc["requested_at"] = datetime.utcnow()
    shift_collection.insert_one(doc)
    return {"message": "Shift request submitted"}

@router.get("")
def get_shift_requests(status: Optional[str] = None, date: Optional[str] = None):
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

@router.get("/table")
def get_shift_table(ipus: str, department: str, start: str, end: str):
    query = {
        "ipus": ipus,
        "department": department,
        "date": {"$gte": start, "$lte": end},
        "status": {"$ne": "rejected"}
    }

    results = []
    for doc in shift_collection.find(query):
        doc["_id"] = str(doc["_id"])
        doc["shift_key"] = f'{doc["sub_department"]}|{doc["shift_name"]}'
        results.append(doc)
    return results

@router.patch("/{request_id}/status")
def update_shift_status(request_id: str, status: str):
    result = shift_collection.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Request not found")
    return {"message": "Status updated"}
