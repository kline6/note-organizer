<script setup lang="ts">
import { ref, reactive } from "vue"
import { setApiKey, getApiKeyDisplay, hasApiKey, settingsApi } from "@/api"

const emit = defineEmits<{ close: [] }>()

const key = ref(getApiKeyDisplay())
const showKey = ref(false)
const testing = ref(false)
const saved = ref(false)
const testRes = ref<{ ok: boolean; text: string } | null>(null)
const existing = ref(hasApiKey())

function doSave() {
  setApiKey(key.value.trim())
  saved.value = true
  existing.value = !!key.value.trim()
  setTimeout(() => { saved.value = false }, 3000)
}

async function doTest() {
  if (!key.value.trim()) return
  testing.value = true; testRes.value = null
  doSave() // Save first so test uses latest key
  try {
    const r = await settingsApi.test(key.value.trim())
    testRes.value = { ok: r.ok, text: r.ok ? "连接成功" : (r.error || "连接失败") }
  } catch (e: any) {
    testRes.value = { ok: false, text: e.message || "请求失败" }
  }
  testing.value = false
}

function overlayClick(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains("overlay")) emit("close")
}
</script>

<template>
  <div class="overlay" @click="overlayClick">
    <div class="modal">
      <div class="mh">
        <h2>API 设置</h2>
        <button class="x" @click="emit('close')">×</button>
      </div>

      <div class="mb">
        <div class="field">
          <label>DeepSeek API Key</label>
          <div class="row">
            <input :type="showKey ? 'text' : 'password'" v-model="key" placeholder="sk-..." autocomplete="off" />
            <button class="btn-ghost" @click="showKey = !showKey">{{ showKey ? '隐藏' : '显示' }}</button>
          </div>
          <span class="hint">
            {{ existing && !key ? '已保存 Key（输入新 Key 将覆盖）' : '获取: platform.deepseek.com/api_keys' }}
          </span>
        </div>

        <div class="field">
          <label>说明</label>
          <p class="hint">
            API Key 仅保存在你的浏览器本地，不会上传到服务器。
            换浏览器或清除数据后需重新设置。
          </p>
        </div>

        <div v-if="testRes" :class="['res', testRes.ok ? 'ok' : 'err']">{{ testRes.ok ? '✓' : '✕' }} {{ testRes.text }}</div>
        <div v-if="saved" class="res ok">设置已保存</div>
      </div>

      <div class="mf">
        <button class="btn-ghost" :disabled="testing" @click="doTest">{{ testing ? '测试中...' : '测试连接' }}</button>
        <div class="fr">
          <button class="btn-ghost" @click="emit('close')">关闭</button>
          <button class="btn-primary" @click="doSave">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,.35); z-index: 2000; display: flex; align-items: center; justify-content: center; animation: fi .2s; }
@keyframes fi { from { opacity: 0 } to { opacity: 1 } }
.modal { background: #fff; border-radius: 16px; width: 480px; max-width: calc(100vw - 40px); box-shadow: 0 10px 30px rgba(0,0,0,.12); display: flex; flex-direction: column; animation: si .25s; }
@keyframes si { from { transform: translateY(24px); opacity: 0 } to { transform: translateY(0); opacity: 1 } }
.mh { display: flex; align-items: center; justify-content: space-between; padding: 18px 22px 12px; border-bottom: 1px solid #e8ecf1; }
.mh h2 { font-size: 17px; }
.x { background: none; font-size: 22px; color: #9ca3af; padding: 4px 10px; border-radius: 6px; border: none; cursor: pointer; }
.x:hover { background: #f3f4f6; color: #1a1d28; }
.mb { padding: 18px 22px; flex: 1; overflow-y: auto; }
.mf { display: flex; align-items: center; justify-content: space-between; padding: 14px 22px; border-top: 1px solid #e8ecf1; }
.fr { display: flex; gap: 8px; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 700; margin-bottom: 5px; }
.field input { width: 100%; box-sizing: border-box; }
.row { display: flex; gap: 8px; }
.row input { flex: 1; }
.hint { font-size: 11px; color: #9ca3af; margin-top: 4px; display: block; }
.res { padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; }
.ok { background: #ecfdf5; color: #059669; }
.err { background: #fef2f2; color: #dc2626; }
.btn-primary { background: #4f6ef6; color: #fff; font-weight: 600; padding: 8px 18px; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; }
.btn-primary:hover { filter: brightness(1.08); }
.btn-ghost { background: transparent; border: 1px solid #d1d5db; padding: 7px 14px; border-radius: 8px; font-size: 13px; cursor: pointer; color: #374151; }
.btn-ghost:hover { background: #f3f4f6; }
</style>
