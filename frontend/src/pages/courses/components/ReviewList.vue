<template>
  <div class="review-list">
    <div v-if="loading" v-loading="true" class="review-loading" />
    <template v-else>
      <el-empty v-if="reviews.length === 0" description="还没有评价，完成全部课时后快来抢沙发吧" />
      <ul v-else>
        <li v-for="review in reviews" :key="review.id" class="review-item">
          <el-avatar :size="40">{{ (review.user?.name || '学')[0] }}</el-avatar>
          <div class="review-body">
            <div class="review-head">
              <strong>{{ review.user?.name || '学员' }}</strong>
              <el-rate :model-value="review.rating" disabled :size="14" />
              <span class="time">{{ formatDateTime(review.updated_at) }}</span>
            </div>
            <p v-if="review.content" class="review-content">{{ review.content }}</p>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { CourseReview } from '@/types/review'
import { formatDateTime } from '@/utils/format'

defineProps<{
  reviews: CourseReview[]
  loading: boolean
}>()
</script>

<style scoped>
.review-list {
  background: #fff;
  border-radius: 8px;
  padding: 8px 18px;
}

.review-loading {
  min-height: 120px;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.review-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.review-item:last-child {
  border-bottom: none;
}

.review-body {
  flex: 1;
}

.review-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.time {
  color: #9ca3af;
  font-size: 12px;
  margin-left: auto;
}

.review-content {
  margin: 8px 0 0;
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
