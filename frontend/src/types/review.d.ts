import type { User } from '@/types/user'

export interface CourseReview {
  id: number
  course_id: number
  user_id: number
  rating: number
  content: string | null
  created_at: string
  updated_at: string
  user?: User
}

export interface ReviewSubmitPayload {
  rating: number
  content?: string
}

export interface MyReviewStatus {
  can_review: boolean
  reason: string | null
  completed_lessons: number
  total_lessons: number
  review: CourseReview | null
}
