from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import service
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    service.close_connection()


origins = os.environ["FASTAPI_ALLOWED_ORIGIN"].split(",")

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/nikos/all")
def get_all_nikos():
    return service.get_all()

@app.get("/nikos/name")
def get_niko_by_name(name = "Niko"):
    return service.get_by_name(name)

@app.get("/nikos/")
def get_niko_by_id(id = 1):
    return service.get_niko_by_id(id)

@app.get("/nikos/count")
def get_niko_count():
    return service.get_nikos_count()

@app.get("/abilities")
def get_abilities():
    return service.get_abilities()

@app.get("/abilities/")
def get_ability(id = 1):
    return service.get_ability_by_id(id)