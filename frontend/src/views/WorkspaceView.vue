<script setup lang="ts">
import { ref } from "vue"
import { useProjectStore } from "@/stores/project"
import FileDropZone from "@/components/FileDropZone.vue"
import NoteEditor from "@/components/NoteEditor.vue"
import RuleEditor from "@/components/RuleEditor.vue"
import ExportPanel from "@/components/ExportPanel.vue"
import SnapshotPanel from "@/components/SnapshotPanel.vue"
import SettingsPanel from "@/components/SettingsPanel.vue"

const store = useProjectStore()
const activeTab = ref<"work" | "rules" | "export" | "history">("work")
const showSettings = ref(false)
const showDrop = ref(false)

async function onFilesDropped() {
  await store.refreshFiles()
  if (store.currentFile) await store.refreshEntries()
  showDrop.value = false // auto-collapse after processing
}

const tabs = [
  { key: "work" as const, label: "工作区", icon: "📝" },
  { key: "rules" as const, label: "分类规则", icon: "⚙" },
  { key: "export" as const, label: "导出", icon: "📦" },
  { key: "history" as const, label: "历史版本", icon: "🕒" },
]
</script>

<template>
  <div class="workspace">
    <header class="ws-header">
      <div class="ws-tabs">
        <button v-for="t in tabs" :key="t.key"
          :class="['ws-tab', { active: activeTab === t.key }]"
          @click="activeTab = t.key">
          <span class="tab-icon">{{ t.icon }}</span> {{ t.label }}
        </button>
      </div>
      <button class="btn-ghost btn-sm" @click="showSettings = true">⚙ 设置</button>
    </header>

    <!-- Work tab: drop zone (collapsible) + editor -->
    <div v-show="activeTab === 'work'" class="ws-body">
      <button class="drop-toggle" @click="showDrop = !showDrop">
        {{ showDrop ? '收起上传区 ▲' : '拖入文件 / 粘贴文本 ▼' }}
      </button>
      <div v-show="showDrop" class="drop-wrap">
        <FileDropZone @processed="onFilesDropped" />
      </div>
      <NoteEditor />
    </div>

    <div v-show="activeTab === 'rules'" class="ws-body"><RuleEditor /></div>
    <div v-show="activeTab === 'export'" class="ws-body"><ExportPanel /></div>
    <div v-show="activeTab === 'history'" class="ws-body"><SnapshotPanel /></div>

    <SettingsPanel v-if="showSettings" @close="showSettings = false" />
  </div>
</template>

<style scoped>
.workspace { display: flex; flex-direction: column; height: 100%; overflow: hidden; }

.ws-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; background: #fff; border-bottom: 1px solid #e8ecf1;
  height: 46px; flex-shrink: 0;
}
.ws-tabs { display: flex; gap: 2px; }
.ws-tab {
  display: flex; align-items: center; gap: 5px; padding: 10px 16px;
  background: none; font-size: 13px; font-weight: 500; color: #6b7280;
  border: none; border-bottom: 2px solid transparent; cursor: pointer; transition: all .15s;
}
.ws-tab:hover { color: #1a1d28; background: #f3f4f6; }
.ws-tab.active { color: #4f6ef6; border-bottom-color: #4f6ef6; background: #eef1ff; }
.tab-icon { font-size: 15px; }

.ws-body { flex: 1; overflow: hidden; display: flex; flex-direction: column; padding: 0; }

/* Collapsible drop toggle */
.drop-toggle {
  width: 100%; padding: 8px; border: none; border-bottom: 1px solid #e8ecf1;
  background: #fafbfc; font-size: 12px; color: #6b7280; cursor: pointer;
  text-align: center; transition: background .15s; flex-shrink: 0;
}
.drop-toggle:hover { background: #f0f4ff; color: #4f6ef6; }

.drop-wrap { padding: 12px 16px 0; flex-shrink: 0; }

.btn-sm { padding: 5px 12px; font-size: 12px; }
.btn-ghost {
  background: transparent; border: 1px solid #d1d5db; padding: 7px 14px;
  border-radius: 8px; font-size: 13px; cursor: pointer; color: #374151;
}
.btn-ghost:hover { background: #f3f4f6; }
</style>
