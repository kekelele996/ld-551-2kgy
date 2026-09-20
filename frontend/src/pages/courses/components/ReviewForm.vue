<template>
  <div class="review-form">
    <!-- 未登录 -->
    <el-alert v-if="!auth.user" type="info" :closable="false" show-icon>
      <template #title>
        登录后完成全部课时即可评价，<el-link type="primary" :underline="false" @click="$router.push('/login')">去登录</el-link>
      </template>
    </el-alert>

    <!-- 讲师 / 管理员 -->
    <el-alert v-else-if="!myStatus?.can_review && roleBlocked" type="warning" :closable="false" show-icon
      :title="myStatus?.reason || '讲师和管理员不能提交课程评价'" />

    <!-- 已登录但不满足条件（未注册 / 未完课） -->
    <el-alert v-else-if="!myStatus?.can_review" type="info" :closable="false" show-icon>
      <template #title>{{ myStatus?.reason }}</template>
      <template v-if="myStatus && myStatus.total_lessons > 0">
        <div class="progress-tip">
          <el-progress :percentage="progressPercent" :stroke-width="8" style="max-width: 260px" />
          <span>已完成 {{ myStatus.completed_lessons }}/{{ myStatus.total_lessons }} 课时</span>
        </div>
      </template>
    </el-alert>

    <!-- 可评价（首次或修改） -->
    <template v-else>
      <div class="form-title">
        <strong>{{ existingReview ? '修改我的评价' : '我要评价' }}</strong>
        <el-rate v-model="rating" :size="22" :texts="ratingTexts" show-text />
      </div>
      <el-input
        v-model="content"
        type="textarea"
        :rows="4"
        maxlength="500"
        show-word-limit
        placeholder="说说这门课的内容、讲师与收获（不超过 500 字，可不填）"
      />
      <div class="form-actions">
        <el-button type="primary" :loading="submitting" :disabled="rating === 0" @click="submit">
          {{ existingReview ? '保存修改' : '提交评价' }}
        </el-button>
        <el-button v-if="existingReview" @click="resetForm">还原</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { UserRole } from '@/constants/enums'
import { useAuthStore } from '@/stores/authStore'
import type { CourseReview, MyReviewStatus, ReviewSubmitPayload } from '@/types/review'

const props = defineProps<{
  myStatus: MyReviewStatus | null
  submitting: boolean
}>()

const emit = defineEmits<{
  submit: [payload: ReviewSubmitPayload]
}>()

const auth = useAuthStore()
const rating = ref(0)
const content = ref('')

const ratingTexts = ['很差', '较差', '还行', '满意', '非常满意']

const existingReview = computed<CourseReview | null>(() => props.myStatus?.review ?? null)
const roleBlocked = computed(() => auth.role === UserRole.INSTRUCTOR || auth.role === UserRole.ADMIN)
const progressPercent = computed(() => {
  if (!props.myStatus || props.myStatus.total_lessons === 0) return 0
  return Math.round((props.myStatus.completed_lessons / props.myStatus.total_lessons) * 100)
})

watch(
  () => props.myStatus,
  (status) => {
    rating.value = status?.review?.rating ?? 0
    content.value = status?.review?.content ?? ''
  },
  { immediate: true }
)

function resetForm() {
  rating.value = existingReview.value?.rating ?? 0
  content.value = existingReview.value?.content ?? ''
}

function submit() {
  if (rating.value < 1) return
  emit('submit', { rating: rating.value, content: content.value.trim() || undefined })
}
</script>

<style scoped>
.review-form {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 18px;
  margin-bottom: 20px;
  display: grid;
  gap: 14px;
}

.form-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.progress-tip {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  color: #6b7280;
  font-size: 13px;
}

.form-actions {
  display: flex;
  gap: 10px;
}
</style>
