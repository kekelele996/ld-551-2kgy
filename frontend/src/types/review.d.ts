import type { User } from '@/types/user'

export interface Review {
  id: number
  course_id: number
  user_id: number
  rating: number
  content: string
  created_at: string
  updated_at: string
  user?: User
}

export interface MyReviewStatus {
  can_review: boolean
  reason: string | null
  review: Review | null
}
