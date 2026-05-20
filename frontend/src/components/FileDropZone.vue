<script setup lang="ts">
import { ref } from "vue"
import { useProjectStore } from "@/stores/project"
import { classifyApi, streamClassify } from "@/api"

const emit = defineEmits<{ processed: [] }>()
const store = useProjectStore()

const isOver = ref(false)
const uploading = ref(false)
const msg = ref("")
const err = ref("")
const pasteText = ref("")
const fileInput = ref<HTMLInputElement | null>(null)

// Streaming progress
const streaming = ref(false)
const streamStatus = ref("")
const streamEntries = ref<{ idx: number; total: number; content: string; file: string; isNew: boolean }[]>([])
const streamDone = ref(false)
let abortCtrl: AbortController | null = null

function cancelStream() {
  abortCtrl?.abort()
  streaming.value = false
  streamStatus.value = "已取消"
  uploading.value = false
}

function onDragEnter(e: DragEvent) { e.preventDefault(); e.stopPropagation(); isOver.value = true }
function onDragOver(e: DragEvent) { e.preventDefault(); e.stopPropagation() }
function onDragLeave(e: DragEvent) { e.preventDefault(); e.stopPropagation(); isOver.value = false }

async function onDrop(e: DragEvent) {
  e.preventDefault(); e.stopPropagation(); isOver.value = false
  if (!store.currentProject) { err.value = "请先创建或选择一个项目"; return }
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    // Read file content and stream
    const text = await files[0].text()
    doStream(text)
  }
}

function onBtnClick() { fileInput.value?.click() }

async function onFilesPicked(e: Event) {
  const t = e.target as HTMLInputElement
  if (!t.files || t.files.length === 0) return
  if (!store.currentProject) { err.value = "请先创建项目"; return }
  const text = await t.files[0].text()
  t.value = ""
  doStream(text)
}

function doStream(text: string) {
  if (!text.trim() || !store.currentProject) return
  uploading.value = true; streaming.value = true; err.value = ""; msg.value = ""
  streamEntries.value = []; streamDone.value = false; streamStatus.value = ""

  abortCtrl = streamClassify(
    store.currentProject.id,
    text,
    // onEntry
    (data) => {
      streamEntries.value.push({
        idx: data.idx, total: data.total,
        content: data.content, file: data.file, isNew: data.isNew,
      })
    },
    // onDone
    async (data) => {
      streaming.value = false; streamDone.value = true; uploading.value = false
      const total = data.total || 0
      const assigned = data.assigned || 0
      const news = data.new || 0
      msg.value = `${total} 条 → ${assigned} 已有 + ${news} 新建`
      await store.refreshFiles()
      if (store.currentFile) await store.refreshEntries()
      emit("processed")
      setTimeout(() => {
        msg.value = ""; streamEntries.value = []; streamDone.value = false
      }, 10000)
    },
    // onError
    (e) => {
      streaming.value = false; uploading.value = false; err.value = e
    },
    // onStatus
    (s) => { streamStatus.value = s },
  )
}

function submitPaste() {
  doStream(pasteText.value)
  pasteText.value = ""
}
</script>

<template>
  <div class="section">
    <!-- Drop zone -->
    <div :class="['drop', { on: isOver, busy: uploading }]"
      @dragenter="onDragEnter" @dragover="onDragOver" @dragleave="onDragLeave" @drop="onDrop">
      <input ref="fileInput" type="file" accept=".txt,.md,.markdown" class="hidden" @change="onFilesPicked" />

      <template v-if="uploading && !streaming">
        <div class="spinner"></div><div class="title">处理中...</div>
      </template>
      <template v-else-if="streaming">
        <div class="spinner"></div>
        <div class="title">{{ streamStatus || 'AI 分析中...' }}</div>
        <div class="hint">{{ streamEntries.length }} 条已完成</div>
        <button class="btn btn-danger" @click.stop="cancelStream" style="margin-top:8px">取消</button>
      </template>
      <template v-else-if="isOver">
        <div class="icon">📥</div><div class="title">松开上传</div>
      </template>
      <template v-else>
        <div class="icon">📁</div>
        <div class="title">拖入文件或点击选择</div>
        <div class="hint">支持 TXT / Markdown</div>
        <button class="btn btn-primary" @click.stop="onBtnClick" style="margin-top:8px">选择文件</button>
      </template>
    </div>

    <!-- Live stream results -->
    <div v-if="streamEntries.length > 0" class="live-box">
      <div class="live-head">
        <span v-if="streaming" class="live-badge pulse">● 实时生成中</span>
        <span v-else class="live-badge done">✓ 完成</span>
        <span class="live-count">{{ streamEntries.length }} 条</span>
      </div>
      <div class="live-list">
        <div v-for="s in streamEntries" :key="s.idx" class="live-item">
          <span class="li-idx">{{ s.idx }}/{{ s.total }}</span>
          <span class="li-content">{{ s.content }}</span>
          <span :class="['li-file', s.isNew ? 'new' : '']">{{ s.isNew ? '＋' : '→' }} {{ s.file }}</span>
        </div>
      </div>
    </div>

    <!-- Paste area -->
    <div class="paste">
      <textarea v-model="pasteText" placeholder="或粘贴文本..." rows="4"></textarea>
      <div class="paste-foot">
        <button class="btn btn-primary" :disabled="uploading || !pasteText.trim()" @click="submitPaste">
          {{ uploading ? '分析中...' : '智能划分' }}
        </button>
      </div>
    </div>

    <div v-if="msg" class="note ok">{{ msg }}</div>
    <div v-if="err" class="note bad">{{ err }}</div>
  </div>
