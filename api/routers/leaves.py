from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime

from api.core.database import leave_collection, doctor_collection
from api.models.leave import LeaveRequest
from api.services.line_service import send_line_message

router = APIRouter(prefix="/leaves", tags=["Leaves"])


def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc


# ===============================
# CREATE LEAVE
# ===============================
@router.post("/")
def create_leave(data: LeaveRequest):
    doc = data.dict(by_alias=True)
    doc["created_at"] = datetime.utcnow()
    doc["status"] = "waiting_replacement"

    result = leave_collection.insert_one(doc)
    leave_id = str(result.inserted_id)

    # ✅ ส่ง LINE หาแพทย์ตัวแทน
    for r in doc["replacement_doctors"]:
        doctor = doctor_collection.find_one(
            {"medical_license": r["doctor_id"]}
        )

        if not doctor or not doctor.get("line_id"):
            continue

        send_line_message(
            doctor["line_id"],
            f"""
มีคำขอเวรแทน

วันที่: {doc['start_date']}
แพทย์: {doc['thai_full_name']}

พิมพ์:
รับ {leave_id}
เพื่อรับเวร
"""
        )

    doc["_id"] = leave_id
    return doc


# ===============================
# GET ALL
# ===============================
@router.get("/")
def get_leaves():
    leaves = []
    for doc in leave_collection.find().sort("created_at", -1):
        leaves.append(serialize(doc))
    return leaves


# ===============================
# GET BY DOCTOR
# ===============================
@router.get("/doctor/{doctor_id}")
def get_by_doctor(doctor_id: str):
    leaves = []
    for doc in leave_collection.find({"doctor_id": doctor_id}):
        leaves.append(serialize(doc))
    return leaves


# ===============================
# UPDATE
# ===============================
@router.put("/{leave_id}")
def update_leave(leave_id: str, data: LeaveRequest):
    leave_collection.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": data.dict(exclude_unset=True)}
    )
    return {"message": "updated"}


# ===============================
# DELETE
# ===============================
@router.delete("/{leave_id}")
def delete_leave(leave_id: str):
    leave_collection.delete_one({"_id": ObjectId(leave_id)})
    return {"message": "deleted"}


# ===============================
# APPROVE
# ===============================
@router.post("/{leave_id}/approve")
def approve_leave(leave_id: str, approver_name: str):
    leave_collection.update_one(
        {"_id": ObjectId(leave_id)},
        {
            "$set": {
                "status": "approved",
                "approved_by": approver_name,
                "approved_at": datetime.utcnow()
            }
        }
    )
    return {"message": "approved"}


# ===============================
# REJECT
# ===============================
@router.post("/{leave_id}/reject")
def reject_leave(leave_id: str, approver_name: str):
    leave_collection.update_one(
        {"_id": ObjectId(leave_id)},
        {
            "$set": {
                "status": "rejected",
                "approved_by": approver_name,
                "approved_at": datetime.utcnow()
            }
        }
    )
    return {"message": "rejected"}

@router.post("/{leave_id}/confirm")
def confirm_replacement(leave_id: str, doctor_id: str):

    leave = leave_collection.find_one({"_id": ObjectId(leave_id)})

    if not leave:
        raise HTTPException(404, "Leave not found")

    for d in leave["replacement_doctors"]:
        if d["doctor_id"] == doctor_id:
            d["status"] = "accepted"

    leave_collection.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {"replacement_doctors": leave["replacement_doctors"]}}
    )

    return {"message": "confirmed"}
