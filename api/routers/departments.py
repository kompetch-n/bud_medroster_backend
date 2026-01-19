from fastapi import APIRouter, HTTPException
from bson import ObjectId

from api.core.database import department_collection
from api.models.department import Department, SubDepartment, Shift
from api.utils.helpers import department_helper

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.post("")
def create_department(payload: Department):
    doc = payload.dict(by_alias=True, exclude={"id"})
    result = department_collection.insert_one(doc)
    return department_helper(
        department_collection.find_one({"_id": result.inserted_id})
    )

@router.get("")
def get_departments():
    return [
        department_helper(d)
        for d in department_collection.find().sort("department", 1)
    ]

@router.get("/{department_id}")
def get_department(department_id: str):
    doc = department_collection.find_one({"_id": ObjectId(department_id)})
    if not doc:
        raise HTTPException(404, "Department not found")
    return department_helper(doc)

@router.put("/{department_id}")
def update_department(department_id: str, payload: Department):
    data = payload.dict(by_alias=True, exclude={"id"})
    result = department_collection.update_one(
        {"_id": ObjectId(department_id)},
        {"$set": data}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Department not found")
    return department_helper(
        department_collection.find_one({"_id": ObjectId(department_id)})
    )

@router.delete("/{department_id}")
def delete_department(department_id: str):
    result = department_collection.delete_one({"_id": ObjectId(department_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Department not found")
    return {"message": "Department deleted successfully"}

@router.patch("/{department_id}/sub-departments")
def add_sub_department(department_id: str, payload: SubDepartment):
    department_collection.update_one(
        {"_id": ObjectId(department_id)},
        {"$push": {"sub_departments": payload.dict()}}
    )
    return department_helper(
        department_collection.find_one({"_id": ObjectId(department_id)})
    )

@router.patch("/{department_id}/sub-departments/{sub_name}/shifts")
def add_shift(department_id: str, sub_name: str, payload: Shift):
    department_collection.update_one(
        {
            "_id": ObjectId(department_id),
            "sub_departments.name": sub_name
        },
        {"$push": {"sub_departments.$.shifts": payload.dict()}}
    )
    return department_helper(
        department_collection.find_one({"_id": ObjectId(department_id)})
    )
