<template>
  <section class="page" v-if="course">
    <div class="detail-head">
      <img :src="course.cover_image" :alt="course.title" />
      <div>
        <el-tag>{{ course.category }}</el-tag>
        <h1>{{ course.title }}</h1>
        <p>{{ course.description }}</p>
        <div class="detail-meta">
          <span>{{ course.instructor?.name }}</span>
          <span>{{ formatMinutes(course.total_duration) }}</span>
          <span>评分 {{ course.rating.toFixed(1) }}（{{ course.review_count }} 条评价）</span>
        </div>
        <strong class="price">{{ formatMoney(course.price) }}</strong>
        <div class="actions">
          <el-button type="primary" @click="buy">立即购买</el-button>
          <el-button @click="$router.push(`/learn/${course.id}`)">继续学习</el-button>
        </div>
      </div>
    </div>
    <el-tabs>
      <el-tab-pane label="大纲">
        <ChapterTree :chapters="chapters" />
      </el-tab-pane>
      <el-tab-pane label="介绍">
        <article class="rich-text">{{ course.description }}</article>
      </el-tab-pane>
      <el-tab-pane :label="`评价（${course.review_count}）`">
        <div class="review-section">
          <div v-if="!authStore.token" class="review-hint">
            <el-alert type="info" :closable="false" title="登录并完成全部课时可提交评价" />
          </div>
          <template v-else-if="reviewStore.myStatus">
            <div v-if="reviewStore.myStatus.can_review" class="review-form">
              <h3>{{ reviewStore.myStatus.review ? '我的评价（再次提交将覆盖原评价）' : '发表评价' }}</h3>
              <el-rate v-model="form.rating" :max="5" />
              <el-input
                v-model="form.content"
                type="textarea"
                :rows="4"
                maxlength="500"
                show-word-limit
                placeholder="分享你的学习体验（不超过 500 字）"
              />
              <el-button type="primary" :loading="submitting" @click="submit">
                {{ reviewStore.myStatus.review ? '更新评价' : '提交评价' }}
              </el-button>
            </div>
            <el-alert v-else type="info" :closable="false" :title="reviewStore.myStatus.reason || '当前无法评价该课程'" />
          </template>
          <el-divider />
          <div v-loading="reviewStore.loading">
            <el-empty v-if="!reviewStore.reviews.length" description="暂无评价" />
            <div v-for="review in reviewStore.reviews" :key="review.id" class="review-item">
              <div class="review-item-head">
                <strong>{{ review.user?.name || '学员' }}</strong>
                <el-rate :model-value="review.rating" disabled :max="5" />
                <span class="review-time">{{ formatDateTime(review.updated_at) }}</span>
              </div>
              <p class="review-content">{{ review.content }}</p>
            </div>
            <el-pagination
              v-if="reviewStore.total > pageSize"
              layout="prev, pager, next"
              :total="reviewStore.total"
              :page-size="pageSize"
              :current-page="page"
              @current-change="loadReviews"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ChapterTree from '@/components/ChapterTree.vue'
import { useAuthStore } from '@/stores/authStore'
import { useCourseStore } from '@/stores/courseStore'
import { useOrderStore } from '@/stores/orderStore'
import { useReviewStore } from '@/stores/reviewStore'
import { formatDateTime, formatMinutes, formatMoney } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const courseStore = useCourseStore()
const orderStore = useOrderStore()
const reviewStore = useReviewStore()
const course = computed(() => courseStore.currentCourse)
const chapters = computed(() => courseStore.chapters)
const courseId = Number(route.params.id)
const page = ref(1)
const pageSize = 10
const submitting = ref(false)
const form = reactive({ rating: 5, content: '' })

async function buy() {
  if (!course.value) return
  if (Number(course.value.price) === 0) {
    ElMessage.success('免费课程可直接进入学习')
    router.push(`/learn/${course.value.id}`)
    return
  }
  const order = await orderStore.createOrder(course.value.id)
  await orderStore.payOrder(order.id)
  ElMessage.success('支付成功，已注册课程')
  router.push(`/learn/${course.value.id}`)
}

function loadReviews(nextPage = 1) {
  page.value = nextPage
  reviewStore.fetchReviews(courseId, nextPage, pageSize)
}

async function submit() {
  if (form.rating < 1) {
    ElMessage.warning('请选择一至五星评分')
    return
  }
  if (!form.content.trim()) {
    ElMessage.warning('请填写评价内容')
    return
  }
  submitting.value = true
  try {
    const isUpdate = Boolean(reviewStore.myStatus?.review)
    await reviewStore.submitReview(courseId, form.rating, form.content.trim())
    ElMessage.success(isUpdate ? '评价已更新' : '评价提交成功')
    await Promise.all([
      courseStore.fetchCourse(courseId),
      reviewStore.fetchMyStatus(courseId),
      reviewStore.fetchReviews(courseId, page.value, pageSize),
    ])
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  reviewStore.reset()
  await courseStore.fetchCourse(courseId)
  loadReviews()
  if (authStore.token) {
    await reviewStore.fetchMyStatus(courseId)
    if (reviewStore.myStatus?.review) {
      form.rating = reviewStore.myStatus.review.rating
      form.content = reviewStore.myStatus.review.content
    }
  }
})
</script>

<style scoped>
.detail-head {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 28px;
  padding: 20px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 20px;
}

.detail-head img {
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  border-radius: 8px;
}

.detail-meta,
.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.price {
  display: block;
  margin: 16px 0;
  font-size: 28px;
  color: #b45309;
}

.rich-text {
  line-height: 1.8;
  background: #fff;
  padding: 18px;
  border-radius: 8px;
}

.review-section {
  background: #fff;
  padding: 18px;
  border-radius: 8px;
}

.review-form {
  display: grid;
  gap: 12px;
  justify-items: start;
}

.review-form h3 {
  margin: 0;
  font-size: 16px;
}

.review-form .el-input,
.review-form :deep(.el-textarea) {
  width: 100%;
}

.review-item {
  padding: 14px 0;
  border-bottom: 1px solid #f0f2f5;
}

.review-item-head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.review-time {
  color: #9ca3af;
  font-size: 13px;
}

.review-content {
  margin: 8px 0 0;
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
}

.el-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
