<script setup lang="ts">
import { ref } from "vue"
import { useProjectStore } from "@/stores/project"

const store = useProjectStore()
const restoring = ref(false)
const msg = ref("")

async function handleCreate() {
  msg.value = "创建快照中..."
  try {
    await store.createSnapshot()
    msg.value = "快照已创建"
    setTimeout(() => { msg.value = "" }, 3000)
  } catch (e: any) {
    msg.value = "创建失败: " + (e.message || "")
  }
}

async function handleRestore(id: string) {
  if (!confirm("确认恢复到此版本？当前修改将丢失。")) return
  restoring.value = true
  msg.value = ""
  try {
    await store.restoreSnapshot(id)
    msg.value = "已恢复"
    setTimeout(() => { msg.value = "" }, 3000)
  } catch (e: any) {
    msg.value = "恢复失败: " + (e.message || "")
  } finally {
    restoring.value = false
  }
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString("zh-CN")
}
</script>

<template>
  <div class="snap">
    <div class="card">
      <div class="card-head">
        <h3>历史快照</h3>
        <button class="btn-primary btn-sm" @click="handleCreate">＋ 创建快照</button>
      </div>
      <p class="desc">每次划分自动保存快照，也可手动创建，支持一键回退</p>

      <div v-if="msg" class="result ok">{{ msg }}</div>

      <div class="snap-list">
        <div v-for="s in store.snapshots" :key="s.id" class="snap-row">
          <div>
            <span class="snap-desc">{{ s.description || "快照" }}</span>
            <span class="snap-time">{{ fmtDate(s.created_at) }}</span>
          </div>
          <button class="btn-ghost btn-sm" :disabled="restoring" @click="handleRestore(s.id)">
            恢复
          </button>
        </div>
        <div v-if="store.snapshots.length === 0" class="empty">暂无快照</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.snap { max-width: 800px; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}

.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.card-head h3 { font-size: 15px; font-weight: 700; }
.desc { font-size: 13px; color: var(--text-muted); margin-bottom: 14px; }

.result { padding: 8px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; }
.ok { background: var(--success-light); color: var(--success); }

.snap-list { display: flex; flex-direction: column; gap: 6px; }
.snap-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: var(--bg); border-radius: 8px;
}
.snap-desc { font-size: 13px; font-weight: 500; display: block; }
.snap-time { font-size: 11px; color: var(--text-muted); }
.empty { padding: 30px; text-align: center; color: var(--text-muted); font-size: 13px; }
.btn-sm { padding: 5px 14px; font-size: 12px; }
</style>
