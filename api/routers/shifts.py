from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional

from api.core.database import shift_collection, leave_collection, doctor_collection
from api.models import leave
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

    # 1. ดึงเวรปกติ
    for doc in shift_collection.find(query):
        doc["_id"] = str(doc["_id"])
        doc["shift_key"] = f'{doc["sub_department"]}|{doc["shift_name"]}'
        results.append(doc)

    # 2. ดึงเวรแทนจากการลา (สถานะ matched)
    matched_leaves = leave_collection.find({
        "status": "matched",
        "ipus": ipus,
        "department": department,
        # ตรวจสอบว่าช่วงที่ลามีส่วนใดส่วนหนึ่งทับซ้อนกับช่วงที่เรียกดูตาราง
        "start_date": {"$lte": end},
        "end_date": {"$gte": start}
    })

    for leave in matched_leaves:
        accepted = leave.get("accepted_by")
        if not accepted: continue

        # หาข้อมูลแพทย์ที่มาแทนเพื่อเอาชื่อไทย
        replacement_doc = doctor_collection.find_one({"_id": ObjectId(accepted["doctor_id"])})
        
        # วนลูปสร้าง Record สำหรับทุกวันที่ลา (ถ้าลาหลายวัน)
        curr_d = datetime.strptime(max(start, leave["start_date"]), "%Y-%m-%d")
        end_d = datetime.strptime(min(end, leave["end_date"]), "%Y-%m-%d")

        while curr_d <= end_d:
            date_str = curr_d.strftime("%Y-%m-%d")
            results.append({
                "_id": f"replacement-{leave['_id']}-{date_str}",
                "doctor_id": accepted["doctor_id"],
                "thai_full_name": accepted.get("name"), # ใช้ชื่อจาก accepted_by โดยตรง
                "thai_first_name": replacement_doc.get("thai_first_name") if replacement_doc else "",
                "thai_last_name": replacement_doc.get("thai_last_name") if replacement_doc else "",
                "sub_department": leave.get("sub_department"),
                "shift_name": leave.get("shift_name"),
                "shift_key": f"{leave.get('sub_department')}|{leave.get('shift_name')}",
                "date": date_str,
                "replacement": True,
                "original_doctor_name": leave.get("thai_full_name") # เก็บชื่อแพทย์เดิมไว้แสดงผล
            })
            curr_d += timedelta(days=1)

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
