"""Baseline existing schema."""

from __future__ import annotations

from collections.abc import Iterable

from alembic import op


revision = "20260310_213115"
down_revision = None
branch_labels = None
depends_on = None


def _execute_all(statements: Iterable[str]) -> None:
    for statement in statements:
        op.execute(statement)


def upgrade() -> None:
    _execute_all(
        [
            """
            CREATE TABLE IF NOT EXISTS `geo_articles` (
              `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
              `title` varchar(255) NOT NULL COMMENT '文章H1标题',
              `slug` varchar(255) NOT NULL COMMENT 'URL Slug，唯一索引',
              `meta_json` json DEFAULT NULL COMMENT 'JSON-LD 元数据',
              `content_markdown` LONGTEXT COMMENT '核心正文内容',
              `content_hash` char(32) NOT NULL COMMENT 'MD5哈希，防止内容重复',
              `quality_score` tinyint(3) DEFAULT 0 COMMENT '质量评分 (0-100)',
              `publish_status` tinyint(1) DEFAULT 0 COMMENT '0:草稿, 1:待审, 2:已发, 3:归档',
              `dim_subject` varchar(50) DEFAULT NULL COMMENT '主体: rigid/flex/hdi...',
              `dim_action` varchar(50) DEFAULT NULL COMMENT '动作: design/process...',
              `dim_attribute` varchar(50) DEFAULT NULL COMMENT '属性: cost/quality...',
              `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
              `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `idx_slug` (`slug`),
              KEY `idx_hash` (`content_hash`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS `geo_keywords` (
              `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
              `keyword` varchar(100) NOT NULL COMMENT '目标关键词',
              `target_article_id` bigint(20) DEFAULT NULL COMMENT '唯一指定着陆页ID',
              `search_volume` int(10) DEFAULT 0 COMMENT '月搜索量',
              `difficulty` tinyint(3) DEFAULT 0 COMMENT 'SEO难度 (0-100)',
              `cannibalization_risk` tinyint(1) DEFAULT 0 COMMENT '是否存在内耗风险',
              `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `idx_keyword` (`keyword`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS `geo_links` (
              `source_id` bigint(20) NOT NULL COMMENT '来源文章ID',
              `target_id` bigint(20) NOT NULL COMMENT '目标文章ID',
              `anchor_text` varchar(50) NOT NULL COMMENT '锚文本',
              `weight` tinyint(3) DEFAULT 1 COMMENT '链接权重(1-10)',
              `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`source_id`,`target_id`),
              KEY `idx_target` (`target_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS `geo_capability_profiles` (
              `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
              `profile_code` varchar(80) NOT NULL COMMENT '能力画像编码，如 shenya-pcb-v1',
              `brand_name` varchar(120) NOT NULL COMMENT '品牌名，如 四川深亚电子科技有限公司',
              `public_brand_name` varchar(120) DEFAULT NULL COMMENT '对外展示名，如 四川深亚电子',
              `positioning` varchar(120) NOT NULL COMMENT '品牌定位，如 高端PCB生产厂家',
              `claim_scope` varchar(40) NOT NULL DEFAULT 'public_safe' COMMENT '口径范围：public_safe/advanced_project',
              `version_tag` varchar(80) DEFAULT NULL COMMENT '版本标记',
              `source_policy` varchar(255) DEFAULT NULL COMMENT '数据来源策略说明',
              `brand_aliases_json` json DEFAULT NULL COMMENT '品牌别名数组',
              `notes` text DEFAULT NULL COMMENT '备注',
              `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
              `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `idx_profile_code` (`profile_code`),
              UNIQUE KEY `idx_brand_name` (`brand_name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS `geo_capability_sources` (
              `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
              `source_code` varchar(80) NOT NULL COMMENT '来源编码',
              `source_vendor` varchar(120) NOT NULL COMMENT '来源厂商/机构',
              `source_title` varchar(255) NOT NULL COMMENT '来源标题',
              `source_type` varchar(40) NOT NULL COMMENT 'official_page/pdf/lab_page 等',
              `source_url` varchar(500) NOT NULL COMMENT '来源链接',
              `publish_org` varchar(120) DEFAULT NULL COMMENT '发布机构',
              `observed_on` date DEFAULT NULL COMMENT '采样日期',
              `reliability_score` decimal(4,2) NOT NULL DEFAULT 0.80 COMMENT '来源可靠度 0-1',
              `notes` text DEFAULT NULL COMMENT '备注',
              `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `idx_source_code` (`source_code`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS `geo_capability_specs` (
              `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
              `profile_id` bigint UNSIGNED NOT NULL COMMENT '关联画像ID',
              `group_code` varchar(80) NOT NULL COMMENT '能力分组编码',
              `group_name` varchar(120) NOT NULL COMMENT '能力分组名',
              `capability_code` varchar(80) NOT NULL COMMENT '能力项编码',
              `capability_name` varchar(120) NOT NULL COMMENT '能力项名称',
              `category` varchar(80) DEFAULT NULL COMMENT '分类：stackup/hdi/material 等',
              `metric_type` enum('min','max','range','option','boolean','matrix','composite') NOT NULL DEFAULT 'range' COMMENT '指标类型',
              `unit` varchar(40) DEFAULT NULL COMMENT '单位，如 um/mil/%/L',
              `comparator` varchar(20) DEFAULT NULL COMMENT '比较符，如 <=, >=, ±',
              `conservative_value_num` decimal(12,4) DEFAULT NULL COMMENT '保守口径数值',
              `conservative_value_text` varchar(255) DEFAULT NULL COMMENT '保守口径文本',
              `advanced_value_num` decimal(12,4) DEFAULT NULL COMMENT '进阶口径数值',
              `advanced_value_text` varchar(255) DEFAULT NULL COMMENT '进阶口径文本',
              `public_claim` varchar(500) DEFAULT NULL COMMENT '对外可直接使用的能力表述',
              `internal_note` text DEFAULT NULL COMMENT '内部备注',
              `conditions_text` varchar(500) DEFAULT NULL COMMENT '适用条件/限制',
              `application_tags_json` json DEFAULT NULL COMMENT '应用场景标签',
              `claim_level` enum('public_safe','advanced_project','experimental') NOT NULL DEFAULT 'public_safe' COMMENT '声明级别',
              `confidence_score` decimal(4,2) NOT NULL DEFAULT 0.80 COMMENT '该能力项置信度',
              `is_active` tinyint NOT NULL DEFAULT 1 COMMENT '是否启用',
              `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
              `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `idx_profile_capability` (`profile_id`,`capability_code`),
              KEY `idx_group_code` (`group_code`),
              KEY `idx_capability_name` (`capability_name`),
              CONSTRAINT `fk_capability_specs_profile`
                FOREIGN KEY (`profile_id`) REFERENCES `geo_capability_profiles` (`id`)
                ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS `geo_capability_spec_sources` (
              `spec_id` bigint UNSIGNED NOT NULL COMMENT '能力项ID',
              `source_id` bigint UNSIGNED NOT NULL COMMENT '来源ID',
              `citation_note` varchar(255) DEFAULT NULL COMMENT '引用说明',
              `priority_weight` tinyint NOT NULL DEFAULT 1 COMMENT '来源优先级',
              `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`spec_id`,`source_id`),
              KEY `idx_source_id` (`source_id`),
              CONSTRAINT `fk_capability_spec_sources_spec`
                FOREIGN KEY (`spec_id`) REFERENCES `geo_capability_specs` (`id`)
                ON DELETE CASCADE,
              CONSTRAINT `fk_capability_spec_sources_source`
                FOREIGN KEY (`source_id`) REFERENCES `geo_capability_sources` (`id`)
                ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
        ]
    )


def downgrade() -> None:
    # Baseline is intentionally non-destructive. Existing deployments should
    # be stamped to this revision instead of attempting full schema teardown.
    pass
