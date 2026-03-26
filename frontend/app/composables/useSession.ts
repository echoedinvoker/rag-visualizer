import { ref } from 'vue'

interface SessionFile {
  id: string
  name: string
  size: number
  chunks: number
}

const sessionId = ref<string | null>(null)
const collectionName = ref<string | null>(null)
const files = ref<SessionFile[]>([])
const isUploading = ref(false)

let initialized = false

export function useSession() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  async function ensureSession() {
    if (sessionId.value) return
    if (initialized) return
    initialized = true

    try {
      const res = await $fetch<{ session_id: string; collection_name: string }>(`${apiBase}/api/session`, {
        method: 'POST',
      })
      sessionId.value = res.session_id
      collectionName.value = res.collection_name
    } catch {
      initialized = false
    }
  }

  async function uploadFile(file: File): Promise<SessionFile | null> {
    await ensureSession()
    if (!sessionId.value) return null

    isUploading.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await $fetch<{ file: SessionFile; collection_name: string }>(
        `${apiBase}/api/session/${sessionId.value}/upload`,
        { method: 'POST', body: formData },
      )
      files.value.push(res.file)
      return res.file
    } catch (e: any) {
      throw new Error(e.data?.error || e.message || 'Upload failed')
    } finally {
      isUploading.value = false
    }
  }

  async function deleteFile(fileId: string) {
    if (!sessionId.value) return
    await $fetch(`${apiBase}/api/session/${sessionId.value}/files/${fileId}`, {
      method: 'DELETE',
    })
    files.value = files.value.filter(f => f.id !== fileId)
  }

  async function refreshFiles() {
    if (!sessionId.value) return
    const res = await $fetch<{ files: SessionFile[] }>(
      `${apiBase}/api/session/${sessionId.value}/files`,
    )
    files.value = res.files
  }

  return {
    sessionId,
    collectionName,
    files,
    isUploading,
    ensureSession,
    uploadFile,
    deleteFile,
    refreshFiles,
  }
}
