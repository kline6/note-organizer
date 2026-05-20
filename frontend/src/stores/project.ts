import { defineStore } from "pinia"
import { ref } from "vue"
import { projectApi, classifyApi } from "@/api"
import type { Project, NoteFile, NoteEntry, Snapshot } from "@/types"

export const useProjectStore = defineStore("project", () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const files = ref<NoteFile[]>([])
  const currentFile = ref<NoteFile | null>(null)
  const entries = ref<NoteEntry[]>([])
  const snapshots = ref<Snapshot[]>([])
  const loading = ref(false)
  const error = ref("")

  async function loadProjects() {
    try {
      projects.value = await projectApi.list()
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function createProject(name: string) {
    const p = await projectApi.create(name)
    projects.value.unshift(p)
    return p
  }

  async function deleteProject(id: string) {
    await projectApi.delete(id)
    projects.value = projects.value.filter(p => p.id !== id)
    if (currentProject.value?.id === id) {
      currentProject.value = null
      files.value = []
      currentFile.value = null
      entries.value = []
    }
  }

  async function selectProject(id: string) {
    loading.value = true
    error.value = ""
    try {
      currentProject.value = await projectApi.get(id)
      files.value = await projectApi.listFiles(id)
      currentFile.value = null
      entries.value = []
      snapshots.value = await classifyApi.listSnapshots(id)
    } catch (e: any) {
      error.value = e?.response?.data?.detail || e.message || "加载项目失败"
    } finally {
      loading.value = false
    }
  }

  async function refreshFiles() {
    if (!currentProject.value) return
    try {
      files.value = await projectApi.listFiles(currentProject.value.id)
    } catch { /* silent */ }
  }

  async function selectFile(file: NoteFile) {
    if (!currentProject.value) return
    currentFile.value = file
    try {
      entries.value = await projectApi.listEntries(currentProject.value.id, file.id)
    } catch { entries.value = [] }
  }

  async function refreshEntries() {
    if (!currentProject.value || !currentFile.value) return
    try {
      entries.value = await projectApi.listEntries(currentProject.value.id, currentFile.value.id)
    } catch { /* silent */ }
  }

  async function moveEntry(entryId: string, targetFileId: string) {
    await classifyApi.moveEntry(entryId, targetFileId)
    await refreshFiles()
    await refreshEntries()
  }

  async function deleteEntry(entryId: string) {
    await classifyApi.deleteEntry(entryId)
    await refreshEntries()
    await refreshFiles()
  }

  async function deleteFile(fileId: string) {
    await classifyApi.deleteFile(fileId)
    await refreshFiles()
    if (currentFile.value?.id === fileId) {
      currentFile.value = null
      entries.value = []
    }
  }

  async function createSnapshot() {
    if (!currentProject.value) return
    await classifyApi.createSnapshot(currentProject.value.id)
    snapshots.value = await classifyApi.listSnapshots(currentProject.value.id)
  }

  async function restoreSnapshot(snapshotId: string) {
    if (!currentProject.value) return
    await classifyApi.restoreSnapshot(currentProject.value.id, snapshotId)
    await refreshFiles()
    await refreshEntries()
  }

  return {
    projects, currentProject, files, currentFile, entries, snapshots, loading, error,
    loadProjects, createProject, deleteProject, selectProject,
    refreshFiles, selectFile, refreshEntries,
    moveEntry, deleteEntry, deleteFile,
    createSnapshot, restoreSnapshot,
  }
})
