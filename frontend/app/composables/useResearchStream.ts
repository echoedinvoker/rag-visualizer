import { ref } from 'vue'
import type { NodeStatus } from './useGraphState'

export interface LogEntry {
  id: number
  node: string
  event: string
  message: string
  details?: Record<string, any>
  timestamp: number
}

export function useResearchStream(
  updateNode: (id: string, status: NodeStatus, details?: Record<string, any>) => void,
  resetAll: () => void,
) {
  const isResearching = ref(false)
  const logs = ref<LogEntry[]>([])
  const report = ref<{ content: string; sources: string[] } | null>(null)
  const error = ref<string | null>(null)
  let abortController: AbortController | null = null
  let logCounter = 0
  let disconnectTimer: ReturnType<typeof setTimeout> | null = null

  function addLog(node: string, event: string, message: string, details?: Record<string, any>) {
    logs.value.push({
      id: ++logCounter,
      node,
      event,
      message,
      details,
      timestamp: Date.now(),
    })
  }

  function resetDisconnectTimer() {
    if (disconnectTimer) clearTimeout(disconnectTimer)
    disconnectTimer = setTimeout(() => {
      if (isResearching.value) {
        error.value = 'Connection lost'
        isResearching.value = false
      }
    }, 35_000) // 35s = 2x heartbeat + tolerance
  }

  function handleEvent(data: Record<string, any>) {
    resetDisconnectTimer()
    const event = data.event as string
    const node = data.node as string

    switch (event) {
      case 'node_start':
        updateNode(node, 'running')
        break

      case 'route_decision':
        updateNode('router', 'completed', { decision: data.decision })
        addLog('router', event,
          data.decision === 'vector_store' ? 'log.routing_vector' : 'log.routing_web',
          data)
        break

      case 'documents_retrieved':
        updateNode('retriever', 'completed', { count: data.count })
        addLog('retriever', event, 'log.retrieving', { count: data.count, sources: data.sources })
        break

      case 'doc_graded':
        // Incremental update on grader
        addLog('grader', event, `${data.doc_id}: ${data.relevant ? '✓' : '✗'}`, data)
        break

      case 'grading_complete':
        updateNode('grader', 'completed', { passed: data.passed, failed: data.failed })
        if (data.fallback) {
          addLog('grader', event, 'log.grading_fallback', data)
        } else {
          addLog('grader', event, 'log.grading', { passed: data.passed, total: data.passed + data.failed })
        }
        break

      case 'web_search_complete':
        updateNode('web_search', 'completed', { count: data.count })
        addLog('web_search', event, 'log.web_found', { count: data.count })
        break

      case 'generation_complete':
        updateNode('generator', 'completed')
        addLog('generator', event, 'log.generated')
        break

      case 'retry':
        addLog(node, event, 'log.retry', { attempt: data.attempt, reason: data.reason })
        break

      case 'hallucination_check':
        updateNode('hallucination_checker', data.grounded ? 'completed' : 'error',
          { grounded: data.grounded })
        addLog('hallucination_checker', event,
          data.grounded ? 'log.hallucination_pass' : 'log.hallucination_fail')
        break

      case 'relevance_check':
        updateNode('relevance_checker', data.useful ? 'completed' : 'error',
          { useful: data.useful })
        addLog('relevance_checker', event,
          data.useful ? 'log.relevance_pass' : 'log.relevance_fail')
        break

      case 'research_complete':
        updateNode('report_builder', 'completed')
        report.value = { content: data.report, sources: data.sources }
        addLog('report_builder', event, 'log.report_done')
        break

      case 'error':
        error.value = data.message
        addLog('system', event, data.message)
        break

      case 'timeout':
        error.value = 'Research timed out'
        addLog('system', event, 'Research timed out')
        break
    }
  }

  async function startResearch(question: string, lang: string) {
    // Reset state
    resetAll()
    logs.value = []
    report.value = null
    error.value = null
    logCounter = 0
    isResearching.value = true

    abortController = new AbortController()

    const config = useRuntimeConfig()
    const url = `${config.public.apiBase}/api/research?q=${encodeURIComponent(question)}&lang=${lang}`

    try {
      const response = await fetch(url, {
        signal: abortController.signal,
        headers: { 'Accept': 'text/event-stream' },
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error || `HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      resetDisconnectTimer()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              handleEvent(data)
            } catch {
              // Skip malformed lines
            }
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        error.value = e.message
      }
    } finally {
      isResearching.value = false
      if (disconnectTimer) clearTimeout(disconnectTimer)
    }
  }

  function abort() {
    abortController?.abort()
    isResearching.value = false
  }

  return { isResearching, logs, report, error, startResearch, abort }
}
