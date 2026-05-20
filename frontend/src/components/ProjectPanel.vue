<script setup lang="ts">
import { ref } from "vue"
import { useProjectStore } from "@/stores/project"
import type { NoteFile } from "@/types"

const store = useProjectStore()
const name = ref("")
const loading = ref(false)
const error = ref("")

async function doCreate() {
  const n = name.value.trim()
  if (!n) return
  loading.value = true
  error.value = ""
  try {
    const p = await store.createProject(n)
    name.value = ""
    await store.selectProject(p.id)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    error.value = detail || e.message || "创建失败 - 请确认后端服务已启动"
    setTimeout(() => { error.value = "" }, 5000)
  } finally {
    loading.value = false
  }
}

function doSelectProject(id: string) {
  error.value = ""
  store.selectProject(id)
}

function doSelectFile(f: NoteFile) {
  store.selectFile(f)
}
</script>

<template>
  <div class="panel">
    <!-- Create -->
    <form class="create" @submit.prevent="doCreate">
      <input
        v-model="name"
        placeholder="输入项目名称，回车创建"
        :disabled="loading"
      />
      <button type="submit" class="btn-add" :disabled="loading || !name.trim()">
        {{ loading ? "..." : "创建" }}
      </button>
    </form>
    <div v-if="error" class="err">{{ error }}</div>

    <!-- Projects -->
    <div class="sec">
      <div class="sec-label">项目列表</div>
      <div class="sec-list">
        <div
          v-for="p in store.projects" :key="p.id"
          :class="['row', { sel: store.currentProject?.id === p.id }]"
          @click="doSelectProject(p.id)"
        >
          <span class="r-icon">📁</span>
          <span class="r-name">{{ p.name }}</span>
        </div>
        <div v-if="store.projects.length === 0" class="empty">暂无项目</div>
      </div>
    </div>

    <!-- Files -->
    <div v-if="store.currentProject" class="sec fill">
      <div class="sec-label">
        文件 <em>{{ store.files.length }}</em>
      </div>
      <div class="sec-list">
        <div
          v-for="f in store.files" :key="f.id"
          :class="['row', { sel: store.currentFile?.id === f.id }]"
          @click="doSelectFile(f)"
        >
          <span class="r-icon">{{ f.created_by_ai ? '🤖' : '📄' }}</span>
          <div class="r-info">
            <span class="r-name">{{ f.filename }}</span>
            <span class="r-meta">{{ f.entry_count }} 条 · {{ f.keywords || '无标签' }}</span>
          </div>
        </div>
        <div v-if="store.files.length === 0" class="empty">拖入文件开始</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; flex: 1; overflow: hidden; }

/* Create */
.create {
  display: flex; gap: 6px;
  padding: 12px 14px; border-bottom: 1px solid var(--border);
}
.create input { flex: 1; padding: 8px 10px; font-size: 13px; }
.btn-add {
  background: var(--primary); color: #fff; font-weight: 700;
  padding: 8px 18px; border: none; border-radius: 8px; font-size: 13px;
  cursor: pointer; white-space: nowrap;
}
.btn-add:hover { filter: brightness(1.08); }
.btn-add:disabled { opacity: .4; cursor: not-allowed; }

.err {
  margin: 0 14px; padding: 8px 12px; background: #fef2f2; color: #dc2626;
  border-radius: 8px; font-size: 12px; font-weight: 500;
}

/* Section */
.sec { border-bottom: 1px solid var(--border); display: flex; flex-direction: column; overflow: hidden; }
.sec.fill { flex: 1; border-bottom: none; }

.sec-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .4px;
  color: #9ca3af; padding: 10px 14px 4px; display: flex; align-items: center; gap: 6px;
  flex-shrink: 0;
}
.sec-label em { font-style: normal; background: #eef1ff; color: var(--primary); padding: 1px 7px; border-radius: 10px; font-size: 10px; }

.sec-list { flex: 1; overflow-y: auto; padding: 0 6px 6px; }

.row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 8px; cursor: pointer; transition: background .12s;
}
.row:hover { background: #f3f4f6; }
.row.sel { background: #eef1ff; }

.r-icon { font-size: 16px; flex-shrink: 0; }
.r-name { font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.r-info { flex: 1; overflow: hidden; }
.r-meta { font-size: 11px; color: #9ca3af; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.empty { padding: 20px; text-align: center; font-size: 12px; color: #9ca3af; }
</style>
