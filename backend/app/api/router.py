from fastapi import APIRouter

from app.api.routers import (
    admin,
    auth,
    authenticity,
    places,
    promotions,
    recommendations,
    reviews,
    saved_lists,
    seller,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(places.router, tags=["places"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(authenticity.router, tags=["authenticity"])
api_router.include_router(promotions.router, tags=["promotions"])
api_router.include_router(saved_lists.router, tags=["saved-lists"])
api_router.include_router(recommendations.router, tags=["recommendations"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(seller.router, tags=["seller"])
api_router.include_router(admin.router, tags=["admin"])
