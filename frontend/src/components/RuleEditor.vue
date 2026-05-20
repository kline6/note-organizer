<script setup lang="ts">
import { ref, onMounted, watch } from "vue"
import { useProjectStore } from "@/stores/project"
import { ruleApi } from "@/api"
import type { ClassificationRule, HighlightRule } from "@/types"

const store = useProjectStore()
const classRules = ref<ClassificationRule[]>([])
const highlightRules = ref<HighlightRule[]>([])
const msg = ref("")
const showAddClass = ref(false)
const showAddHl = ref(false)

// Classification form
const classPat = ref("")
const classTarget = ref("")

// Highlight form
const hlPat = ref("")
const hlColor = ref("#ef4444")
const hlLabel = ref("")

const presetPatterns = [
  { pattern: "bug|报错|异常|故障|问题", label: "技术问题" },
  { pattern: "下周|截止|DDL|deadline|计划", label: "待办事项" },
  { pattern: "完成|已处理|搞定|OK|解决", label: "已完成" },
  { pattern: "会议|周报|日报|汇报|纪要", label: "会议记录" },
  { pattern: "学习|教程|文档|阅读|笔记", label: "学习笔记" },
]

const presetColors = [
  { color: "#ef4444", label: "红色", hint: "紧急 / 问题" },
  { color: "#3b82f6", label: "蓝色", hint: "待办 / 计划" },
  { color: "#10b981", label: "绿色", hint: "完成 / 通过" },
  { color: "#f97316", label: "橙色", hint: "重要 / 提醒" },
  { color: "#eab308", label: "黄色", hint: "注意 / 警告" },
  { color: "#8b5cf6", label: "紫色", hint: "其他关注" },
]

async function load() {
  if (!store.currentProject) return
  classRules.value = await ruleApi.listClassification(store.currentProject.id)
  highlightRules.value = await ruleApi.listHighlight(store.currentProject.id)
}
watch(() => store.currentProject, () => { if (store.currentProject) load() })
onMounted(() => { if (store.currentProject) load() })

async function addClass() {
  if (!classPat.value.trim() || !classTarget.value.trim() || !store.currentProject) return
  await ruleApi.createClassification({ project_id: store.currentProject.id, pattern: classPat.value.trim(), target_file: classTarget.value.trim(), priority: 0 })
  classPat.value = ""; classTarget.value = ""; showAddClass.value = false
  await load()
}

async function addPreset(pat: string, label: string) {
  if (!store.currentProject) return
  await ruleApi.createClassification({ project_id: store.currentProject.id, pattern: pat, target_file: label + ".txt", priority: 0 })
  await load()
  msg.value = `已添加规则: ${label}`
  setTimeout(() => { msg.value = "" }, 2000)
}

async function addHl() {
  if (!hlPat.value.trim() || !store.currentProject) return
  await ruleApi.createHighlight({ project_id: store.currentProject.id, pattern: hlPat.value.trim(), color: hlColor.value, label: hlLabel.value.trim() || undefined })
  hlPat.value = ""; hlLabel.value = ""; showAddHl.value = false
  await load()
}

function hasPreset(pat: string) { return classRules.value.some(r => r.pattern === pat) }

async function delClass(id: string) { await ruleApi.deleteClassification(id); await load() }
async function delHl(id: string) { await ruleApi.deleteHighlight(id); await load() }
</script>

<template>
  <div class="rules" v-if="store.currentProject">
    <div v-if="msg" class="toast">{{ msg }}</div>

    <!-- ====== Classification Rules ====== -->
    <div class="card">
      <div class="card-hd">
        <div>
          <h3>📋 分类规则</h3>
          <p class="desc">关键词匹配后自动归入指定文件，AI 优先遵循</p>
        </div>
        <button class="btn btn-primary" @click="showAddClass = !showAddClass">{{ showAddClass ? '取消' : '＋ 添加规则' }}</button>
      </div>

      <!-- Quick presets -->
      <div class="presets">
        <span class="pre-label">快速添加：</span>
        <button v-for="p in presetPatterns" :key="p.label" class="pre-chip"
          @click="addPreset(p.pattern, p.label)"
          :disabled="hasPreset(p.pattern)">
          {{ hasPreset(p.pattern) ? '✓ ' : '' }}{{ p.label }}
        </button>
      </div>

      <!-- Add form -->
      <div v-if="showAddClass" class="add-panel">
        <div class="add-row">
          <div class="add-fld">
            <label>匹配关键词</label>
            <input v-model="classPat" placeholder="bug|报错|异常 (支持正则)" @keyup.enter="addClass" />
          </div>
          <div class="add-fld">
            <label>归入文件</label>
            <input v-model="classTarget" placeholder="技术问题.txt" @keyup.enter="addClass" list="file-list" />
            <datalist id="file-list">
              <option v-for="f in store.files" :key="f.filename" :value="f.filename" />
            </datalist>
          </div>
          <button class="btn btn-primary add-btn" @click="addClass">确认</button>
        </div>
      </div>

      <!-- Rule table -->
      <table class="tbl" v-if="classRules.length > 0">
        <thead><tr><th>匹配关键词</th><th>归入文件</th><th></th></tr></thead>
        <tbody>
          <tr v-for="r in classRules" :key="r.id">
            <td><code>{{ r.pattern }}</code></td>
            <td><span class="target">📄 {{ r.target_file }}</span></td>
            <td class="td-act"><button class="btn-del" @click="delClass(r.id)">删除</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ====== Highlight Rules ====== -->
    <div class="card">
      <div class="card-hd">
        <div>
          <h3>🎨 高亮标注规则</h3>
          <p class="desc">匹配的内容自动用指定颜色高亮显示</p>
        </div>
        <button class="btn btn-primary" @click="showAddHl = !showAddHl">{{ showAddHl ? '取消' : '＋ 添加规则' }}</button>
      </div>

      <div v-if="showAddHl" class="add-panel">
        <div class="add-row">
          <div class="add-fld">
            <label>匹配关键词</label>
            <input v-model="hlPat" placeholder="关键词|另一关键词" @keyup.enter="addHl" />
          </div>
          <div class="add-fld add-fld-sm">
            <label>颜色</label>
            <div class="color-pick">
              <button v-for="c in presetColors" :key="c.color"
                :class="['c-opt', { sel: hlColor === c.color }]"
                :style="{ background: c.color }" :title="c.label + ' ' + c.hint"
                @click="hlColor = c.color"></button>
            </div>
          </div>
          <div class="add-fld add-fld-xs">
            <label>标签 <span class="opt">可选</span></label>
            <input v-model="hlLabel" placeholder="紧急" @keyup.enter="addHl" />
          </div>
          <button class="btn btn-primary add-btn" @click="addHl">确认</button>
        </div>
      </div>

      <!-- Highlight grid -->
      <div class="hl-grid" v-if="highlightRules.length > 0">
        <div v-for="r in highlightRules" :key="r.id" class="hl-item">
          <span class="hl-dot" :style="{ background: r.color }"></span>
          <div class="hl-body">
            <code>{{ r.pattern }}</code>
            <span v-if="r.label" class="hl-tag">{{ r.label }}</span>
          </div>
          <button class="btn-del" @click="delHl(r.id)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rules { max-width: 860px; display: flex; flex-direction: column; gap: 20px; }

