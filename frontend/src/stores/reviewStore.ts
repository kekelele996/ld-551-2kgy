import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Course } from '@/types/course'
import type { CourseReview, MyReviewStatus, ReviewSubmitPayload } from '@/types/review'
import request from '@/utils/request'

export const useReviewStore = defineStore('review', () => {
  const reviews = ref<CourseReview[]>([])
  const myStatus = ref<MyReviewStatus | null>(null)
  const loading = ref(false)
  const submitting = ref(false)

  async function fetchReviews(courseId: number) {
    loading.value = true
    try {
      reviews.value = await request.get<unknown, CourseReview[]>(`/courses/${courseId}/reviews`)
    } finally {
      loading.value = false
    }
  }

  async function fetchMyReview(courseId: number) {
    myStatus.value = await request.get<unknown, MyReviewStatus>(`/courses/${courseId}/reviews/me`)
  }

  // 提交或修改评价；后端在同一事务内更新课程平均分与评价人数，返回最新课程详情
  async function submitReview(courseId: number, payload: ReviewSubmitPayload): Promise<Course> {
    submitting.value = true
    try {
      const course = await request.put<unknown, Course>(`/courses/${courseId}/reviews`, payload)
      await Promise.all([fetchReviews(courseId), fetchMyReview(courseId)])
      return course
    } finally {
      submitting.value = false
    }
  }

  function reset() {
    reviews.value = []
    myStatus.value = null
  }

  return { reviews, myStatus, loading, submitting, fetchReviews, fetchMyReview, submitReview, reset }
})
