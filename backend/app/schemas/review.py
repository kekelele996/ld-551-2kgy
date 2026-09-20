from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str = Field(min_length=1, max_length=500)


class ReviewResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    rating: int
    content: str
    created_at: datetime
    updated_at: datetime
    user: UserResponse | None = None

    model_config = {"from_attributes": True}


class MyReviewStatus(BaseModel):
    can_review: bool
    reason: str | None = None
    review: ReviewResponse | None = None
