from fastapi import APIRouter, Request
from datetime import datetime
from bson import ObjectId

from api.core.database import doctor_collection, session_collection, leave_collection
from api.models.line import SendLineRequest
from api.services.line_service import send_line_message

router = APIRouter()

# -------------------------
# Session helper
# -------------------------
def get_session(user_id):
    session = session_collection.find_one({"user_id": user_id})

    if not session:
        session = {
            "user_id": user_id,
            "state": "idle",
            "updated_at": datetime.utcnow()
        }
        session_collection.insert_one(session)

    return session

def update_state(user_id, state, context=None):
    session_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "state": state,
                "context": context or {},
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )

@router.post("/send-line")
def send_line_api(data: SendLineRequest):
    result = send_line_message(data.to, data.message)

    return {
        "status": "sent",
        "line_response": result
    }

# -------------------------
# Webhook
# -------------------------

# @router.post("/webhook/line")
# async def webhook(request: Request):
#     return {"status": "ok"}


@router.post("/webhook/line")
async def webhook(request: Request):
    body = await request.json()

    for event in body.get("events", []):
        user_id = event["source"].get("userId")
        msg = event.get("message", {}).get("text", "").strip()

        if not user_id or not msg:
            continue

        session = get_session(user_id)
        state = session["state"]

        # -------------------------
        # STATE: idle → รับรหัสแพทย์
        # -------------------------
        if state == "idle":
            doctor = doctor_collection.find_one(
                {"care_provider_code": msg}
            )

            if not doctor:
                send_line_message(user_id, "❌ ไม่พบรหัสแพทย์")
                continue

            update_state(user_id, "confirm", {
                "doctor_id": str(doctor["_id"])
            })

            doctor_name = f"{doctor.get('thai_first_name', '')} {doctor.get('thai_last_name', '')}".strip()

            send_line_message(
                user_id,
                f"ยืนยัน {doctor_name}\nพิมพ์ 1=ยืนยัน 2=ยกเลิก"
            )

        # -------------------------
        # STATE: confirm
        # -------------------------
        # elif state == "confirm":
        #     if msg == "1":
        #         leave_id = session["context"].get("leave_id")

        #         accepted_by = {
        #             "doctor_id": str(doctor["_id"]),
        #             "name": f"{doctor.get('thai_first_name', '')} {doctor.get('thai_last_name', '')}".strip(),
        #             "line_id": user_id,
        #             "accepted_at": datetime.utcnow()
        #         }

        #         result = leave_collection.update_one(
        #             {
        #                 "_id": ObjectId(leave_id),
        #                 "replacement_doctors": {
        #                     "$elemMatch": {
        #                         "doctor_id": str(doctor["_id"]),
        #                         "status": "pending"
        #                     }
        #                 }
        #             },
        #             {
        #                 "$set": {
        #                     "replacement_doctors.$.status": "matched",
        #                     "accepted_by": accepted_by,
        #                     "status": "matched"
        #                 }
        #             }
        #         )

        #         if result.matched_count == 0:
        #             send_line_message(user_id, "❌ มีผู้อื่นรับเวรนี้ไปแล้ว")
        #             update_state(user_id, "idle")
        #             return {"status": "no-match"}

        #         update_state(user_id, "idle")
        #         send_line_message(user_id, "✅ รับเวรแทนเรียบร้อยแล้ว")

        #     elif msg == "2":
        #         update_state(user_id, "idle")
        #         send_line_message(user_id, "ยกเลิกแล้ว")

       # -------------------------
        # STATE: waiting_accept_leave
        # -------------------------
        elif state == "waiting_accept_leave":

            if msg.lower() != "ok":
                send_line_message(user_id, "พิมพ์ OK เพื่อยืนยันรับเวร")
                continue

            leave_id = session["context"]["leave_id"]

            leave = leave_collection.find_one({
                "_id": ObjectId(leave_id)
            })

            if not leave:
                send_line_message(user_id, "ไม่พบรายการ")
                update_state(user_id, "idle")
                continue

            doctor = doctor_collection.find_one({
                "line_id": user_id
            })

            if not doctor:
                send_line_message(user_id, "กรุณาลงทะเบียน LINE ก่อน")
                update_state(user_id, "idle")
                continue

            # เช็คว่ามีคนรับแล้วหรือยัง
            already = any(
                d["status"] == "matched"
                for d in leave["replacement_doctors"]
            )

            if already:
                send_line_message(user_id, "มีคนรับเวรไปแล้ว")
                update_state(user_id, "idle")
                continue

            doctor_name = f"{doctor.get('first_name', '')} {doctor.get('last_name', '')}".strip()
            accepted_by = {
                "doctor_id": str(doctor["_id"]),
                "name": f"{doctor.get('thai_full_name', '')}".strip(),
                "line_id": user_id,
                "accepted_at": datetime.utcnow()
            }

            result = leave_collection.update_one(
                {
                    "_id": ObjectId(leave_id),
                    "replacement_doctors": {
                        "$elemMatch": {
                            "doctor_id": str(doctor["_id"]),
                            "status": "pending"
                        }
                    }
                },
                {
                    "$set": {
                        "replacement_doctors.$.status": "matched",
                        "accepted_by": accepted_by,
                        "status": "matched"
                    }
                }
            )

            if result.modified_count == 0:
                send_line_message(user_id, "คุณไม่ได้อยู่ในรายชื่อแพทย์แทน")
                update_state(user_id, "idle")
                continue

            send_line_message(user_id, "✅ รับเวรสำเร็จ")

            update_state(user_id, "idle")
            continue


    return {"status": "ok"}

