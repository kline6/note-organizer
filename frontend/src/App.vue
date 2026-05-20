<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue"
import { useProjectStore } from "@/stores/project"
import ProjectPanel from "@/components/ProjectPanel.vue"
import WorkspaceView from "@/views/WorkspaceView.vue"
import SettingsPanel from "@/components/SettingsPanel.vue"

const store = useProjectStore()
const showSettings = ref(false)

// Global: prevent browser from opening dropped files
function blockDrag(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
}

onMounted(() => {
  store.loadProjects()
  document.addEventListener("dragover", blockDrag, false)
  document.addEventListener("drop", blockDrag, false)
})

onUnmounted(() => {
  document.removeEventListener("dragover", blockDrag, false)
  document.removeEventListener("drop", blockDrag, false)
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-icon">📋</span>
        <span class="brand-text">NoteFlow</span>
      </div>
      <ProjectPanel />
      <div class="sidebar-bottom">
        <button class="btn-sidebar" @click="showSettings = true">
          <span class="btn-icon">⚙</span>
          <span>API 设置</span>
        </button>
      </div>
    </aside>
    <main class="main-area">
      <WorkspaceView v-if="store.currentProject" />
      <div v-else class="welcome-screen">
        <div class="welcome-card">
          <div class="welcome-icon">📋</div>
          <h1>NoteFlow 笔记智能整理</h1>
          <p class="welcome-sub">拖入总结笔记，AI 自动拆解归类，智能标注美化</p>
          <div class="feature-grid">
            <div class="feature-item">
              <span class="feat-icon">🤖</span>
              <div>
                <strong>AI 智能拆分</strong>
                <p>自动分析每段内容，分配到最匹配的分类文件</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="feat-icon">🏷</span>
              <div>
                <strong>关键词标签</strong>
                <p>自动提取 3-5 个关键词，一键搜索定位</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="feat-icon">🎨</span>
              <div>
                <strong>颜色高亮</strong>
                <p>紧急红色、待办蓝色、完成绿色，一目了然</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="feat-icon">📦</span>
              <div>
                <strong>多格式导出</strong>
                <p>MD / HTML / Word / PDF，保留颜色标注</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="feat-icon">↩</span>
              <div>
                <strong>撤销回退</strong>
                <p>自动保存快照，一键恢复到任意历史版本</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="feat-icon">📐</span>
              <div>
                <strong>自定义规则</strong>
                <p>设置关键词规则，AI 优先按你的规则分类</p>
              </div>
            </div>
          </div>
          <p class="welcome-hint">← 在左侧创建一个项目开始使用</p>
        </div>
      </div>
    </main>
    <SettingsPanel v-if="showSettings" @close="showSettings = false" />
  </div>
</template>

<style>
/* ── Reset & Variables ───────────── */
*,
*::before,
*::after { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #f5f6fa;
  --surface: #ffffff;
  --border: #e8ecf1;
  --text: #1a1d28;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
  --primary: #4f6ef6;
  --primary-light: #eef1ff;
  --primary-bg: #f0f3ff;
  --danger: #ef4444;
  --danger-light: #fef2f2;
  --success: #10b981;
  --success-light: #ecfdf5;
  --warning: #f59e0b;
  --warning-light: #fffbeb;
  --orange: #f97316;
  --purple: #8b5cf6;
  --radius: 10px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,.04);
  --shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,.05), 0 2px 4px rgba(0,0,0,.04);
  --shadow-lg: 0 10px 15px rgba(0,0,0,.06), 0 4px 6px rgba(0,0,0,.04);
  --transition: 150ms ease;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", "Helvetica Neue", sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

#app { height: 100vh; }

/* ── Layout ──────────────────────── */
.app-shell {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 280px;
  min-width: 280px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
}

.brand-icon { font-size: 22px; }
.brand-text { font-size: 17px; font-weight: 700; color: var(--text); letter-spacing: -0.3px; }

.sidebar-bottom {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.btn-sidebar {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.btn-sidebar:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
  color: var(--primary);
}

.btn-sidebar .btn-icon { font-size: 16px; }

.main-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ── Welcome ─────────────────────── */
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.welcome-card {
  text-align: center;
  max-width: 680px;
}

.welcome-icon { font-size: 56px; margin-bottom: 16px; }

.welcome-card h1 {
  font-size: 26px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.welcome-sub {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 36px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-bottom: 32px;
  text-align: left;
}

.feature-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: all var(--transition);
}

.feature-item:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow);
}

.feat-icon { font-size: 24px; flex-shrink: 0; margin-top: 2px; }
.feature-item strong { display: block; font-size: 14px; margin-bottom: 2px; }
.feature-item p { font-size: 12px; color: var(--text-muted); line-height: 1.5; }

.welcome-hint {
  font-size: 13px;
  color: var(--text-muted);
  padding: 10px 20px;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  display: inline-block;
}

/* ── Shared components ───────────── */
button {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  transition: all var(--transition);
  outline: none;
}

button:active { transform: scale(0.97); }

.btn-primary {
  background: var(--primary);
  color: #fff;
  font-weight: 600;
  padding: 8px 18px;
}

.btn-primary:hover { filter: brightness(1.08); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-danger {
  background: var(--danger);
  color: #fff;
  font-weight: 600;
  padding: 8px 18px;
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  padding: 8px 14px;
}

.btn-ghost:hover { background: var(--bg); }

input, textarea, select {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 12px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: all var(--transition);
  background: var(--surface);
  color: var(--text);
}

input:focus, textarea:focus, select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79,110,246,.1);
}

/* ── Highlight classes ───────────── */
.hl-red { background: #fee2e2; color: #dc2626; font-weight: 600; padding: 1px 4px; border-radius: 3px; }
.hl-blue { background: #dbeafe; color: #2563eb; font-weight: 600; padding: 1px 4px; border-radius: 3px; }
.hl-green { background: #d1fae5; color: #059669; font-weight: 600; padding: 1px 4px; border-radius: 3px; }
.hl-orange { background: #ffedd5; color: #ea580c; font-weight: 600; padding: 1px 4px; border-radius: 3px; }
.hl-yellow { background: #fef9c3; color: #a16207; font-weight: 600; padding: 1px 4px; border-radius: 3px; }
.hl-purple { background: #ede9fe; color: #7c3aed; font-weight: 600; padding: 1px 4px; border-radius: 3px; }
.hl-bold { font-weight: 700; }

/* ── Scrollbar ───────────────────── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

/* ── Toast ───────────────────────── */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  z-index: 9999;
  animation: toastIn .3s ease;
  box-shadow: var(--shadow-lg);
}

.toast-error { background: var(--danger-light); color: var(--danger); border: 1px solid #fecaca; }
.toast-success { background: var(--success-light); color: var(--success); border: 1px solid #a7f3d0; }

@keyframes toastIn {
  from { opacity: 0; transform: translateX(-50%) translateY(10px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}
</style>
