from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import doctors, shifts, departments, leaves

app = FastAPI(title="BUD Doctor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(doctors.router)
app.include_router(shifts.router)
app.include_router(departments.router)
app.include_router(leaves.router)
