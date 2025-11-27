import os
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware

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
