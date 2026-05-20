export interface Project {
  id: string
  name: string
  workspace_dir: string
  created_at: string
  updated_at: string
}

export interface NoteFile {
  id: string
  project_id: string
  filename: string
  filepath: string
  keywords: string | null
  summary: string | null
  color_tag: string | null
  created_by_ai: boolean
  sort_order: number
  created_at: string
  updated_at: string
  entry_count: number
}

export interface NoteEntry {
  id: string
  note_file_id: string
  content: string
  highlighted_content: string | null
  importance: string | null
  color: string | null
  source_note: string | null
  sort_order: number
  similarity_score: number | null
  linked_entry_id: string | null
  created_at: string
}

export interface ClassificationRule {
  id: string
  project_id: string
  pattern: string
  target_file: string
  priority: number
  created_at: string
}

export interface HighlightRule {
  id: string
  project_id: string
  pattern: string
  color: string
  style: string | null
  label: string | null
  created_at: string
}

export interface Snapshot {
  id: string
  description: string
  created_at: string
}

export interface ClassifyResult {
  total_entries: number
  assigned: ClassifyEntryResult[]
  created_new: ClassifyEntryResult[]
  similar_found: SimilarEntryResult[]
  cross_links: CrossLinkResult[]
}

export interface ClassifyEntryResult {
  entry_id: string
  content: string
  target_file: string
  target_file_id: string
  is_new_file: boolean
  is_similar: boolean
  keywords: string[]
  summary: string
}

export interface SimilarEntryResult {
  entry_id: string
  entry_content: string
  target_file: string
  target_file_id: string
  similar: { entry_id: string; similarity: number; existing_content: string }[]
}

export interface CrossLinkResult {
  entry_id: string
  linked_file_id: string
  relation_reason: string
}
