-- GEO Runtime Job Schema
-- 用途：记录每个关键词处理 run 及其步骤状态，支撑工程化追踪、失败定位与后续重试

CREATE TABLE IF NOT EXISTS `geo_job_runs` (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `run_uid` varchar(80) NOT NULL COMMENT '运行唯一ID，如 kw-12-1741600000000',
  `run_type` varchar(40) NOT NULL DEFAULT 'article_generation' COMMENT '运行类型',
  `trigger_mode` varchar(40) NOT NULL DEFAULT 'auto' COMMENT '触发方式，如 keyword_auto / geo_gap_auto / manual',
  `keyword_id` bigint UNSIGNED DEFAULT NULL COMMENT '关键词ID',
  `keyword` varchar(191) NOT NULL COMMENT '关键词文本',
  `article_id` bigint UNSIGNED DEFAULT NULL COMMENT '运行产出的文章ID',
  `status` varchar(20) NOT NULL DEFAULT 'running' COMMENT 'running/succeeded/failed/partial',
  `current_step` varchar(80) DEFAULT NULL COMMENT '当前步骤编码',
  `retry_count` int NOT NULL DEFAULT 0 COMMENT '重试次数',
  `error_message` text DEFAULT NULL COMMENT '运行级错误信息',
  `detail_json` json DEFAULT NULL COMMENT '运行摘要',
  `started_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `finished_at` datetime DEFAULT NULL,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_run_uid` (`run_uid`),
  KEY `idx_status_started` (`status`, `started_at`),
  KEY `idx_keyword_id` (`keyword_id`),
  KEY `idx_article_id` (`article_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `geo_job_steps` (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `job_run_id` bigint UNSIGNED NOT NULL COMMENT '所属 run ID',
  `step_code` varchar(80) NOT NULL COMMENT '步骤编码，如 generate / quality_check / export_html',
  `step_name` varchar(120) NOT NULL COMMENT '步骤中文名',
  `attempt_no` int NOT NULL DEFAULT 1 COMMENT '第几次尝试',
  `status` varchar(20) NOT NULL DEFAULT 'running' COMMENT 'running/succeeded/failed/skipped',
  `article_id` bigint UNSIGNED DEFAULT NULL COMMENT '关联文章ID',
  `error_message` text DEFAULT NULL COMMENT '步骤错误信息',
  `detail_json` json DEFAULT NULL COMMENT '步骤明细',
  `started_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `finished_at` datetime DEFAULT NULL,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_run_step_attempt` (`job_run_id`, `step_code`, `attempt_no`),
  KEY `idx_job_run_id` (`job_run_id`),
  KEY `idx_step_status` (`status`),
  CONSTRAINT `fk_job_steps_run`
    FOREIGN KEY (`job_run_id`) REFERENCES `geo_job_runs` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
