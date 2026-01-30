from fastapi import APIRouter, Request
from datetime import datetime

from api.core.database import doctor_collection, session_collection
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

            send_line_message(
                user_id,
                f"ยืนยัน {doctor.get('thai_full_name')}\nพิมพ์ 1=ยืนยัน 2=ยกเลิก"
            )

        # -------------------------
        # STATE: confirm
        # -------------------------
        elif state == "confirm":
            if msg == "1":
                doctor_collection.update_one(
                    {"_id": session["context"]["doctor_id"]},
                    {"$set": {"line_id": user_id}}
                )

                update_state(user_id, "idle")

                send_line_message(user_id, "✅ ลงทะเบียนสำเร็จ")

            elif msg == "2":
                update_state(user_id, "idle")
                send_line_message(user_id, "ยกเลิกแล้ว")

    return {"status": "ok"}
