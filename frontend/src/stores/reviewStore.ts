import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MyReviewStatus, Review } from '@/types/review'
import request from '@/utils/request'

interface PageResult<T> {
  total: number
  page: number
  size: number
  items: T[]
}

export const useReviewStore = defineStore('review', () => {
  const reviews = ref<Review[]>([])
  const total = ref(0)
  const myStatus = ref<MyReviewStatus | null>(null)
  const loading = ref(false)

  async function fetchReviews(courseId: number, page = 1, size = 10) {
    loading.value = true
    try {
      const data = await request.get<unknown, PageResult<Review>>(`/courses/${courseId}/reviews`, { params: { page, size } })
      reviews.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchMyStatus(courseId: number) {
    myStatus.value = await request.get<unknown, MyReviewStatus>(`/courses/${courseId}/reviews/me`)
  }

  async function submitReview(courseId: number, rating: number, content: string) {
    return request.post<unknown, Review>(`/courses/${courseId}/reviews`, { rating, content })
  }

  function reset() {
    reviews.value = []
    total.value = 0
    myStatus.value = null
  }

  return { reviews, total, myStatus, loading, fetchReviews, fetchMyStatus, submitReview, reset }
})
