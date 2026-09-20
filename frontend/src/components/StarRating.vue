<template>
  <span class="star-rating" :class="{ 'is-large': size === 'large' }">
    <el-rate :model-value="rounded" disabled :size="iconSize" />
    <span v-if="showScore" class="score">{{ rating.toFixed(1) }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    rating: number
    showScore?: boolean
    size?: 'small' | 'default' | 'large'
  }>(),
  { showScore: false, size: 'default' }
)

// el-rate 只支持整星，展示平均分按四舍五入取整
const rounded = computed(() => Math.round(props.rating))
const iconSize = computed(() => (props.size === 'small' ? 14 : props.size === 'large' ? 22 : 18))
</script>

<style scoped>
.star-rating {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.score {
  color: #d97706;
  font-weight: 600;
}

.is-large .score {
  font-size: 20px;
}
</style>
