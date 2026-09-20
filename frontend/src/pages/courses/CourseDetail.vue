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
          <StarRating :rating="course.rating" show-score />
          <span>{{ course.review_count }} 人评价</span>
        </div>
        <strong class="price">{{ formatMoney(course.price) }}</strong>
        <div class="actions">
          <el-button type="primary" @click="buy">立即购买</el-button>
          <el-button @click="$router.push(`/learn/${course.id}`)">继续学习</el-button>
        </div>
      </div>
    </div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="大纲" name="outline">
        <ChapterTree :chapters="chapters" />
      </el-tab-pane>
      <el-tab-pane label="介绍" name="intro">
        <article class="rich-text">{{ course.description }}</article>
      </el-tab-pane>
      <el-tab-pane :label="`评价（${course.review_count}）`" name="reviews" lazy>
        <ReviewForm
          :my-status="reviewStore.myStatus"
          :submitting="reviewStore.submitting"
          @submit="submitReview"
        />
        <ReviewList :reviews="reviewStore.reviews" :loading="reviewStore.loading" />
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ChapterTree from '@/components/ChapterTree.vue'
import StarRating from '@/components/StarRating.vue'
import ReviewForm from '@/pages/courses/components/ReviewForm.vue'
import ReviewList from '@/pages/courses/components/ReviewList.vue'
import { useCourseStore } from '@/stores/courseStore'
import { useOrderStore } from '@/stores/orderStore'
import { useReviewStore } from '@/stores/reviewStore'
import { useAuthStore } from '@/stores/authStore'
import type { ReviewSubmitPayload } from '@/types/review'
import { formatMinutes, formatMoney } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const orderStore = useOrderStore()
const reviewStore = useReviewStore()
const authStore = useAuthStore()
const course = computed(() => courseStore.currentCourse)
const chapters = computed(() => courseStore.chapters)
const activeTab = ref('outline')
let reviewsLoaded = false

async function loadReviews() {
  const courseId = Number(route.params.id)
  await reviewStore.fetchReviews(courseId)
  if (authStore.token) {
    await reviewStore.fetchMyReview(courseId)
  }
  reviewsLoaded = true
}

// 首次切到评价 Tab 时加载；提交后 reviewStore 已自行刷新
watch(activeTab, (tab) => {
  if (tab === 'reviews' && !reviewsLoaded) {
    loadReviews()
  }
})

async function submitReview(payload: ReviewSubmitPayload) {
  const hadReview = Boolean(reviewStore.myStatus?.review)
  const updated = await reviewStore.submitReview(Number(route.params.id), payload)
  // 课程详情的平均评分与评价人数立即更新；课程列表缓存也一并同步
  courseStore.applyCourseUpdate(updated)
  ElMessage.success(hadReview ? '评价已更新' : '评价提交成功')
}

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

watch(
  () => route.params.id,
  (id) => {
    if (id) {
      reviewsLoaded = false
      reviewStore.reset()
      activeTab.value = 'outline'
      courseStore.fetchCourse(Number(id))
    }
  }
)

onMounted(async () => {
  await courseStore.fetchCourse(Number(route.params.id))
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
  align-items: center;
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
</style>
