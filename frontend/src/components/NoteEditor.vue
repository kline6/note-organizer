<script setup lang="ts">
import { computed } from "vue"
import { useProjectStore } from "@/stores/project"
import { classifyApi } from "@/api"
import type { NoteEntry } from "@/types"

const store = useProjectStore()

const sorted = computed(() => [...store.entries].sort((a, b) => a.sort_order - b.sort_order))

function onDragStart(e: DragEvent, entry: NoteEntry) {
  if (e.dataTransfer) { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", entry.id) }
}
function onDropOver(e: DragEvent) { e.preventDefault() }

async function onFileDrop(e: DragEvent, targetId: string) {
  e.preventDefault(); const id = e.dataTransfer?.getData("text/plain")
  if (id) { try { await store.moveEntry(id, targetId) } catch {} }
}
async function onNewDrop(e: DragEvent) {
  e.preventDefault(); const id = e.dataTransfer?.getData("text/plain")
  if (!id || !store.currentProject) return
  const name = prompt("新文件名称："); if (!name) return
  const fn = name.endsWith(".txt") ? name : name + ".txt"
  try {
    await classifyApi.uploadExisting(store.currentProject.id, [new File([new Blob(["\n"])], fn)])
    await store.refreshFiles(); const f = store.files.find(x => x.filename === fn)
    if (f) await store.moveEntry(id, f.id)
  } catch {}
}

function bColor(c: string | null) {
  const m: Record<string, string> = { red: "#fca5a5", blue: "#93c5fd", green: "#86efac", yellow: "#fde047", orange: "#fdba74", purple: "#c4b5fd" }
  return m[c || ""] || "#e5e7eb"
}
function bBg(c: string | null) {
  const m: Record<string, string> = { red: "#fef2f2", blue: "#eff6ff", green: "#f0fdf4", yellow: "#fefce8", orange: "#fff7ed", purple: "#faf5ff" }
  return m[c || ""] || "#fff"
}
</script>

<template>
  <div class="editor">
    <!-- File header -->
    <div v-if="store.currentFile" class="head">
      <div class="head-row">
        <h3>{{ store.currentFile.filename }} <span v-if="store.currentFile.created_by_ai" class="ai">AI</span></h3>
        <span class="cnt">{{ store.entries.length }} 条</span>
      </div>
      <div v-if="store.currentFile.keywords" class="kws">
        <span v-for="k in store.currentFile.keywords.split(',')" :key="k" class="kw">{{ k.trim() }}</span>
      </div>
      <p v-if="store.currentFile.summary" class="sum">{{ store.currentFile.summary }}</p>
    </div>

    <!-- Empty -->
    <div v-if="!store.currentFile" class="empty">
      <span style="font-size:48px">📂</span><p style="margin-top:12px">选择文件查看内容</p>
      <div class="dh" @dragover="onDropOver" @drop="onNewDrop">拖条目到此处创建新文件</div>
    </div>
    <div v-else-if="sorted.length === 0" class="empty">
      <span style="font-size:48px">📝</span><p style="margin-top:12px">该文件暂无条目</p>
    </div>

    <!-- Cards -->
    <div v-else class="cards">
      <div v-for="e in sorted" :key="e.id"
        :class="['card', e.importance === 'high' ? 'c-hi' : '']"
        :style="{ borderLeftColor: bColor(e.color), background: bBg(e.color) }"
        draggable="true" @dragstart="onDragStart($event, e)">
        <div class="card-bar">
          <span class="grip">⠿</span>
          <span v-if="e.importance === 'high'" class="tag t-red">重要</span>
          <span v-if="e.similarity_score" class="tag t-warn">⚠ 相似</span>
          <button class="x" @click="store.deleteEntry(e.id)">×</button>
        </div>
        <div class="card-text" v-html="e.highlighted_content || e.content"></div>
        <div v-if="e.linked_entry_id" class="card-link">🔗 关联内容</div>
      </div>
    </div>

    <!-- Targets -->
    <div v-if="store.currentFile" class="bar">
      <span class="lbl">移到：</span>
      <div v-for="f in store.files.filter(x => x.id !== store.currentFile?.id)" :key="f.id"
        class="chip" @dragover="onDropOver" @drop="onFileDrop($event, f.id)">📄 {{ f.filename }}</div>
      <div class="chip ch-new" @dragover="onDropOver" @drop="onNewDrop">＋ 新文件</div>
    </div>
  </div>
</template>

<style scoped>
.editor { display: flex; flex-direction: column; flex: 1; overflow: hidden; min-height: 0; padding: 12px 20px; }

/* Head */
.head {
  background: #fff; border: 1px solid #e8ecf1; border-radius: 10px;
  padding: 14px 18px; flex-shrink: 0; margin-bottom: 10px;
}
.head-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.head-row h3 { font-size: 15px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.ai { font-size: 10px; background: #eef1ff; color: #4f6ef6; padding: 2px 7px; border-radius: 10px; font-weight: 700; }
.cnt { font-size: 12px; color: #9ca3af; }
.kws { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 4px; }
.kw { font-size: 11px; background: #f3f4f6; color: #6b7280; padding: 3px 9px; border-radius: 10px; font-weight: 500; }
.sum { font-size: 13px; color: #6b7280; line-height: 1.5; }

/* Empty */
.empty {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; color: #9ca3af; font-size: 14px;
}
.dh { margin-top: 12px; padding: 12px 28px; border: 2px dashed #d1d5db; border-radius: 10px; font-size: 12px; cursor: pointer; color: #9ca3af; }
.dh:hover { border-color: #10b981; color: #10b981; background: #ecfdf5; }

/* Cards */
.cards { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-bottom: 4px; }

.card {
  border: 1px solid #e8ecf1; border-left-width: 4px;
  border-radius: 10px; padding: 16px 20px;
  cursor: grab; transition: all .15s; background: #fff;
}
.card:hover { box-shadow: 0 2px 10px rgba(0,0,0,.05); }
.card:active { cursor: grabbing; }

.card-bar { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
.grip { color: #d1d5db; font-size: 15px; cursor: grab; user-select: none; }
.tag { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 6px; }
.t-red { background: #fef2f2; color: #dc2626; }
.t-warn { background: #fffbeb; color: #d97706; }
.x { margin-left: auto; background: none; font-size: 18px; color: #d1d5db; padding: 0 6px; border: none; border-radius: 4px; cursor: pointer; }
.x:hover { background: #fef2f2; color: #dc2626; }

.card-text {
  font-size: 15px; line-height: 2; white-space: pre-wrap; word-break: break-word;
}

/* Make highlight spans bigger */
.card-text :deep(.hl-red), .card-text :deep(.hl-blue), .card-text :deep(.hl-green),
.card-text :deep(.hl-orange), .card-text :deep(.hl-yellow), .card-text :deep(.hl-purple),
.card-text :deep(.hl-bold) {
  font-size: 15px; padding: 1px 5px; border-radius: 3px;
}
.card-text :deep(strong) { font-size: 15px; }

.card-link { font-size: 12px; color: #4f6ef6; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e8ecf1; }

/* Bottom bar */
.bar {
  background: #fff; border: 1px solid #e8ecf1; border-radius: 10px;
  padding: 10px 14px; display: flex; align-items: center; gap: 8px;
  flex-shrink: 0; flex-wrap: wrap; margin-top: 8px;
}
.lbl { font-size: 12px; font-weight: 600; color: #6b7280; flex-shrink: 0; }
.chip { padding: 5px 12px; border: 1px dashed #d1d5db; border-radius: 16px; font-size: 12px; color: #6b7280; cursor: pointer; transition: all .15s; }
.chip:hover { border-color: #4f6ef6; color: #4f6ef6; background: #eef1ff; border-style: solid; }
.ch-new { border-style: solid; color: #10b981; border-color: #86efac; background: #ecfdf5; }
.ch-new:hover { background: #d1fae5; }
</style>
