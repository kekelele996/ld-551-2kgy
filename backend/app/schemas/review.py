from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str | None = Field(default=None, max_length=500)


class ReviewResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    rating: int
    content: str | None = None
    created_at: datetime
    updated_at: datetime
    user: UserResponse | None = None

    model_config = {"from_attributes": True}


class MyReviewResponse(BaseModel):
    can_review: bool
    reason: str | None = None
    completed_lessons: int = 0
    total_lessons: int = 0
    review: ReviewResponse | None = None
