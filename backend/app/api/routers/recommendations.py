from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import RecommendationRequest, RecommendationResponse
from app.services.recommendations import get_recommendations

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse)
def recommend(payload: RecommendationRequest, db: Session = Depends(get_db)) -> RecommendationResponse:
    results = get_recommendations(db, payload)
    return RecommendationResponse(results=results)