</template>

<style scoped>
.section { flex-shrink: 0; }
.hidden { display: none; }

.drop {
  border: 2px dashed #d1d5db; border-radius: 10px;
  padding: 16px; text-align: center; background: #fff; transition: all .2s; cursor: pointer;
}
.drop:hover { border-color: #4f6ef6; background: #f8faff; }
.drop.on { border-color: #4f6ef6; background: #eef1ff; border-style: solid; }
.drop.busy { cursor: wait; }

.icon { font-size: 28px; margin-bottom: 4px; }
.title { font-size: 13px; font-weight: 600; color: #1a1d28; }
.hint { font-size: 11px; color: #9ca3af; margin-top: 2px; }

.spinner {
  width: 24px; height: 24px; border: 3px solid #e5e7eb;
  border-top-color: #4f6ef6; border-radius: 50%; animation: s .7s linear infinite; margin: 0 auto 8px;
}
@keyframes s { to { transform: rotate(360deg); } }

/* Live stream results */
.live-box {
  margin-top: 8px; background: #fff; border: 1px solid #e8ecf1; border-radius: 10px;
  max-height: 240px; overflow-y: auto;
}
.live-head {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; border-bottom: 1px solid #f3f4f6; position: sticky; top: 0; background: #fff;
}
.live-badge { font-size: 11px; font-weight: 700; }
.live-badge.pulse { color: #4f6ef6; animation: pulse 1.5s infinite; }
.live-badge.done { color: #10b981; }
@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: .3 } }
.live-count { font-size: 11px; color: #9ca3af; margin-left: auto; }

.live-list { padding: 4px 8px; }
.live-item {
  display: flex; align-items: center; gap: 8px; padding: 6px 8px;
  font-size: 12px; border-bottom: 1px solid #f9fafb; animation: fadeIn .3s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(-4px) } to { opacity: 1; transform: translateY(0) } }
.li-idx { color: #9ca3af; font-weight: 600; min-width: 36px; }
.li-content { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #374151; }
.li-file { font-size: 11px; color: #6b7280; flex-shrink: 0; font-weight: 500; }
.li-file.new { color: #10b981; }

/* Paste */
.paste {
  margin-top: 8px; background: #fff; border: 1px solid #e8ecf1; border-radius: 10px; padding: 8px 10px;
}
.paste textarea {
  width: 100%; resize: vertical; min-height: 60px; max-height: 100px;
  border: none; outline: none; font-size: 13px; line-height: 1.6; font-family: inherit; background: transparent;
}
.paste-foot { display: flex; justify-content: flex-end; margin-top: 6px; }

.note { margin-top: 8px; padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: 500; }
.ok { background: #ecfdf5; color: #059669; }
.bad { background: #fef2f2; color: #dc2626; }

.btn { font-size: 12px; font-weight: 600; padding: 6px 16px; border-radius: 8px; border: none; cursor: pointer; transition: all .15s; }
.btn:active { transform: scale(.97); }
.btn-primary { background: #4f6ef6; color: #fff; }
.btn-primary:hover { filter: brightness(1.08); }
.btn-primary:disabled { opacity: .4; cursor: not-allowed; }
.btn-danger { background: #ef4444; color: #fff; }
.btn-danger:hover { filter: brightness(1.08); }
</style>
