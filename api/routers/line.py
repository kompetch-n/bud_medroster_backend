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

    print("🔥 LINE WEBHOOK HIT:", body)

    for event in body.get("events", []):
        user_id = event["source"].get("userId")
        msg = event.get("message", {}).get("text", "").strip()

        print("📩 MESSAGE:", msg)

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

        # -------------------------
        # รับเวรแทน
        # -------------------------
        if msg.startswith("รับ"):
            leave_id = msg.replace("รับ", "").strip()

            print("🟡 leave_id from msg:", leave_id)

            try:
                oid = ObjectId(leave_id)
            except:
                send_line_message(user_id, "❌ รหัสไม่ถูกต้อง")
                continue

            leave = leave_collection.find_one({"_id": oid})

            print("🟡 LEAVE:", leave)

            if not leave:
                send_line_message(user_id, "ไม่พบรายการ")
                continue

            # ✅ หา doctor จาก line_id
            doctor = doctor_collection.find_one({
                "line_id": user_id
            })

            print("🟢 USER ID:", user_id)
            print("🟢 DOCTOR:", doctor)

            if not doctor:
                send_line_message(user_id, "ไม่พบข้อมูลแพทย์")
                continue

            print("🟢 DOCTOR LICENSE:", doctor["medical_license"])
            print("🟢 REPLACEMENT LIST:", leave["replacement_doctors"])

            # ✅ เช็คว่ามีคนรับแล้วหรือยัง
            already = any(
                d["status"] == "accepted"
                for d in leave["replacement_doctors"]
            )

            if already:
                send_line_message(user_id, "มีผู้รับเวรแล้ว")
                continue

            # ✅ Atomic update
            result = leave_collection.update_one(
                {
                    "_id": oid,
                    "replacement_doctors.status": "pending"
                },
                {
                    "$set": {
                        "replacement_doctors.$[elem].status": "accepted",
                        "accepted_by": doctor["thai_full_name"],
                        "status": "matched"
                    }
                },
                array_filters=[
                    {"elem.doctor_id": doctor["_id"]}
                ]
            )

            print("🟣 UPDATE RESULT:", result.modified_count)

            if result.modified_count == 0:
                send_line_message(user_id, "มีคนรับไปก่อนแล้ว หรือไม่อยู่ในรายชื่อ")
                continue

            send_line_message(user_id, "✅ คุณได้รับเวรนี้แล้ว")


    return {"status": "ok"}

