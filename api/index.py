from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import doctors, shifts, departments

app = FastAPI(title="BUD Doctor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(doctors.router)
app.include_router(shifts.router)
app.include_router(departments.router)
