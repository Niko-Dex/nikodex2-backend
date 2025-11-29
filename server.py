import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import (
    abilities,
    auth,
    blogs,
    bot,
    images,
    nikos,
    posts,
    submissions,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


origins = os.environ["FASTAPI_ALLOWED_ORIGIN"].split(",")

app = FastAPI(title="NikodexV2 API", lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.detail}, headers=exc.headers
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(abilities.router)
app.include_router(auth.router)
app.include_router(blogs.router)
app.include_router(bot.router)
app.include_router(images.router)
app.include_router(nikos.router)
app.include_router(posts.router)
app.include_router(submissions.router)
app.include_router(users.router)


@app.get("/ping")
def ping():
    return Response(status_code=status.HTTP_200_OK)
