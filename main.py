import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.v1 import agent, delegation, socket
from app.core.config import settings

logging.basicConfig(level=logging.DEBUG)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)
app.add_middleware(
  CORSMiddleware,
  allow_origins=['*'],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

app.include_router(agent.router, prefix=settings.APP_VER_STR)
app.include_router(delegation.router, prefix=settings.APP_VER_STR)
app.include_router(socket.router, prefix=settings.APP_VER_STR)

@app.get("/", tags=["Root"])
async def health():
    """Check the app is running"""
    return {"status": "👌"}
