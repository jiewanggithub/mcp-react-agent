<template>
  <div class="chat-window">
    <header class="chat-header">
      <h1>MCP ReAct Agent</h1>
      <span class="status" :class="{ online: backendOnline, offline: !backendOnline }">
        {{ backendOnline ? '服务在线' : '服务不可用' }}
      </span>
    </header>

    <div class="messages" ref="messagesRef">
      <div v-if="messages.length === 0" class="empty-hint">
        试着问我："北京今天天气怎么样？现在适合穿什么？"
      </div>
      <MessageBubble
        v-for="(m, idx) in messages"
        :key="idx"
        :role="m.role"
        :content="m.content"
        :is-error="m.isError"
      />
      <div v-if="loading" class="bubble-row assistant">
        <div class="avatar">AI</div>
        <div class="bubble loading-bubble">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    </div>

    <form class="input-bar" @submit.prevent="onSend">
      <input
        v-model="draft"
        type="text"
        placeholder="输入消息，按 Enter 发送..."
        :disabled="loading"
      />
      <button type="submit" :disabled="loading || !draft.trim()">发送</button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import MessageBubble from './MessageBubble.vue'
import { sendMessage, checkHealth } from '../api/chat.js'

const messages = ref([])
const draft = ref('')
const loading = ref(false)
const backendOnline = ref(true)
const messagesRef = ref(null)

// 每个浏览器会话生成一个唯一 thread_id，
// 对应后端 InMemorySaver checkpointer 的会话隔离维度，
// 避免多个用户/多个标签页之间的上下文互相串扰。
const threadId = crypto.randomUUID()

async function scrollToBottom() {
  await nextTick()
  const el = messagesRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function onSend() {
  const text = draft.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  draft.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const data = await sendMessage(text, threadId)
    messages.value.push({ role: 'assistant', content: data.reply })
  } catch (err) {
    // 异常降级提示：网络错误 / 后端 500 / Agent 执行失败等都会落到这里，
    // 以醒目的错误气泡呈现，而不是让界面卡死或白屏。
    messages.value.push({
      role: 'assistant',
      content: `抱歉，请求出现问题：${err.message}`,
      isError: true,
    })
    backendOnline.value = false
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

onMounted(async () => {
  try {
    await checkHealth()
    backendOnline.value = true
  } catch {
    backendOnline.value = false
  }
})
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 760px;
  margin: 0 auto;
  background: #fff;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.06);
}
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid #e5e7eb;
}
.chat-header h1 {
  font-size: 18px;
  margin: 0;
}
.status {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
}
.status.online {
  background: #dcfce7;
  color: #166534;
}
.status.offline {
  background: #fee2e2;
  color: #991b1b;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}
.empty-hint {
  color: #9ca3af;
  text-align: center;
  margin-top: 40px;
  font-size: 14px;
}
.input-bar {
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #e5e7eb;
}
.input-bar input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}
.input-bar input:focus {
  border-color: #2563eb;
}
.input-bar button {
  padding: 10px 20px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.input-bar button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
.loading-bubble {
  display: flex;
  gap: 4px;
  align-items: center;
  background: #f3f4f6;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  animation: blink 1.2s infinite ease-in-out;
}
.dot:nth-child(2) {
  animation-delay: 0.2s;
}
.dot:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}
</style>
