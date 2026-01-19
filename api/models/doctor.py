from pydantic import BaseModel, Field
from typing import Optional, List, Dict

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

    phone: Optional[str] = None
    line_id: Optional[str] = None
    email: Optional[str] = None

    specialties: Optional[List[str]] = []
    sub_specialties: Optional[List[str]] = []

    approvals: Optional[Dict[str, bool]] = {
        "shift": False,
        "leave": False
    }

    status: Optional[str] = None
