-- GitGeo PostgreSQL Initialization
-- Auto-generated from MySQL schema files (schema.sql + job_runtime_schema.sql + feedback_schema.sql + pcb_capability_schema.sql)
-- Converted for PostgreSQL 17 + pgvector

-- 1. Core Articles
CREATE TABLE IF NOT EXISTS geo_articles (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  meta_json JSONB DEFAULT NULL,
  content_markdown TEXT,
  content_hash CHAR(32) NOT NULL,
  quality_score SMALLINT DEFAULT 0,
  publish_status SMALLINT DEFAULT 0,
  dim_subject VARCHAR(50) DEFAULT NULL,
  dim_action VARCHAR(50) DEFAULT NULL,
  dim_attribute VARCHAR(50) DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_articles_hash ON geo_articles(content_hash);

-- 2. Keywords
CREATE TABLE IF NOT EXISTS geo_keywords (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  keyword VARCHAR(100) NOT NULL UNIQUE,
  target_article_id BIGINT DEFAULT NULL,
  search_volume INTEGER DEFAULT 0,
  difficulty SMALLINT DEFAULT 0,
  cannibalization_risk SMALLINT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Internal Link Graph
CREATE TABLE IF NOT EXISTS geo_links (
  source_id BIGINT NOT NULL,
  target_id BIGINT NOT NULL,
  anchor_text VARCHAR(50) NOT NULL,
  weight SMALLINT DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (source_id, target_id)
);
CREATE INDEX IF NOT EXISTS idx_links_target ON geo_links(target_id);

-- 4. Article Publications
CREATE TABLE IF NOT EXISTS article_publications (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  article_id BIGINT NOT NULL REFERENCES geo_articles(id) ON DELETE CASCADE,
  platform VARCHAR(32) NOT NULL,
  publish_mode VARCHAR(20) NOT NULL DEFAULT 'draft',
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  trigger_mode VARCHAR(20) NOT NULL DEFAULT 'manual',
  attempt_no INTEGER NOT NULL DEFAULT 1,
  retry_of_publication_id BIGINT DEFAULT NULL REFERENCES article_publications(id) ON DELETE SET NULL,
  external_id VARCHAR(191) DEFAULT NULL,
  external_url VARCHAR(500) DEFAULT NULL,
  message TEXT DEFAULT NULL,
  error_message TEXT DEFAULT NULL,
  request_payload_json JSONB DEFAULT NULL,
  response_payload_json JSONB DEFAULT NULL,
  published_at TIMESTAMPTZ DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pub_article_platform ON article_publications(article_id, platform, created_at);
CREATE INDEX IF NOT EXISTS idx_pub_platform_status ON article_publications(platform, status, created_at);

-- 5. Job Runs
CREATE TABLE IF NOT EXISTS geo_job_runs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_uid VARCHAR(80) NOT NULL UNIQUE,
  run_type VARCHAR(40) NOT NULL DEFAULT 'article_generation',
  trigger_mode VARCHAR(40) NOT NULL DEFAULT 'auto',
  keyword_id BIGINT DEFAULT NULL,
  keyword VARCHAR(191) NOT NULL,
  article_id BIGINT DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'running',
  current_step VARCHAR(80) DEFAULT NULL,
  retry_count INTEGER NOT NULL DEFAULT 0,
  error_message TEXT DEFAULT NULL,
  detail_json JSONB DEFAULT NULL,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  finished_at TIMESTAMPTZ DEFAULT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_runs_status ON geo_job_runs(status, started_at);
CREATE INDEX IF NOT EXISTS idx_runs_keyword_id ON geo_job_runs(keyword_id);

-- 6. Job Steps
CREATE TABLE IF NOT EXISTS geo_job_steps (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  job_run_id BIGINT NOT NULL REFERENCES geo_job_runs(id) ON DELETE CASCADE,
  step_code VARCHAR(80) NOT NULL,
  step_name VARCHAR(120) NOT NULL,
  attempt_no INTEGER NOT NULL DEFAULT 1,
  status VARCHAR(20) NOT NULL DEFAULT 'running',
  article_id BIGINT DEFAULT NULL,
  error_message TEXT DEFAULT NULL,
  detail_json JSONB DEFAULT NULL,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  finished_at TIMESTAMPTZ DEFAULT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (job_run_id, step_code, attempt_no)
);
CREATE INDEX IF NOT EXISTS idx_steps_run ON geo_job_steps(job_run_id);
CREATE INDEX IF NOT EXISTS idx_steps_status ON geo_job_steps(status);

-- 7. Probe Results
CREATE TABLE IF NOT EXISTS geo_probe_results (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  keyword_id BIGINT DEFAULT NULL,
  keyword VARCHAR(191) NOT NULL,
  article_id BIGINT DEFAULT NULL,
  platform VARCHAR(40) NOT NULL,
  mentioned BOOLEAN NOT NULL DEFAULT FALSE,
  cited BOOLEAN NOT NULL DEFAULT FALSE,
  visibility_rank SMALLINT DEFAULT NULL,
  visibility_score DOUBLE PRECISION DEFAULT NULL,
  evidence_labels_json JSONB DEFAULT NULL,
  source_hits_json JSONB DEFAULT NULL,
  snapshot_text TEXT DEFAULT NULL,
  detail_json JSONB DEFAULT NULL,
  probed_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_probe_keyword_platform ON geo_probe_results(keyword, platform, probed_at);

-- 8. Keyword Feedback
CREATE TABLE IF NOT EXISTS geo_keyword_feedback (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  keyword_id BIGINT DEFAULT NULL,
  keyword VARCHAR(191) NOT NULL UNIQUE,
  article_id BIGINT DEFAULT NULL,
  citation_score DOUBLE PRECISION DEFAULT NULL,
  probe_coverage_score DOUBLE PRECISION DEFAULT NULL,
  feedback_labels_json JSONB DEFAULT NULL,
  article_signals_json JSONB DEFAULT NULL,
  probe_summary_json JSONB DEFAULT NULL,
  suggested_keywords_json JSONB DEFAULT NULL,
  prompt_guidance TEXT DEFAULT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Capability Profiles
CREATE TABLE IF NOT EXISTS geo_capability_profiles (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  profile_code VARCHAR(80) NOT NULL UNIQUE,
  brand_name VARCHAR(120) NOT NULL UNIQUE,
  public_brand_name VARCHAR(120) DEFAULT NULL,
  positioning VARCHAR(120) NOT NULL,
  claim_scope VARCHAR(40) NOT NULL DEFAULT 'public_safe',
  version_tag VARCHAR(80) DEFAULT NULL,
  source_policy VARCHAR(255) DEFAULT NULL,
  brand_aliases_json JSONB DEFAULT NULL,
  notes TEXT DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Capability Sources
CREATE TABLE IF NOT EXISTS geo_capability_sources (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_code VARCHAR(80) NOT NULL UNIQUE,
  source_vendor VARCHAR(120) NOT NULL,
  source_title VARCHAR(255) NOT NULL,
  source_type VARCHAR(40) NOT NULL,
  source_url VARCHAR(500) NOT NULL,
  publish_org VARCHAR(120) DEFAULT NULL,
  observed_on DATE DEFAULT NULL,
  reliability_score DOUBLE PRECISION NOT NULL DEFAULT 0.80,
  notes TEXT DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Capability Specs
CREATE TYPE metric_type_enum AS ENUM ('min', 'max', 'range', 'option', 'boolean', 'matrix', 'composite');
CREATE TYPE claim_level_enum AS ENUM ('public_safe', 'advanced_project', 'experimental');

CREATE TABLE IF NOT EXISTS geo_capability_specs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  profile_id BIGINT NOT NULL REFERENCES geo_capability_profiles(id) ON DELETE CASCADE,
  group_code VARCHAR(80) NOT NULL,
  group_name VARCHAR(120) NOT NULL,
  capability_code VARCHAR(80) NOT NULL,
  capability_name VARCHAR(120) NOT NULL,
  category VARCHAR(80) DEFAULT NULL,
  metric_type metric_type_enum NOT NULL DEFAULT 'range',
  unit VARCHAR(40) DEFAULT NULL,
  comparator VARCHAR(20) DEFAULT NULL,
  conservative_value_num DOUBLE PRECISION DEFAULT NULL,
  conservative_value_text VARCHAR(255) DEFAULT NULL,
  advanced_value_num DOUBLE PRECISION DEFAULT NULL,
  advanced_value_text VARCHAR(255) DEFAULT NULL,
  public_claim VARCHAR(500) DEFAULT NULL,
  internal_note TEXT DEFAULT NULL,
  conditions_text VARCHAR(500) DEFAULT NULL,
  application_tags_json JSONB DEFAULT NULL,
  claim_level claim_level_enum NOT NULL DEFAULT 'public_safe',
  confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.80,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (profile_id, capability_code)
);
CREATE INDEX IF NOT EXISTS idx_specs_group ON geo_capability_specs(group_code);
CREATE INDEX IF NOT EXISTS idx_specs_name ON geo_capability_specs(capability_name);

-- 12. Capability Spec Sources (junction table)
CREATE TABLE IF NOT EXISTS geo_capability_spec_sources (
  spec_id BIGINT NOT NULL REFERENCES geo_capability_specs(id) ON DELETE CASCADE,
  source_id BIGINT NOT NULL REFERENCES geo_capability_sources(id) ON DELETE CASCADE,
  citation_note VARCHAR(255) DEFAULT NULL,
  priority_weight SMALLINT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (spec_id, source_id)
);
CREATE INDEX IF NOT EXISTS idx_spec_sources_source ON geo_capability_spec_sources(source_id);

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
