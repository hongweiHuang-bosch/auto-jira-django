CREATE DATABASE IF NOT EXISTS `jira_analyzer` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `jira_analyzer`;

CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `analyzer_analysistask` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL DEFAULT 'Jira分析任务',
  `status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `progress` int unsigned NOT NULL DEFAULT 0,
  `message` longtext NOT NULL,
  `total_groups` int unsigned NOT NULL DEFAULT 0,
  `finished_groups` int unsigned NOT NULL DEFAULT 0,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `analyzer_issueanalysisresult` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `issue_key` varchar(64) NOT NULL,
  `summary` varchar(500) NOT NULL DEFAULT '',
  `model` varchar(100) NOT NULL DEFAULT '',
  `result_status` varchar(20) NOT NULL DEFAULT 'SUCCESS',
  `reply_text` longtext NOT NULL,
  `can_trace_image` varchar(500) NOT NULL DEFAULT '',
  `can_trace_image_url` varchar(500) NOT NULL DEFAULT '',
  `raw_signals` longtext NOT NULL,
  `has_commented_to_jira` tinyint(1) NOT NULL DEFAULT 0,
  `commented_at` datetime(6) DEFAULT NULL,
  `error_message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `task_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `analyzer_issueanalysisresult_task_issue_key_uniq` (`task_id`, `issue_key`),
  KEY `analyzer_issueanalysisresult_task_id_idx` (`task_id`),
  CONSTRAINT `analyzer_issueanalysisresult_task_id_fk` FOREIGN KEY (`task_id`) REFERENCES `analyzer_analysistask` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
