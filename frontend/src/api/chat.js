const API_BASE = '/api'

/**
 * 调用后端 Agent 服务接口。使用非流式 ainvoke 方案：
 * 等待整轮 ReAct 循环（工具选择 -> 调用 -> 观察 -> 继续判断）跑完后
 * 一次性返回最终回答。
 */
export async function sendMessage(message, threadId) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  })

  if (!res.ok) {
    let detail = `请求失败 (HTTP ${res.status})`
    try {
      const data = await res.json()
      if (data?.detail) detail = data.detail
    } catch {
      // ignore JSON parse error, use default message
    }
    throw new Error(detail)
  }

  return res.json()
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('后端服务不可用')
  return res.json()
}
