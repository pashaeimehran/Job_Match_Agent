CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS cv_documents (
    cv_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    dimensions INTEGER NOT NULL CHECK (dimensions BETWEEN 1 AND 2000),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cv_chunks (
    chunk_id TEXT NOT NULL,
    cv_id TEXT NOT NULL REFERENCES cv_documents(cv_id) ON DELETE CASCADE,
    section TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    embedding vector NOT NULL,
    PRIMARY KEY (cv_id, chunk_id),
    UNIQUE (cv_id, ordinal),
    CHECK (start_offset >= 0 AND end_offset > start_offset)
);
