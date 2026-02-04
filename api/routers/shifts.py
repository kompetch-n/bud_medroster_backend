from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional

from api.core.database import shift_collection, leave_collection, doctor_collection
from api.models.shift import ShiftRequest

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

# @router.get("/table")
# def get_shift_table(ipus: str, department: str, start: str, end: str):
#     query = {
#         "ipus": ipus,
#         "department": department,
#         "date": {"$gte": start, "$lte": end},
#         "status": {"$ne": "rejected"}
#     }

#     results = []
#     for doc in shift_collection.find(query):
#         doc["_id"] = str(doc["_id"])
#         doc["shift_key"] = f'{doc["sub_department"]}|{doc["shift_name"]}'
#         results.append(doc)
#     return results

# @router.get("/table")
# def get_shift_table(ipus: str, department: str, start: str, end: str):

#     query = {
#         "ipus": ipus,
#         "department": department,
#         "date": {"$gte": start, "$lte": end},
#         "status": {"$ne": "rejected"}
#     }

#     results = []

#     for doc in shift_collection.find(query):
#         doc["_id"] = str(doc["_id"])
#         doc["shift_key"] = f'{doc["sub_department"]}|{doc["shift_name"]}'
#         doc_date = doc["date"]

#         # 🔥 หา leave วันนั้น
#         leave = leave_collection.find_one({
#             "doctor_id": doc["doctor_id"],
#             "start_date": {"$lte": doc_date},
#             "end_date": {"$gte": doc_date},
#             "status": {"$in": ["waiting_replacement", "matched"]}
#         })

#         if leave:
#             doc["is_on_leave"] = True

#             accepted = next(
#                 (r for r in leave.get("replacement_doctors", [])
#                 if r.get("status") in ["approved", "matched", "accepted"]),
#                 None
#             )

#             if accepted:
#                 doc["replacement_name"] = accepted.get("doctor_name")


#         results.append(doc)

#     return results

@router.get("/table")
def get_shift_table(ipus: str, department: str, start: str, end: str):

    query = {
        "ipus": ipus,
        "department": department,
        "date": {"$gte": start, "$lte": end},
        "status": {"$ne": "rejected"}
    }

    results = []

    # ===============================
    # 1) SHIFT ปกติ
    # ===============================
    for doc in shift_collection.find(query):
        doc["_id"] = str(doc["_id"])
        doc["shift_key"] = f'{doc["sub_department"]}|{doc["shift_name"]}'
        results.append(doc)

    # ===============================
    # 2) SHIFT แพทย์ที่มาแทน (🔥 ตรงนี้แหละ)
    # ===============================
    matched_leaves = leave_collection.find({
        "status": "matched",
        "ipus": ipus,
        "department": department,
        "start_date": {"$lte": end},
        "end_date": {"$gte": start}
    })

    for leave in matched_leaves:
        accepted = leave.get("accepted_by")
        if not accepted:
            continue

        doctor = doctor_collection.find_one({
            "_id": ObjectId(accepted["doctor_id"])
        })
        if not doctor:
            continue

        start = datetime.strptime(leave["start_date"], "%Y-%m-%d")
        end = datetime.strptime(leave["end_date"], "%Y-%m-%d")

        d = start
        while d <= end:
            date_str = d.strftime("%Y-%m-%d")

            replacement_shift = {
                "_id": f"replacement-{leave['_id']}-{date_str}",
                "doctor_id": str(doctor["_id"]),
                "thai_first_name": doctor.get("thai_first_name"),
                "thai_last_name": doctor.get("thai_last_name"),

                "department": doctor.get("department"),
                "sub_department": leave.get("sub_department"),
                "shift_name": leave.get("shift_name"),
                "shift_key": f"{leave.get('sub_department')}|{leave.get('shift_name')}",

                "date": date_str,
                "replacement": True,
                "replacing_doctor_id": leave.get("doctor_id")
            }

        results.append(replacement_shift)
        d += timedelta(days=1)

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
