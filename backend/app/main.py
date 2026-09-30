from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine, Base
from app.models import user, instrument, application, attachment, appointment, inspection, certificate, audit, notification
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield


app = FastAPI(
    title="Legal Metrology Online Verification System",
    description="Prototype for PS-26036 / SIH26036 - Online Verification System for Weighing and Measuring Instruments",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "legal-metrology-verification"}


@app.get("/")
def root():
    return {
        "message": "Legal Metrology Online Verification System API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }