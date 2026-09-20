import os
import tempfile

_db_path = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.main import app  # noqa: E402
from app.constants.enums import CourseLevel, CourseStatus, UserRole, LessonType  # noqa: E402
from app.models import (  # noqa: E402
    Chapter,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    User,
)
from app.models.course_review import CourseReview  # noqa: E402

Base.metadata.create_all(bind=engine)
client = TestClient(app)

db = SessionLocal()

admin = User(email="admin@test.com", name="Admin", hashed_password=get_password_hash("pw"), role=UserRole.ADMIN)
instructor = User(email="ins@test.com", name="Teacher", hashed_password=get_password_hash("pw"), role=UserRole.INSTRUCTOR)
s1 = User(email="s1@test.com", name="Student1", hashed_password=get_password_hash("pw"), role=UserRole.STUDENT)
s2 = User(email="s2@test.com", name="Student2", hashed_password=get_password_hash("pw"), role=UserRole.STUDENT)
s3 = User(email="s3@test.com", name="Student3", hashed_password=get_password_hash("pw"), role=UserRole.STUDENT)
db.add_all([admin, instructor, s1, s2, s3])
db.flush()

course = Course(
    title="测试课程", description="desc", instructor_id=instructor.id, category="编程",
    level=CourseLevel.BEGINNER, price=0, cover_image="x.png", status=CourseStatus.PUBLISHED,
)
course_archived = Course(
    title="归档课程", description="desc", instructor_id=instructor.id, category="编程",
    level=CourseLevel.BEGINNER, price=0, cover_image="x.png", status=CourseStatus.ARCHIVED,
)
db.add_all([course, course_archived])
db.flush()
ch = Chapter(course_id=course.id, title="第一章", sort_order=1)
db.add(ch)
db.flush()
l1 = Lesson(chapter_id=ch.id, title="课时1", type=LessonType.TEXT, content="c1", duration=10, sort_order=1)
l2 = Lesson(chapter_id=ch.id, title="课时2", type=LessonType.VIDEO, content="c2", duration=20, sort_order=2)
db.add_all([l1, l2])
db.flush()

# s1 fully enrolled+completed; s2 enrolled but not finished; s3 not enrolled
e1 = Enrollment(user_id=s1.id, course_id=course.id)
e2 = Enrollment(user_id=s2.id, course_id=course.id)
db.add_all([e1, e2])
db.flush()
db.add_all([
    LessonProgress(enrollment_id=e1.id, lesson_id=l1.id),
    LessonProgress(enrollment_id=e1.id, lesson_id=l2.id),
    LessonProgress(enrollment_id=e2.id, lesson_id=l1.id),
])
# archived course: s1 completed and reviewed previously
ch2 = Chapter(course_id=course_archived.id, title="章", sort_order=1)
db.add(ch2)
db.flush()
l3 = Lesson(chapter_id=ch2.id, title="课时", type=LessonType.TEXT, content="c", duration=5, sort_order=1)
db.add(l3)
db.flush()
ea = Enrollment(user_id=s1.id, course_id=course_archived.id)
db.add(ea)
db.flush()
db.add(LessonProgress(enrollment_id=ea.id, lesson_id=l3.id))
db.add(CourseReview(course_id=course_archived.id, user_id=s1.id, rating=3, content="下架前的评价"))
db.commit()

cid, acid = course.id, course_archived.id


def token(user_id: int) -> dict:
    from app.core.security import create_access_token
    return {"Authorization": f"Bearer {create_access_token(str(user_id), {})}"}


H_ADMIN, H_INS, H_S1, H_S2, H_S3 = (
    token(admin.id), token(instructor.id), token(s1.id), token(s2.id), token(s3.id)
)

passed = []
failed = []


def check(name: str, cond: bool, detail=""):
    (passed if cond else failed).append(name)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")


# 1. 未登录：评价列表可读
r = client.get(f"/api/courses/{cid}/reviews")
check("公开接口-评价列表可匿名读取", r.status_code == 200 and r.json() == [], str(r.status_code))

# 2. 未登录：不能提交
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 5})
check("匿名提交被拒(401)", r.status_code == 401, str(r.status_code))

# 3. 讲师不能提交
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 5}, headers=H_INS)
check("讲师不能提交(403)", r.status_code == 403, r.json().get("message", ""))

# 4. 管理员不能提交
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 5}, headers=H_ADMIN)
check("管理员不能提交(403)", r.status_code == 403, r.json().get("message", ""))

# 5. 未注册学员不能提交
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 5}, headers=H_S3)
check("未注册学员不能提交(403)", r.status_code == 403, r.json().get("message", ""))

# 6. 未完课学员不能提交（s2 完成 1/2）
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 5}, headers=H_S2)
check("未完课学员不能提交(403)", r.status_code == 403 and "1/2" in r.json()["message"], r.json().get("message", ""))

# 7. 星级越界
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 6}, headers=H_S1)
check("6星校验失败(422)", r.status_code == 422)
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 0}, headers=H_S1)
check("0星校验失败(422)", r.status_code == 422)

# 8. 反馈超长
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 5, "content": "好" * 501}, headers=H_S1)
check("超过500字校验失败(422)", r.status_code == 422)

# 9. 正常提交（500 字边界允许）
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 4, "content": "很" * 500}, headers=H_S1)
check("完课学员提交成功", r.status_code == 200, str(r.status_code))
body = r.json()
check("提交后课程详情平均分=4.0", body["rating"] == 4.0, str(body["rating"]))
check("提交后评价人数=1", body["review_count"] == 1, str(body["review_count"]))

# 10. 我的评价状态
r = client.get(f"/api/courses/{cid}/reviews/me", headers=H_S1)
me = r.json()
check("我的评价-已评价回显", me["review"] is not None and me["review"]["rating"] == 4)
check("我的评价-含完课进度", me["completed_lessons"] == 2 and me["total_lessons"] == 2, str(me))
r = client.get(f"/api/courses/{cid}/reviews/me", headers=H_S2)
me2 = r.json()
check("我的评价-未完课不可评", me2["can_review"] is False and me2["completed_lessons"] == 1, str(me2))
r = client.get(f"/api/courses/{cid}/reviews/me", headers=H_INS)
me3 = r.json()
check("我的评价-讲师不可评", me3["can_review"] is False, str(me3))

# 11. 评价列表
r = client.get(f"/api/courses/{cid}/reviews")
items = r.json()
check("评价列表返回1条", len(items) == 1)
check("评价列表含学员信息", items[0]["user"] and items[0]["user"]["name"] == "Student1")

# 12. 再次提交=修改（upsert），不新增
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 2, "content": "改成分"}, headers=H_S1)
body = r.json()
check("修改提交成功", r.status_code == 200)
check("修改后平均分=2.0且人数仍为1", body["rating"] == 2.0 and body["review_count"] == 1, str((body["rating"], body["review_count"])))
r = client.get(f"/api/courses/{cid}/reviews")
check("修改后列表仍只有1条", len(r.json()) == 1 and r.json()[0]["rating"] == 2)

# 13. s1 完成 s2 也完成后 s2 评价，验证平均分聚合
db.add(LessonProgress(enrollment_id=e2.id, lesson_id=l2.id))
db.commit()
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 5, "content": "很棒"}, headers=H_S2)
body = r.json()
check("第二名学员评价成功", r.status_code == 200 and body["review_count"] == 2, str(body.get("review_count")))
check("平均分为(2+5)/2=3.5", body["rating"] == 3.5, str(body["rating"]))

# 14. 按更新时间倒序（s2 刚更新排在前）
r = client.get(f"/api/courses/{cid}/reviews")
order = [it["user_id"] for it in r.json()]
check("评价按更新时间倒序", order == [s2.id, s1.id], str(order))

import time
time.sleep(1.1)
# 15. s1 再次修改后应排到最前
r = client.put(f"/api/courses/{cid}/reviews", json={"rating": 3}, headers=H_S1)
r = client.get(f"/api/courses/{cid}/reviews")
order = [it["user_id"] for it in r.json()]
check("修改后该评价重新置顶", order[0] == s1.id and r.json()[0]["rating"] == 3, str(order))
detail = client.get(f"/api/courses/{cid}").json()
check("重新进入课程详情平均分实时一致", detail["rating"] == 4.0 and detail["review_count"] == 2, str((detail["rating"], detail["review_count"])))

# 16. 课程列表中的平均分与人数
r = client.get("/api/courses")
listed = {c["id"]: c for c in r.json()["items"]}
check("课程列表含平均分与评价人数", listed[cid]["rating"] == 4.0 and listed[cid]["review_count"] == 2, str(listed[cid]))

# 17. 课程下架后评价仍可读
r = client.get(f"/api/courses/{acid}/reviews")
check("下架课程评价仍可读取", r.status_code == 200 and len(r.json()) == 1 and r.json()[0]["rating"] == 3)

# 18. 不存在的课程
r = client.get("/api/courses/9999/reviews")
check("不存在课程评价列表404", r.status_code == 404)
r = client.put("/api/courses/9999/reviews", json={"rating": 5}, headers=H_S1)
check("不存在课程提交404", r.status_code == 404)

# 19. content 为空字符串允许
r = client.put(f"/api/courses/{acid}/reviews", json={"rating": 4, "content": ""}, headers=H_S1)
check("纯星级评价允许(空文本)", r.status_code == 200)
r = client.get(f"/api/courses/{acid}/reviews")
check("空文本落库为null且正常返回", r.json()[0]["content"] is None and r.json()[0]["rating"] == 4)

print(f"\n==== {len(passed)} passed, {len(failed)} failed ====")
if failed:
    print("FAILED:", failed)
    raise SystemExit(1)
