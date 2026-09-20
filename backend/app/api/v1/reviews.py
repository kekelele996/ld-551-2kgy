from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.constants.enums import UserRole
from app.core.database import get_db
from app.models.user import User
from app.schemas.course import CourseDetailResponse
from app.schemas.review import MyReviewResponse, ReviewCreate, ReviewResponse
from app.services.course_service import CourseService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/courses", tags=["reviews"])


@router.get("/{course_id}/reviews", response_model=list[ReviewResponse])
def list_course_reviews(course_id: int, db: Session = Depends(get_db)):
    return ReviewService.list_course_reviews(db, course_id)


@router.get("/{course_id}/reviews/me", response_model=MyReviewResponse)
def get_my_review(course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ReviewService.get_my_review(db, user, course_id)


@router.put("/{course_id}/reviews", response_model=CourseDetailResponse)
def submit_review(
    course_id: int,
    payload: ReviewCreate,
    request: Request,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    ReviewService.submit_review(db, user, course_id, payload, request.client.host if request.client else None)
    # 平均评分与评价人数已在同一事务中更新，立即返回最新课程详情
    return CourseService.get_course(db, course_id)