/* Cards */
.card { background: #fff; border: 1px solid #e8ecf1; border-radius: 12px; padding: 20px; }
.card-hd { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.card-hd h3 { font-size: 15px; font-weight: 700; margin-bottom: 2px; }
.desc { font-size: 12px; color: #9ca3af; margin: 0; }

/* Presets */
.presets { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
.pre-label { font-size: 11px; color: #9ca3af; font-weight: 600; flex-shrink: 0; }
.pre-chip {
  font-size: 12px; padding: 5px 12px; border-radius: 16px; border: 1px solid #d1d5db;
  background: #fafafa; cursor: pointer; transition: all .15s; font-weight: 500;
}
.pre-chip:hover:not(:disabled) { border-color: #4f6ef6; color: #4f6ef6; background: #eef1ff; }
.pre-chip:disabled { opacity: .4; cursor: default; }

/* Add panel */
.add-panel {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 16px; margin-bottom: 14px;
}
.add-row { display: flex; gap: 10px; align-items: flex-end; }
.add-fld { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.add-fld-sm { flex: .8; min-width: 200px; }
.add-fld-xs { flex: .5; }
.add-fld label { font-size: 11px; font-weight: 600; color: #6b7280; }
.add-fld input { padding: 8px 10px; font-size: 13px; width: 100%; }
.opt { font-weight: 400; color: #9ca3af; }
.add-btn { align-self: flex-end; height: 38px; white-space: nowrap; }

/* Color picker */
.color-pick { display: flex; gap: 5px; }
.c-opt { width: 26px; height: 26px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; transition: all .15s; }
.c-opt:hover { transform: scale(1.15); }
.c-opt.sel { border-color: #1a1d28; transform: scale(1.1); }

/* Table */
.tbl { width: 100%; border-collapse: collapse; }
.tbl th { text-align: left; font-size: 11px; font-weight: 600; color: #9ca3af; text-transform: uppercase; padding: 0 0 8px; }
.tbl td { padding: 7px 0; font-size: 13px; border-bottom: 1px solid #f3f4f6; }
.tbl code {
  font-size: 12px; background: #fdf2f8; color: #be185d;
  padding: 3px 8px; border-radius: 4px; font-family: "SF Mono", "Fira Code", "Consolas", monospace;
}
.target { color: #374151; font-weight: 500; }
.td-act { text-align: right; }

/* Highlight grid */
.hl-grid { display: flex; flex-direction: column; gap: 4px; }
.hl-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; background: #f9fafb; border-radius: 8px;
}
.hl-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 0 2px rgba(0,0,0,.06); }
.hl-body { flex: 1; display: flex; align-items: center; gap: 8px; }
.hl-tag { font-size: 10px; background: #e5e7eb; color: #6b7280; padding: 2px 7px; border-radius: 8px; font-weight: 600; }
.hl-body code { font-size: 12px; }

/* Buttons */
.btn {
  font-size: 12px; font-weight: 600; padding: 7px 16px; border-radius: 8px;
  border: none; cursor: pointer; transition: all .15s;
}
.btn-primary { background: #4f6ef6; color: #fff; }
.btn-primary:hover { filter: brightness(1.08); }
.btn-del { font-size: 11px; color: #9ca3af; background: none; border: none; cursor: pointer; padding: 3px 8px; border-radius: 4px; }
.btn-del:hover { background: #fef2f2; color: #dc2626; }

/* Toast */
.toast {
  padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 500;
  background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0;
}
</style>
