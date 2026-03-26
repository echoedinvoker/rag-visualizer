<script setup lang="ts">
import {
  UploadOutlined,
  DeleteOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue'

const { t } = useI18n()
const { files, isUploading, uploadFile, deleteFile, ensureSession } = useSession()

const uploadError = ref<string | null>(null)

async function handleUpload(info: any) {
  const file = info.file as File
  uploadError.value = null
  try {
    await uploadFile(file)
  } catch (e: any) {
    uploadError.value = e.message
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(() => {
  ensureSession()
})
</script>

<template>
  <div class="file-upload">
    <div class="upload-title">{{ t('upload.title') }}</div>

    <a-upload
      :before-upload="() => false"
      :show-upload-list="false"
      accept=".pdf,.txt,.md"
      @change="handleUpload"
    >
      <a-button size="small" :loading="isUploading" :disabled="isUploading">
        <template #icon><UploadOutlined /></template>
        {{ t('upload.button') }}
      </a-button>
    </a-upload>

    <a-alert
      v-if="uploadError"
      type="error"
      :message="uploadError"
      show-icon
      closable
      style="margin-top: 8px; font-size: 12px"
      @close="uploadError = null"
    />

    <div v-if="files.length > 0" class="file-list">
      <div v-for="file in files" :key="file.id" class="file-item">
        <FileTextOutlined class="file-icon" />
        <div class="file-info">
          <div class="file-name">{{ file.name }}</div>
          <div class="file-meta">{{ formatSize(file.size) }} · {{ file.chunks }} chunks</div>
        </div>
        <a-button type="text" size="small" danger @click="deleteFile(file.id)">
          <template #icon><DeleteOutlined /></template>
        </a-button>
      </div>
    </div>

    <div v-else class="no-files">
      {{ t('upload.no_files') }}
    </div>
  </div>
</template>

<style scoped>
.file-upload {
  padding: var(--space-2) 0;
}

.upload-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: var(--space-2);
}

.file-list {
  margin-top: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border-radius: var(--radius-sm);
  background: var(--color-bg-well);
}

.file-icon {
  color: var(--primary);
  font-size: 14px;
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--slate-700);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 10px;
  color: var(--color-text-muted);
}

.no-files {
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-3) 0;
}
</style>
