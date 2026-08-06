PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('schema_version', '1');
INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('application_name', 'Sergio Knowledge OS');

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY,
  source_type TEXT NOT NULL,
  name TEXT NOT NULL,
  root_path TEXT,
  created_at TEXT NOT NULL,
  last_import_at TEXT,
  is_original_immutable INTEGER NOT NULL DEFAULT 1,
  notes TEXT,
  UNIQUE(source_type, name, root_path)
);

CREATE TABLE IF NOT EXISTS imports (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(id),
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  files_seen INTEGER NOT NULL DEFAULT 0,
  files_new INTEGER NOT NULL DEFAULT 0,
  files_duplicate INTEGER NOT NULL DEFAULT 0,
  errors_count INTEGER NOT NULL DEFAULT 0,
  report_path TEXT
);

CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY,
  permanent_id TEXT NOT NULL UNIQUE,
  sha256 TEXT NOT NULL UNIQUE,
  content_type TEXT NOT NULL,
  mime_type TEXT,
  extension TEXT,
  display_name TEXT NOT NULL,
  original_name TEXT,
  size_bytes INTEGER NOT NULL DEFAULT 0,
  storage_mode TEXT NOT NULL,
  storage_path TEXT,
  created_at TEXT,
  modified_at TEXT,
  indexed_at TEXT,
  is_missing INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS file_occurrences (
  id INTEGER PRIMARY KEY,
  file_id INTEGER NOT NULL REFERENCES files(id),
  source_id INTEGER REFERENCES sources(id),
  original_path TEXT NOT NULL,
  original_name TEXT,
  export_file_id TEXT,
  first_seen_at TEXT,
  last_seen_at TEXT,
  UNIQUE(file_id, original_path)
);

CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY,
  source_id INTEGER REFERENCES sources(id),
  external_id TEXT,
  title TEXT,
  created_at TEXT,
  updated_at TEXT,
  model TEXT,
  url TEXT,
  raw_json_path TEXT
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER NOT NULL REFERENCES conversations(id),
  parent_message_id INTEGER REFERENCES messages(id),
  role TEXT,
  author TEXT,
  content_text TEXT,
  created_at TEXT,
  model TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS conversation_assets (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER REFERENCES conversations(id),
  message_id INTEGER REFERENCES messages(id),
  file_id INTEGER NOT NULL REFERENCES files(id),
  relationship_type TEXT,
  caption TEXT
);

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  priority INTEGER NOT NULL DEFAULT 0,
  created_at TEXT,
  updated_at TEXT,
  favorite INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS file_projects (
  id INTEGER PRIMARY KEY,
  file_id INTEGER NOT NULL REFERENCES files(id),
  project_id INTEGER NOT NULL REFERENCES projects(id),
  role TEXT,
  confidence REAL,
  assigned_by TEXT NOT NULL DEFAULT 'system',
  created_at TEXT,
  notes TEXT,
  UNIQUE(file_id, project_id, role)
);

CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  category TEXT
);

CREATE TABLE IF NOT EXISTS file_tags (
  id INTEGER PRIMARY KEY,
  file_id INTEGER NOT NULL REFERENCES files(id),
  tag_id INTEGER NOT NULL REFERENCES tags(id),
  confidence REAL,
  assigned_by TEXT NOT NULL DEFAULT 'system',
  UNIQUE(file_id, tag_id)
);

CREATE TABLE IF NOT EXISTS duplicates (
  id INTEGER PRIMARY KEY,
  duplicate_group_id TEXT NOT NULL,
  file_id INTEGER NOT NULL REFERENCES files(id),
  occurrence_path TEXT,
  duplicate_type TEXT NOT NULL,
  reason TEXT,
  status TEXT NOT NULL DEFAULT 'needs_review',
  reviewed_at TEXT,
  review_notes TEXT,
  UNIQUE(duplicate_group_id, occurrence_path)
);

CREATE TABLE IF NOT EXISTS timeline_events (
  id INTEGER PRIMARY KEY,
  project_id INTEGER REFERENCES projects(id),
  file_id INTEGER REFERENCES files(id),
  conversation_id INTEGER REFERENCES conversations(id),
  event_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  event_date TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY,
  project_id INTEGER REFERENCES projects(id),
  conversation_id INTEGER REFERENCES conversations(id),
  message_id INTEGER REFERENCES messages(id),
  file_id INTEGER REFERENCES files(id),
  title TEXT,
  decision_text TEXT NOT NULL,
  decision_date TEXT,
  confidence REAL,
  created_by TEXT NOT NULL DEFAULT 'system'
);

CREATE TABLE IF NOT EXISTS operation_log (
  id INTEGER PRIMARY KEY,
  import_id INTEGER REFERENCES imports(id),
  operation_type TEXT NOT NULL,
  target_type TEXT,
  target_id INTEGER,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL,
  metadata_json TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
  entity_type,
  entity_id UNINDEXED,
  title,
  body,
  project_names,
  tags,
  source_name,
  path
);

CREATE INDEX IF NOT EXISTS idx_files_permanent_id ON files(permanent_id);
CREATE INDEX IF NOT EXISTS idx_file_occurrences_file_id ON file_occurrences(file_id);
CREATE INDEX IF NOT EXISTS idx_file_occurrences_source_id ON file_occurrences(source_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_file_projects_file_id ON file_projects(file_id);
CREATE INDEX IF NOT EXISTS idx_file_projects_project_id ON file_projects(project_id);
CREATE INDEX IF NOT EXISTS idx_file_tags_file_id ON file_tags(file_id);
CREATE INDEX IF NOT EXISTS idx_duplicates_group ON duplicates(duplicate_group_id);
CREATE INDEX IF NOT EXISTS idx_timeline_project_id ON timeline_events(project_id);
CREATE INDEX IF NOT EXISTS idx_decisions_project_id ON decisions(project_id);
