from fastapi import APIRouter

from app.api.routers import (
    auth,
    authenticity,
    places,
    promotions,
    recommendations,
    reviews,
    saved_lists,
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(places.router, tags=["places"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(authenticity.router, tags=["authenticity"])
api_router.include_router(promotions.router, tags=["promotions"])
api_router.include_router(saved_lists.router, tags=["saved-lists"])
api_router.include_router(recommendations.router, tags=["recommendations"])
