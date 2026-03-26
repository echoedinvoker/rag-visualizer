import { ref } from 'vue'
import type { NodeStatus } from '~/types/graph'
import type { LogEntry, GraphConfig } from '~/types/graph'

export function useGraphExecution(
  updateNode: (id: string, status: NodeStatus, details?: Record<string, any>) => void,
  resetAll: () => void,
) {
  const isRunning = ref(false)
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
      if (isRunning.value) {
        error.value = 'Connection lost'
        isRunning.value = false
      }
    }, 35_000)
  }

  function handleEvent(data: Record<string, any>) {
    resetDisconnectTimer()
    const event = data.event as string
    const node = data.node as string

    switch (event) {
      case 'graph_start':
        addLog('system', event, 'log.graph_started', { node_count: data.node_count })
        break

      case 'node_start':
        updateNode(node, 'running')
        break

      case 'route_decision':
        updateNode(node, 'completed', { decision: data.decision })
        addLog(node, event,
          data.decision === 'vector_store' ? 'log.routing_vector' : 'log.routing_web',
          data)
        break

      case 'documents_retrieved':
        updateNode(node, 'completed', { count: data.count })
        addLog(node, event, 'log.retrieving', { count: data.count, sources: data.sources })
        break

      case 'doc_graded':
        addLog(node, event, `${data.doc_id}: ${data.relevant ? '✓' : '✗'}`, data)
        break

      case 'grading_summary':
        updateNode(node, 'completed', { passed: data.passed, failed: data.failed })
        if (data.fallback) {
          addLog(node, event, 'log.grading_fallback', data)
        } else {
          addLog(node, event, 'log.grading', { passed: data.passed, total: data.passed + data.failed })
        }
        break

      case 'web_search_complete':
        updateNode(node, 'completed', { count: data.count })
        addLog(node, event, 'log.web_found', { count: data.count })
        break

      case 'generation_complete':
        updateNode(node, 'completed')
        addLog(node, event, 'log.generated')
        break

      case 'retry':
        addLog(node, event, 'log.retry', { attempt: data.attempt, reason: data.reason })
        break

      case 'hallucination_check':
        updateNode(node, data.grounded ? 'completed' : 'error', { grounded: data.grounded })
        addLog(node, event,
          data.grounded ? 'log.hallucination_pass' : 'log.hallucination_fail')
        break

      case 'relevance_check':
        updateNode(node, data.useful ? 'completed' : 'error', { useful: data.useful })
        addLog(node, event,
          data.useful ? 'log.relevance_pass' : 'log.relevance_fail')
        break

      case 'summary_complete':
        updateNode(node, 'completed')
        addLog(node, event, 'log.summary_done')
        break

      case 'query_rewritten':
        updateNode(node, 'completed', { rewritten: data.rewritten })
        addLog(node, event, 'log.query_rewritten', { original: data.original, rewritten: data.rewritten })
        break

      case 'research_complete':
        updateNode(node, 'completed')
        report.value = { content: data.report, sources: data.sources }
        addLog(node, event, 'log.report_done')
        break

      case 'graph_complete':
        addLog('system', event, 'log.graph_complete', { duration_ms: data.total_duration_ms })
        break

      case 'graph_error':
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

  async function runPipeline(config: GraphConfig, question: string, lang: string) {
    // Reset state
    resetAll()
    logs.value = []
    report.value = null
    error.value = null
    logCounter = 0
    isRunning.value = true

    abortController = new AbortController()

    const runtimeConfig = useRuntimeConfig()
    const url = `${runtimeConfig.public.apiBase}/api/graph/run`

    try {
      const response = await fetch(url, {
        method: 'POST',
        signal: abortController.signal,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ config, question, language: lang }),
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
        buffer = lines.pop() || ''

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
      isRunning.value = false
      if (disconnectTimer) clearTimeout(disconnectTimer)
    }
  }

  function abort() {
    abortController?.abort()
    isRunning.value = false
  }

  return { isRunning, logs, report, error, runPipeline, abort }
}
