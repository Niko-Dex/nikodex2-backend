from fastapi import FastAPI
from contextlib import asynccontextmanager
import service

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    service.close_connection()

app = FastAPI(lifespan=lifespan)

@app.get("/niko/all")
def get_all_nikos():
    return service.get_all()

@app.get("/niko")
def get_one_niko():
    return service.get_by_name("Niko")