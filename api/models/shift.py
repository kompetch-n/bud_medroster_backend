from pydantic import BaseModel
from typing import Optional

class ShiftRequest(BaseModel):
    doctor_id: str
    thai_full_name: str
    care_provider_code: str
    ipus: str
    department: str
    sub_department: str
    shift_name: str
    date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    remark: Optional[str] = None
