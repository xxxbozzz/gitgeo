-- GEO Feedback Schema
-- 用途：记录关键词在 AI 平台的探测结果，以及可反哺生成 Prompt 的反馈摘要

CREATE TABLE IF NOT EXISTS `geo_probe_results` (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `keyword_id` bigint UNSIGNED DEFAULT NULL COMMENT '关键词ID',
  `keyword` varchar(191) NOT NULL COMMENT '关键词文本',
  `article_id` bigint UNSIGNED DEFAULT NULL COMMENT '关联文章ID',
  `platform` varchar(40) NOT NULL COMMENT '探测平台，如 deepseek / kimi',
  `mentioned` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否提及品牌或目标实体',
  `cited` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否出现引用型来源线索',
  `visibility_rank` tinyint DEFAULT NULL COMMENT '可见性层级，1最好',
  `visibility_score` decimal(6,2) DEFAULT NULL COMMENT '综合可见性得分',
  `evidence_labels_json` json DEFAULT NULL COMMENT '命中的证据标签，如 工程实践 / 官方文档',
  `source_hits_json` json DEFAULT NULL COMMENT '命中的来源或域名线索',
  `snapshot_text` text DEFAULT NULL COMMENT '抓取摘要',
  `detail_json` json DEFAULT NULL COMMENT '完整明细',
  `probed_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_keyword_platform_time` (`keyword`, `platform`, `probed_at`),
  KEY `idx_article_platform` (`article_id`, `platform`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `geo_keyword_feedback` (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `keyword_id` bigint UNSIGNED DEFAULT NULL COMMENT '关键词ID',
  `keyword` varchar(191) NOT NULL COMMENT '关键词文本',
  `article_id` bigint UNSIGNED DEFAULT NULL COMMENT '最近一次绑定文章ID',
  `citation_score` decimal(6,2) DEFAULT NULL COMMENT '文章自身可引用性得分',
  `probe_coverage_score` decimal(6,2) DEFAULT NULL COMMENT '外部平台探测得分',
  `feedback_labels_json` json DEFAULT NULL COMMENT '建议强化的标签集合',
  `article_signals_json` json DEFAULT NULL COMMENT '文章证据信号摘要',
  `probe_summary_json` json DEFAULT NULL COMMENT '最近一次探测汇总',
  `suggested_keywords_json` json DEFAULT NULL COMMENT '推荐继续扩展的关键词',
  `prompt_guidance` text DEFAULT NULL COMMENT '可直接注入下一轮 Prompt 的建议',
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_keyword_feedback_keyword` (`keyword`),
  KEY `idx_feedback_article` (`article_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
