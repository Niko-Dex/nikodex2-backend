from fastapi import FastAPI
from contextlib import asynccontextmanager
import service

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    service.close_connection()

app = FastAPI(lifespan=lifespan)

@app.get("/nikos/all")
def get_all_nikos():
    return service.get_all()

@app.get("/nikos/name")
def get_niko_by_name(name = "Niko"):
    return service.get_by_name(name)

@app.get("/abilities")
def get_abilities():
    return service.get_abilities()

@app.get("/abilities/")
def get_ability(id = 1):
    return service.get_ability_by_id(id)