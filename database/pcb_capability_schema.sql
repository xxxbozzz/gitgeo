-- PCB Capability Knowledge Schema
-- 用途：为 GEO 系统补充“工程能力参数层”，支撑选题、写作、证据链与品牌能力植入

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
