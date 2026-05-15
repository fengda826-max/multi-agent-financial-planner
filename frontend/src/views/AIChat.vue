<template>
  <div class="chat-container">
    <div class="chat-main">
      <!-- 消息列表 -->
      <div class="chat-messages" ref="chatMessagesRef">
        <div v-if="messages.length === 0" class="chat-welcome">
          <div class="welcome-icon">🤖</div>
          <h2>{{ welcomeMessage }}</h2>
          <p>您可以向我咨询任何理财相关的问题</p>
        </div>

        <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="msg.role">
          <div class="message-avatar">
            {{ msg.role === 'assistant' ? '🤖' : '👤' }}
          </div>
          <div class="message-bubble" :class="msg.role">
            <div class="message-text">{{ msg.content }}</div>
            <div v-if="msg.action === 'replan'" class="message-action">
              <el-button type="warning" size="small" @click="handleReplan">
                需要调整方案？
              </el-button>
            </div>
          </div>
        </div>

        <div v-if="sending" class="message-row assistant">
          <div class="message-avatar">🤖</div>
          <div class="message-bubble assistant typing">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      </div>

      <!-- 快捷问题 -->
      <div class="quick-questions" v-if="messages.length === 0">
        <el-button v-for="q in quickQuestions" :key="q" size="small" @click="sendMessage(q)">
          {{ q }}
        </el-button>
      </div>

      <!-- 输入框 -->
      <div class="chat-input-area">
        <el-input
          v-model="inputText"
          placeholder="输入您的问题..."
          @keyup.enter="sendMessage()"
          :disabled="sending"
          size="large"
        >
          <template #append>
            <el-button @click="sendMessage()" :disabled="!inputText.trim() || sending" type="primary">
              发送
            </el-button>
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { orchestratorAPI, userAPI } from '../api/client'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  action?: string
}

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const chatMessagesRef = ref<HTMLElement | null>(null)
const userName = ref('')
const strategyData = ref<any>(null)
const marketData = ref<any>(null)

const welcomeMessage = ref('您好！我是您的专属理财顾问，可以帮您理解方案、分析市场、解答疑问。')

const quickQuestions = [
  '为什么我的长期仓位占比较高？',
  '现在市场情况怎么样？',
  '帮我分析一下我的资产配置',
  '什么是"四笔钱"框架？',
  '我的风险等级合适吗？',
]

function scrollToBottom() {
  nextTick(() => {
    const el = chatMessagesRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function loadContext() {
  const userId = localStorage.getItem('user_id')
  if (!userId) return

  try {
    const [userData, statusData] = await Promise.all([
      userAPI.getMe(),
      orchestratorAPI.getStatus(userId).catch(() => null)
    ])
    userName.value = userData.username
    if (statusData) {
      strategyData.value = statusData.strategy
      marketData.value = statusData.market_analysis
    }
  } catch { /* ignore */ }
}

async function sendMessage(text?: string) {
  const msg = (text || inputText.value).trim()
  if (!msg || sending.value) return

  messages.value.push({ role: 'user', content: msg })
  inputText.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const userId = localStorage.getItem('user_id')
    if (!userId) return

    // 构建上下文传给 coaching agent
    const data = await orchestratorAPI.chat({
      user_id: userId,
      user_message: msg,
      strategy: strategyData.value,
      market_analysis: marketData.value,
      conversation_history: messages.value.slice(-6).map(m => ({
        role: m.role,
        content: m.content
      }))
    })

    messages.value.push({
      role: 'assistant',
      content: data.message || '抱歉，我暂时无法回答这个问题。',
      action: data.action
    })
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '网络连接失败，请检查网络后重试。'
    })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function handleReplan() {
  sendMessage('请帮我重新规划方案')
}

onMounted(() => {
  loadContext()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  justify-content: center;
  padding: 20px;
  height: calc(100vh - 100px);
}

.chat-main {
  width: 100%;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.chat-welcome {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon { font-size: 56px; margin-bottom: 16px; }
.chat-welcome h2 { color: #1e293b; margin-bottom: 8px; font-size: 20px; }
.chat-welcome p { color: #94a3b8; font-size: 15px; }

.message-row {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: #f1f5f9;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-bubble.user {
  background: #3b82f6;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  background: #f1f5f9;
  color: #1e293b;
  border-bottom-left-radius: 4px;
}

.message-text { word-break: break-word; }

.message-action {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 16px 20px;
}

.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  animation: typing 1.4s infinite both;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 24px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
}

.quick-questions .el-button {
  font-size: 13px;
}

.chat-input-area {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
}
</style>
