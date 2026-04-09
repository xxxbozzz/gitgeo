"""Add article_publications table for platform-level publication audit."""

from __future__ import annotations

from alembic import op


revision = "20260311_103000"
down_revision = "20260310_213115"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS `article_publications` (
          `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
          `article_id` bigint UNSIGNED NOT NULL COMMENT '关联文章ID',
          `platform` varchar(32) NOT NULL COMMENT '发布平台，如 zhihu/wechat',
          `publish_mode` varchar(20) NOT NULL DEFAULT 'draft' COMMENT '发布模式：draft/live',
          `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/draft_saved/published/failed',
          `trigger_mode` varchar(20) NOT NULL DEFAULT 'manual' COMMENT '触发方式：manual/retry/auto',
          `attempt_no` int NOT NULL DEFAULT 1 COMMENT '同平台第几次尝试',
          `retry_of_publication_id` bigint UNSIGNED DEFAULT NULL COMMENT '重试来源记录ID',
          `external_id` varchar(191) DEFAULT NULL COMMENT '平台侧文章/草稿/媒体ID',
          `external_url` varchar(500) DEFAULT NULL COMMENT '平台侧链接',
          `message` text DEFAULT NULL COMMENT '平台返回摘要信息',
          `error_message` text DEFAULT NULL COMMENT '失败错误信息',
          `request_payload_json` json DEFAULT NULL COMMENT '发起时请求载荷',
          `response_payload_json` json DEFAULT NULL COMMENT '平台返回原始结果',
          `published_at` datetime DEFAULT NULL COMMENT '平台确认成功时间',
          `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
          `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          KEY `idx_article_platform_created` (`article_id`, `platform`, `created_at`),
          KEY `idx_platform_status_created` (`platform`, `status`, `created_at`),
          KEY `idx_retry_of_publication_id` (`retry_of_publication_id`),
          CONSTRAINT `fk_article_publications_article`
            FOREIGN KEY (`article_id`) REFERENCES `geo_articles` (`id`)
            ON DELETE CASCADE,
          CONSTRAINT `fk_article_publications_retry`
            FOREIGN KEY (`retry_of_publication_id`) REFERENCES `article_publications` (`id`)
            ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS `article_publications`")
