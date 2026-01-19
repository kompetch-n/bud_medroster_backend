from pymongo import MongoClient
from core.config import MONGO_URI, DB_NAME, COLLECTIONS

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

doctor_collection = db[COLLECTIONS["doctors"]]
shift_collection = db[COLLECTIONS["shifts"]]
department_collection = db[COLLECTIONS["departments"]]
