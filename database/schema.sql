-- Geo Knowledge Engine Schema
-- Database: geo_knowledge_engine

-- 1. 核心文章表 (Core Articles)
CREATE TABLE IF NOT EXISTS `geo_articles` (
  `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL COMMENT '文章H1标题',
  `slug` varchar(255) NOT NULL COMMENT 'URL Slug，唯一索引',
  `meta_json` json DEFAULT NULL COMMENT 'JSON-LD 元数据',
  `content_markdown` LONGTEXT COMMENT '核心正文内容',
  `content_hash` char(32) NOT NULL COMMENT 'MD5哈希，防止内容重复',
  `quality_score` tinyint(3) DEFAULT 0 COMMENT '质量评分 (0-100)',
  `publish_status` tinyint(1) DEFAULT 0 COMMENT '0:草稿, 1:待审, 2:已发, 3:归档',
  -- Multidimensional Tags
  `dim_subject` varchar(50) DEFAULT NULL COMMENT '主体: rigid/flex/hdi...',
  `dim_action` varchar(50) DEFAULT NULL COMMENT '动作: design/process...',
  `dim_attribute` varchar(50) DEFAULT NULL COMMENT '属性: cost/quality...',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_slug` (`slug`),
  KEY `idx_hash` (`content_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 关键词与内耗控制表 (Keyword Cannibalization Control)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 内链关系图谱 (Internal Link Graph)
CREATE TABLE IF NOT EXISTS `geo_links` (
  `source_id` bigint(20) NOT NULL COMMENT '来源文章ID',
  `target_id` bigint(20) NOT NULL COMMENT '目标文章ID',
  `anchor_text` varchar(50) NOT NULL COMMENT '锚文本',
  `weight` tinyint(3) DEFAULT 1 COMMENT '链接权重(1-10)',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`source_id`,`target_id`),
  KEY `idx_target` (`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
