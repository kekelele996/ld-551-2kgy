from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.review import MyReviewStatus, ReviewCreate, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/courses/{course_id}/reviews", tags=["reviews"])


@router.get("", response_model=PageResponse[ReviewResponse])
def list_reviews(course_id: int, page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    total, items = ReviewService.list_reviews(db, course_id, page=page, size=size)
    return PageResponse(total=total, page=page, size=size, items=items)


@router.get("/me", response_model=MyReviewStatus)
def my_review_status(course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    can_review, reason, review = ReviewService.get_my_status(db, user, course_id)
    return MyReviewStatus(can_review=can_review, reason=reason, review=review)


@router.post("", response_model=ReviewResponse)
def submit_review(
    course_id: int,
    payload: ReviewCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReviewService.upsert_review(db, user, course_id, payload, request.client.host if request.client else None)
