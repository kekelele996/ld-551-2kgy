from sqlalchemy.orm import Session, joinedload

from app.constants.enums import UserRole
from app.exceptions.course import CourseNotFoundException
from app.exceptions.review import ReviewPermissionException
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.course_review import CourseReview
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.models.user import User
from app.schemas.review import ReviewCreate
from app.services.audit_service import AuditService


class ReviewService:
    @staticmethod
    def list_course_reviews(db: Session, course_id: int) -> list[CourseReview]:
        # 已下架（ARCHIVED）课程的已有评价仍可读取，只要课程存在
        if not db.get(Course, course_id):
            raise CourseNotFoundException()
        return (
            db.query(CourseReview)
            .options(joinedload(CourseReview.user))
            .filter(CourseReview.course_id == course_id)
            .order_by(CourseReview.updated_at.desc(), CourseReview.id.desc())
            .all()
        )

    @staticmethod
    def get_my_review(db: Session, user: User, course_id: int) -> dict:
        if not db.get(Course, course_id):
            raise CourseNotFoundException()
        review = db.query(CourseReview).filter_by(course_id=course_id, user_id=user.id).first()
        enrolled, completed, total = ReviewService._lesson_completion(db, user, course_id)
        can_review, reason = ReviewService._review_eligibility(user, enrolled, completed, total)
        return {
            "can_review": can_review,
            "reason": reason,
            "completed_lessons": completed,
            "total_lessons": total,
            "review": review,
        }

    @staticmethod
    def submit_review(
        db: Session,
        user: User,
        course_id: int,
        payload: ReviewCreate,
        ip_address: str | None = None,
    ) -> tuple[CourseReview, str]:
        course = db.get(Course, course_id)
        if not course:
            raise CourseNotFoundException()
        if user.role != UserRole.STUDENT:
            raise ReviewPermissionException("讲师和管理员不能提交课程评价")

        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            raise ReviewPermissionException("请先注册该课程")

        _enrolled, completed, total = ReviewService._lesson_completion(db, user, course_id)
        if total == 0 or completed < total:
            raise ReviewPermissionException(f"需完成全部课时后才能评价（{completed}/{total}）")

        # 每名学员对同一课程仅保留一条评价，再次提交视为修改
        content = payload.content.strip() if payload.content and payload.content.strip() else None
        existing = db.query(CourseReview).filter_by(course_id=course_id, user_id=user.id).first()
        if existing:
            before = {"rating": existing.rating, "content": existing.content}
            existing.rating = payload.rating
            existing.content = content
            review = existing
            action = "UPDATE"
            AuditService.record(
                db,
                user_id=user.id,
                action=action,
                entity="CourseReview",
                entity_id=str(review.id),
                before_data=before,
                after_data={"rating": review.rating, "content": review.content},
                ip_address=ip_address,
            )
        else:
            review = CourseReview(course_id=course_id, user_id=user.id, rating=payload.rating, content=content)
            db.add(review)
            db.flush()
            action = "CREATE"
            AuditService.record(
                db,
                user_id=user.id,
                action=action,
                entity="CourseReview",
                entity_id=str(review.id),
                after_data={"course_id": course_id, "rating": review.rating, "content": review.content},
                ip_address=ip_address,
            )

        ReviewService._recalculate_course_rating(db, course)
        db.commit()
        db.refresh(review)
        return review, action

    @staticmethod
    def _review_eligibility(user: User, enrolled: bool, completed: int, total: int) -> tuple[bool, str | None]:
        if user.role != UserRole.STUDENT:
            return False, "讲师和管理员不能提交课程评价"
        if not enrolled:
            return False, "请先注册该课程"
        if total == 0 or completed < total:
            return False, f"完成全部课时后才能评价（{completed}/{total}）"
        return True, None

    @staticmethod
    def _lesson_completion(db: Session, user: User, course_id: int) -> tuple[bool, int, int]:
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        total = db.query(Lesson).join(Chapter).filter(Chapter.course_id == course_id).count()
        if not enrollment or total == 0:
            return enrollment is not None, 0, total
        completed = db.query(LessonProgress).filter(LessonProgress.enrollment_id == enrollment.id).count()
        return True, min(completed, total), total

    @staticmethod
    def _recalculate_course_rating(db: Session, course: Course) -> None:
        reviews = db.query(CourseReview).filter(CourseReview.course_id == course.id).all()
        if reviews:
            course.rating = round(sum(review.rating for review in reviews) / len(reviews), 2)
            course.review_count = len(reviews)
        else:
            course.rating = 0
            course.review_count = 0
