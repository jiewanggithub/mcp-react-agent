<template>
  <div class="bubble-row" :class="role">
    <div class="avatar">{{ role === 'user' ? '我' : 'AI' }}</div>
    <div class="bubble" :class="{ error: isError }">
      <div v-if="isError" class="error-text">{{ content }}</div>
      <div v-else class="markdown-body" v-html="renderedHtml"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  role: { type: String, required: true }, // 'user' | 'assistant'
  content: { type: String, required: true },
  isError: { type: Boolean, default: false },
})

// XSS 防护：Markdown 渲染出的 HTML 先经过 DOMPurify 消毒后再插入 DOM，
// 防止 Agent 回复中的恶意脚本被执行。
const renderedHtml = computed(() => {
  const rawHtml = marked.parse(props.content ?? '', { breaks: true })
  return DOMPurify.sanitize(rawHtml)
})
</script>

<style scoped>
.bubble-row {
  display: flex;
  gap: 10px;
  margin: 12px 0;
  align-items: flex-start;
}
.bubble-row.user {
  flex-direction: row-reverse;
}
.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #fff;
  background: #6b7280;
}
.bubble-row.user .avatar {
  background: #2563eb;
}
.bubble-row.assistant .avatar {
  background: #10b981;
}
.bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 10px;
  background: #f3f4f6;
  line-height: 1.6;
  word-break: break-word;
}
.bubble-row.user .bubble {
  background: #dbeafe;
}
.bubble.error {
  background: #fee2e2;
  color: #b91c1c;
}
.markdown-body :deep(p) {
  margin: 0.4em 0;
}
.markdown-body :deep(pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
}
.markdown-body :deep(code) {
  font-family: 'SFMono-Regular', Consolas, monospace;
}
</style>
