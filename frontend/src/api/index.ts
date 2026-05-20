import axios from "axios"
import type {
  Project, NoteFile, NoteEntry,
  ClassificationRule, HighlightRule, Snapshot, ClassifyResult,
} from "@/types"

// ── Session & API Key (browser localStorage) ──
function getSessionId(): string {
  let id = localStorage.getItem("nf_session_id")
  if (!id) {
    id = "sess_" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36)
    localStorage.setItem("nf_session_id", id)
  }
  return id
}

function getApiKey(): string {
  return localStorage.getItem("nf_api_key") || ""
}

export function setApiKey(key: string) { localStorage.setItem("nf_api_key", key) }
export function getApiKeyDisplay(): string { return getApiKey() }
export function hasApiKey(): boolean { return !!getApiKey() }

// ── Stream API (SSE real-time classification) ──
export function streamClassify(
  projectId: string,
  text: string,
  onEntry: (data: any) => void,
  onDone: (data: any) => void,
  onError: (msg: string) => void,
  onStatus: (msg: string) => void,
): AbortController {
  const controller = new AbortController()
  fetch("/api/stream/classify", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": getApiKey(),
      "X-Session-ID": getSessionId(),
    },
    body: JSON.stringify({ project_id: projectId, summary_text: text }),
    signal: controller.signal,
  }).then(async response => {
    if (!response.ok) {
      const err = await response.text()
      onError(err || "Request failed")
      return
    }
    const reader = response.body?.getReader()
    if (!reader) { onError("No response body"); return }
    const decoder = new TextDecoder()
    let buffer = ""
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n\n")
      buffer = lines.pop() || ""
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === "entry") onEntry(data)
            else if (data.type === "done") onDone(data)
            else if (data.type === "error") onError(data.msg)
            else if (data.type === "status") onStatus(data.msg)
          } catch {}
        }
      }
    }
  }).catch(e => {
    if (e.name !== "AbortError") onError(e.message || "Stream failed")
  })
  return controller
}

// ── Axios instance ──
const api = axios.create({ baseURL: "/api", timeout: 600000 }) // 10 min for AI analysis

api.interceptors.request.use(config => {
  config.headers["X-Session-ID"] = getSessionId()
  const key = getApiKey()
  if (key) config.headers["X-API-Key"] = key
  return config
})

// ── Project API ──
export const projectApi = {
  list: () => api.get<Project[]>("/projects").then(r => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}`).then(r => r.data),
  create: (name: string) => api.post<Project>("/projects", { name }).then(r => r.data),
  delete: (id: string) => api.delete(`/projects/${id}`).then(r => r.data),
  listFiles: (projectId: string) =>
    api.get<NoteFile[]>(`/projects/${projectId}/files`).then(r => r.data),
  listEntries: (projectId: string, fileId: string) =>
    api.get<NoteEntry[]>(`/projects/${projectId}/files/${fileId}/entries`).then(r => r.data),
}

// ── Classify API ──
export const classifyApi = {
  uploadSummary: (projectId: string, file: File) => {
    const fd = new FormData(); fd.append("project_id", projectId); fd.append("file", file)
    return api.post<{ ok: boolean; results: ClassifyResult; source_file: string }>("/classify/upload-summary", fd).then(r => r.data)
  },
  classifyText: (projectId: string, summaryText: string) =>
    api.post<{ ok: boolean; results: ClassifyResult }>("/classify/classify-text", { project_id: projectId, summary_text: summaryText }).then(r => r.data),
  uploadExisting: (projectId: string, files: File[]) => {
    const fd = new FormData(); fd.append("project_id", projectId); files.forEach(f => fd.append("files", f))
    return api.post("/classify/upload-existing", fd).then(r => r.data)
  },
  moveEntry: (entryId: string, targetFileId: string) =>
    api.post("/classify/move-entry", { entry_id: entryId, target_file_id: targetFileId }).then(r => r.data),
  mergeDecision: (entryId: string, action: "merge" | "replace" | "skip") =>
    api.post("/classify/merge-decision", { entry_id: entryId, action }).then(r => r.data),
  deleteEntry: (entryId: string) => api.delete(`/classify/entries/${entryId}`).then(r => r.data),
  deleteFile: (fileId: string) => api.delete(`/classify/files/${fileId}`).then(r => r.data),
  createSnapshot: (projectId: string) => {
    const fd = new FormData(); fd.append("project_id", projectId)
    return api.post("/classify/snapshot", fd).then(r => r.data)
  },
  listSnapshots: (projectId: string) =>
    api.get<Snapshot[]>(`/classify/${projectId}/snapshots`).then(r => r.data),
  restoreSnapshot: (projectId: string, snapshotId: string) =>
    api.post(`/classify/${projectId}/restore/${snapshotId}`).then(r => r.data),
}

// ── Export API ──
export const exportApi = {
  exportAll: (projectId: string, fmt: string) => {
    const url = `/export/all/${projectId}?fmt=${fmt}`
    return api.post(url, null, { responseType: "blob" }).then(r => {
      const a = document.createElement("a")
      a.href = URL.createObjectURL(r.data as Blob)
      a.download = fmt === "docx" || fmt === "pdf" || fmt === "html"
        ? `export_${projectId}.${fmt}` : `export_${projectId}.zip`
      a.click(); URL.revokeObjectURL(a.href)
    })
  },
  exportSingle: (fileId: string, fmt: string) =>
    api.post(`/export/file/${fileId}?fmt=${fmt}`, null, { responseType: "blob" }).then(r => {
      const a = document.createElement("a")
      a.href = URL.createObjectURL(r.data as Blob)
      a.download = `export.${fmt}`
      a.click(); URL.revokeObjectURL(a.href)
    }),
}

// ── Rules API ──
export const ruleApi = {
  listClassification: (projectId: string) =>
    api.get<ClassificationRule[]>(`/rules/classification/${projectId}`).then(r => r.data),
  createClassification: (data: { project_id: string; pattern: string; target_file: string; priority: number }) =>
    api.post<ClassificationRule>("/rules/classification", data).then(r => r.data),
  deleteClassification: (ruleId: string) => api.delete(`/rules/classification/${ruleId}`).then(r => r.data),
  listHighlight: (projectId: string) =>
    api.get<HighlightRule[]>(`/rules/highlight/${projectId}`).then(r => r.data),
  createHighlight: (data: { project_id: string; pattern: string; color: string; style?: string; label?: string }) =>
    api.post<HighlightRule>("/rules/highlight", data).then(r => r.data),
  deleteHighlight: (ruleId: string) => api.delete(`/rules/highlight/${ruleId}`).then(r => r.data),
  batchCreate: (projectId: string, cr: any[], hr: any[]) =>
    api.post(`/rules/batch/${projectId}`, { classification_rules: cr, highlight_rules: hr }).then(r => r.data),
}

// ── Settings API ──
export const settingsApi = {
  get: () => api.get<{ has_api_key: boolean }>("/settings").then(r => r.data),
  test: (key: string) =>
    api.post<{ ok: boolean; message?: string; error?: string }>("/settings/test", null, { headers: { "X-Test-Key": key } }).then(r => r.data),
}
