from fastapi import FastAPI
import service

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/niko/all")
def get_all_nikos():
    return service.get_all()

@app.get("/niko")
def get_one_niko():
    return service.get_by_name("Niko")