from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.constants.enums import UserRole
from app.exceptions.review import ReviewNotAllowedException
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.models.review import CourseReview
from app.models.user import User
from app.schemas.review import ReviewCreate
from app.services.audit_service import AuditService
from app.services.course_service import CourseService


class ReviewService:
    @staticmethod
    def list_reviews(db: Session, course_id: int, *, page: int = 1, size: int = 10) -> tuple[int, list[CourseReview]]:
        CourseService.get_course(db, course_id)
        query = (
            db.query(CourseReview)
            .options(joinedload(CourseReview.user))
            .filter(CourseReview.course_id == course_id)
            .order_by(CourseReview.updated_at.desc(), CourseReview.id.desc())
        )
        total = query.count()
        return total, query.offset((page - 1) * size).limit(size).all()

    @staticmethod
    def get_my_status(db: Session, user: User, course_id: int) -> tuple[bool, str | None, CourseReview | None]:
        CourseService.get_course(db, course_id)
        review = db.query(CourseReview).filter_by(user_id=user.id, course_id=course_id).first()
        can_review, reason = ReviewService.check_eligibility(db, user, course_id)
        return can_review, reason, review

    @staticmethod
    def check_eligibility(db: Session, user: User, course_id: int) -> tuple[bool, str | None]:
        if user.role != UserRole.STUDENT:
            return False, "讲师和管理员不能提交评价"
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            return False, "尚未注册该课程"
        total = db.query(Lesson).join(Chapter).filter(Chapter.course_id == course_id).count()
        completed = db.query(LessonProgress).filter(LessonProgress.enrollment_id == enrollment.id).count()
        if total == 0 or completed < total:
            return False, "完成全部课时后才能评价"
        return True, None

    @staticmethod
    def upsert_review(db: Session, user: User, course_id: int, payload: ReviewCreate, ip_address: str | None = None) -> CourseReview:
        CourseService.get_course(db, course_id)
        can_review, reason = ReviewService.check_eligibility(db, user, course_id)
        if not can_review:
            raise ReviewNotAllowedException(reason)
        review = db.query(CourseReview).filter_by(user_id=user.id, course_id=course_id).first()
        if review:
            before = {"rating": review.rating, "content": review.content}
            review.rating = payload.rating
            review.content = payload.content
            db.flush()
            AuditService.record(db, user_id=user.id, action="UPDATE", entity="CourseReview", entity_id=str(review.id), before_data=before, after_data=payload.model_dump(), ip_address=ip_address)
        else:
            review = CourseReview(course_id=course_id, user_id=user.id, rating=payload.rating, content=payload.content)
            db.add(review)
            db.flush()
            AuditService.record(db, user_id=user.id, action="CREATE", entity="CourseReview", entity_id=str(review.id), after_data=payload.model_dump(), ip_address=ip_address)
        ReviewService.recalculate_course_rating(db, course_id)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def recalculate_course_rating(db: Session, course_id: int) -> None:
        avg_rating, count = (
            db.query(func.avg(CourseReview.rating), func.count(CourseReview.id))
            .filter(CourseReview.course_id == course_id)
            .one()
        )
        course = db.get(Course, course_id)
        if course:
            course.rating = round(float(avg_rating or 0), 2)
            course.review_count = count
            db.flush()
