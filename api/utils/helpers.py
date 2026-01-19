def doctor_helper(doc):
    doc["_id"] = str(doc["_id"])
    return doc

def department_helper(doc):
    return {
        "_id": str(doc["_id"]),
        "department": doc.get("department"),
        "sub_departments": doc.get("sub_departments", [])
    }
