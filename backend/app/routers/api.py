from fastapi import APIRouter

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.books import router as books_router
from app.routers.chapter_rules import router as chapter_rules_router
from app.routers.health import router as health_router


api_router = APIRouter()
api_v1_router = APIRouter(prefix=settings.api_v1_prefix)

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chapter_rules_router)
api_router.include_router(books_router)
api_router.include_router(api_v1_router)
