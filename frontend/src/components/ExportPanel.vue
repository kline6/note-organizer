<script setup lang="ts">
import { ref } from "vue"
import { useProjectStore } from "@/stores/project"
import { exportApi } from "@/api"

const store = useProjectStore()
const exporting = ref(false)
const msg = ref<{ text: string; ok: boolean } | null>(null)

const formats = [
  { key: "md", label: "Markdown", icon: "📝", desc: "保留高亮，适合二次编辑" },
  { key: "html", label: "HTML", icon: "🌐", desc: "保留颜色和样式，浏览器查看" },
  { key: "txt", label: "纯文本", icon: "📄", desc: "去除格式，纯文本导出" },
  { key: "docx", label: "Word", icon: "📘", desc: "可编辑的 Word 文档" },
  { key: "pdf", label: "PDF", icon: "📕", desc: "保留排版，打印分享" },
]

async function doExport(fn: () => Promise<void>) {
  exporting.value = true
  msg.value = null
  try {
    await fn()
    msg.value = { text: "导出成功", ok: true }
  } catch (e: any) {
    let detail = e.message || "未知错误"
    // Blob responses need text extraction for error detail
    if (e.response?.data instanceof Blob) {
      try { const t = await e.response.data.text(); const j = JSON.parse(t); detail = j.detail || t } catch {}
    } else if (e.response?.data?.detail) {
      detail = e.response.data.detail
    }
    msg.value = { text: "导出失败: " + detail, ok: false }
  } finally {
    exporting.value = false
    setTimeout(() => { msg.value = null }, 6000)
  }
}
</script>

<template>
  <div class="export">
    <div class="card">
      <h3>导出整个项目</h3>
      <p class="desc">将当前项目中所有文件导出为指定格式</p>
      <div class="fmt-grid">
        <button
          v-for="f in formats" :key="'all-' + f.key"
          class="fmt-btn" :disabled="exporting"
          @click="doExport(() => exportApi.exportAll(store.currentProject!.id, f.key))"
        >
          <span class="fmt-icon">{{ f.icon }}</span>
          <span class="fmt-label">{{ f.label }}</span>
          <span class="fmt-desc">{{ f.desc }}</span>
        </button>
      </div>
    </div>

    <div class="card">
      <h3>导出当前文件</h3>
      <p class="desc" v-if="store.currentFile">{{ store.currentFile.filename }}</p>
      <p class="desc" v-else>请先在左侧选择一个文件</p>
      <div class="fmt-grid">
        <button
          v-for="f in formats" :key="'s-' + f.key"
          class="fmt-btn" :disabled="exporting || !store.currentFile"
          @click="doExport(() => exportApi.exportSingle(store.currentFile!.id, f.key))"
        >
          <span class="fmt-icon">{{ f.icon }}</span>
          <span class="fmt-label">{{ f.label }}</span>
          <span class="fmt-desc">{{ f.desc }}</span>
        </button>
      </div>
    </div>

    <div v-if="msg" :class="['result', msg.ok ? 'ok' : 'err']">{{ msg.text }}</div>
  </div>
</template>

<style scoped>
.export { max-width: 800px; display: flex; flex-direction: column; gap: 20px; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}

.card h3 { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
.desc { font-size: 13px; color: var(--text-muted); margin-bottom: 14px; }

.fmt-grid { display: flex; gap: 10px; flex-wrap: wrap; }

.fmt-btn {
  flex: 0 0 calc(20% - 8px);
  min-width: 100px;
  padding: 16px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg);
  text-align: center;
  cursor: pointer;
  transition: all var(--transition);
}

.fmt-btn:hover:not(:disabled) { border-color: var(--primary); background: var(--primary-bg); }
.fmt-btn:disabled { opacity: .4; cursor: not-allowed; }

.fmt-icon { display: block; font-size: 28px; margin-bottom: 6px; }
.fmt-label { display: block; font-size: 14px; font-weight: 700; margin-bottom: 2px; }
.fmt-desc { display: block; font-size: 11px; color: var(--text-muted); }

.result { padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 500; }
.ok { background: var(--success-light); color: var(--success); }
.err { background: var(--danger-light); color: var(--danger); }
</style>
