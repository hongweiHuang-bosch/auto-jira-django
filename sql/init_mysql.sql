CREATE DATABASE IF NOT EXISTS `jira_analyzer` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `jira_analyzer`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`, `model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`, `codename`),
  KEY `auth_permission_content_type_id_2f476e4b` (`content_type_id`),
  CONSTRAINT `auth_permission_content_type_id_fk` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_name_a6ea08ec_uniq` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_username_6821ab7c_uniq` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`, `permission_id`),
  KEY `auth_group_permissions_group_id_b120cbf9` (`group_id`),
  KEY `auth_group_permissions_permission_id_84c5c92e` (`permission_id`),
  CONSTRAINT `auth_group_permissions_group_id_fk` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`) ON DELETE CASCADE,
  CONSTRAINT `auth_group_permissions_permission_id_fk` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`, `group_id`),
  KEY `auth_user_groups_user_id_6a12ed8b` (`user_id`),
  KEY `auth_user_groups_group_id_97559544` (`group_id`),
  CONSTRAINT `auth_user_groups_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `auth_user_groups_group_id_fk` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`, `permission_id`),
  KEY `auth_user_user_permissions_user_id_a95ead1b` (`user_id`),
  KEY `auth_user_user_permissions_permission_id_1fbb5f2c` (`permission_id`),
  CONSTRAINT `auth_user_user_permissions_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `auth_user_user_permissions_permission_id_fk` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_fk` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`) ON DELETE SET NULL,
  CONSTRAINT `django_admin_log_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyzer_analysistask` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL DEFAULT 'Jira分析任务',
  `role_index` int unsigned NOT NULL DEFAULT 0,
  `role_label` varchar(200) NOT NULL DEFAULT '',
  `jql` longtext NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `progress` int unsigned NOT NULL DEFAULT 0,
  `message` longtext NOT NULL,
  `total_groups` int unsigned NOT NULL DEFAULT 0,
  `finished_groups` int unsigned NOT NULL DEFAULT 0,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `analyzer_analysistask_role_index_023a818f` (`role_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyzer_issueanalysisresult` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `task_id` bigint NOT NULL,
  `issue_key` varchar(64) NOT NULL,
  `summary` varchar(500) NOT NULL DEFAULT '',
  `model` varchar(100) NOT NULL DEFAULT '',
  `result_status` varchar(20) NOT NULL DEFAULT 'SUCCESS',
  `reply_text` longtext NOT NULL,
  `upper_comment` longtext NOT NULL,
  `can_trace_image` varchar(500) NOT NULL DEFAULT '',
  `can_trace_image_url` varchar(500) NOT NULL DEFAULT '',
  `raw_signals` longtext NOT NULL,
  `has_commented_to_jira` tinyint(1) NOT NULL DEFAULT 0,
  `commented_at` datetime(6) DEFAULT NULL,
  `error_message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `analyzer_issueanalysisresult_task_issue_key_uniq` (`task_id`, `issue_key`),
  KEY `analyzer_issueanalysisresult_task_id_0faea8df` (`task_id`),
  CONSTRAINT `analyzer_issueanalysisresult_task_id_fk` FOREIGN KEY (`task_id`) REFERENCES `analyzer_analysistask` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyzer_filtertask` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role_index` int unsigned NOT NULL,
  `role_label` varchar(200) NOT NULL DEFAULT '',
  `jql` longtext NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `issue_count` int unsigned NOT NULL DEFAULT 0,
  `message` longtext NOT NULL,
  `error_message` longtext NOT NULL,
  `started_at` datetime(6) DEFAULT NULL,
  `finished_at` datetime(6) DEFAULT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `analyzer_filtertask_role_index_c10dc223` (`role_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyzer_filteredissuesnapshot` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `filter_task_id` bigint NOT NULL,
  `issue_key` varchar(64) NOT NULL,
  `summary` varchar(500) NOT NULL DEFAULT '',
  `assignee` varchar(200) NOT NULL DEFAULT '',
  `issue_updated_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `analyzer_filteredissuesnapshot_filter_task_issue_key_uniq` (`filter_task_id`, `issue_key`),
  KEY `analyzer_filteredissuesnapshot_filter_task_id_6e5b61a7` (`filter_task_id`),
  CONSTRAINT `analyzer_filteredissuesnapshot_filter_task_id_fk` FOREIGN KEY (`filter_task_id`) REFERENCES `analyzer_filtertask` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyzer_issueprocesstask` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `filter_task_id` bigint NOT NULL,
  `snapshot_id` bigint NOT NULL,
  `issue_key` varchar(64) NOT NULL,
  `summary` varchar(500) NOT NULL DEFAULT '',
  `status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `stage` varchar(40) NOT NULL DEFAULT 'PREPARING',
  `progress` int unsigned NOT NULL DEFAULT 0,
  `message` longtext NOT NULL,
  `error_message` longtext NOT NULL,
  `started_at` datetime(6) DEFAULT NULL,
  `finished_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `analyzer_issueprocesstask_issue_key_9caf239c` (`issue_key`),
  KEY `analyzer_issueprocesstask_filter_task_id_099dc2db` (`filter_task_id`),
  KEY `analyzer_issueprocesstask_snapshot_id_433c5ed6` (`snapshot_id`),
  CONSTRAINT `analyzer_issueprocesstask_filter_task_id_fk` FOREIGN KEY (`filter_task_id`) REFERENCES `analyzer_filtertask` (`id`) ON DELETE CASCADE,
  CONSTRAINT `analyzer_issueprocesstask_snapshot_id_fk` FOREIGN KEY (`snapshot_id`) REFERENCES `analyzer_filteredissuesnapshot` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyzer_issueprocessresult` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `process_task_id` bigint NOT NULL,
  `issue_key` varchar(64) NOT NULL,
  `summary` varchar(500) NOT NULL DEFAULT '',
  `model` varchar(100) NOT NULL DEFAULT '',
  `result_status` varchar(20) NOT NULL DEFAULT 'SUCCESS',
  `reply_text` longtext NOT NULL,
  `upper_comment` longtext NOT NULL,
  `can_trace_image` varchar(500) NOT NULL DEFAULT '',
  `can_trace_image_url` varchar(500) NOT NULL DEFAULT '',
  `raw_signals` longtext NOT NULL,
  `has_commented_to_jira` tinyint(1) NOT NULL DEFAULT 0,
  `commented_at` datetime(6) DEFAULT NULL,
  `error_message` longtext NOT NULL,
  `review_status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `review_reason` longtext NOT NULL,
  `reviewed_at` datetime(6) DEFAULT NULL,
  `review_model` varchar(100) NOT NULL DEFAULT '',
  `manual_override_after_review` tinyint(1) NOT NULL DEFAULT 0,
  `manual_error_reason` longtext NOT NULL,
  `manual_correct_result` longtext NOT NULL,
  `manual_review_saved_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `analyzer_issueprocessresult_process_task_id_uniq` (`process_task_id`),
  CONSTRAINT `analyzer_issueprocessresult_process_task_id_fk` FOREIGN KEY (`process_task_id`) REFERENCES `analyzer_issueprocesstask` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyzer_issuereviewsample` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role_index` int unsigned NOT NULL,
  `issue_key` varchar(64) NOT NULL,
  `incorrect_conclusion` longtext NOT NULL,
  `correct_conclusion` longtext NOT NULL,
  `error_reason` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `analyzer_issuereviewsample_role_index_idx` (`role_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyzer_issuelearningmemory` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role_index` int unsigned NOT NULL,
  `issue_key` varchar(64) NOT NULL,
  `review_status` varchar(20) NOT NULL DEFAULT '',
  `incorrect_conclusion` longtext NOT NULL,
  `correct_conclusion` longtext NOT NULL,
  `error_reason` longtext NOT NULL,
  `signal_summary` longtext NOT NULL,
  `memory_file_path` varchar(500) NOT NULL DEFAULT '',
  `memory_content_hash` varchar(64) NOT NULL DEFAULT '',
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `analyzer_issuelearningmemory_role_issue_uniq` (`role_index`, `issue_key`),
  KEY `analyzer_issuelearningmemory_role_index_idx` (`role_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `geely2_analyzer_jiracredentialbinding` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `project_code` varchar(32) NOT NULL DEFAULT 'geely2',
  `jira_base_url` varchar(200) NOT NULL DEFAULT 'https://boolbool.atlassian.net/',
  `jira_username` varchar(255) NOT NULL,
  `encrypted_password` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `geely2_binding_user_project_uniq` (`user_id`, `project_code`),
  KEY `geely2_binding_user_id_idx` (`user_id`),
  CONSTRAINT `geely2_binding_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `geely2_analyzer_geely2synctask` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `credential_binding_id` bigint NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `issue_count` int unsigned NOT NULL DEFAULT 0,
  `message` longtext NOT NULL,
  `error_code` varchar(64) NOT NULL DEFAULT '',
  `error_message` longtext NOT NULL,
  `started_at` datetime(6) DEFAULT NULL,
  `finished_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `geely2_synctask_user_id_idx` (`user_id`),
  KEY `geely2_synctask_binding_id_idx` (`credential_binding_id`),
  CONSTRAINT `geely2_synctask_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `geely2_synctask_binding_id_fk` FOREIGN KEY (`credential_binding_id`) REFERENCES `geely2_analyzer_jiracredentialbinding` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `geely2_analyzer_geely2issuesnapshot` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `last_sync_task_id` bigint DEFAULT NULL,
  `issue_key` varchar(64) NOT NULL,
  `summary` varchar(500) NOT NULL DEFAULT '',
  `assignee` varchar(255) NOT NULL DEFAULT '',
  `jira_updated_at` datetime(6) DEFAULT NULL,
  `current_analysis_status` varchar(20) NOT NULL DEFAULT 'IDLE',
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `geely2_snapshot_user_issue_uniq` (`user_id`, `issue_key`),
  KEY `geely2_snapshot_last_sync_task_id_idx` (`last_sync_task_id`),
  KEY `geely2_snapshot_user_id_idx` (`user_id`),
  CONSTRAINT `geely2_snapshot_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `geely2_snapshot_last_sync_task_id_fk` FOREIGN KEY (`last_sync_task_id`) REFERENCES `geely2_analyzer_geely2synctask` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `geely2_analyzer_geely2analysistask` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `credential_binding_id` bigint NOT NULL,
  `issue_snapshot_id` bigint NOT NULL,
  `issue_key` varchar(64) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `stage` varchar(64) NOT NULL DEFAULT 'FETCH_COMMENTS',
  `progress` int unsigned NOT NULL DEFAULT 0,
  `message` longtext NOT NULL,
  `error_code` varchar(64) NOT NULL DEFAULT '',
  `error_message` longtext NOT NULL,
  `workspace_dir` varchar(500) NOT NULL DEFAULT '',
  `started_at` datetime(6) DEFAULT NULL,
  `finished_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `geely2_analysistask_user_id_idx` (`user_id`),
  KEY `geely2_analysistask_binding_id_idx` (`credential_binding_id`),
  KEY `geely2_analysistask_snapshot_id_idx` (`issue_snapshot_id`),
  KEY `geely2_analysistask_issue_key_idx` (`issue_key`),
  CONSTRAINT `geely2_analysistask_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `geely2_analysistask_binding_id_fk` FOREIGN KEY (`credential_binding_id`) REFERENCES `geely2_analyzer_jiracredentialbinding` (`id`) ON DELETE CASCADE,
  CONSTRAINT `geely2_analysistask_snapshot_id_fk` FOREIGN KEY (`issue_snapshot_id`) REFERENCES `geely2_analyzer_geely2issuesnapshot` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `geely2_analyzer_geely2analysisresult` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `analysis_task_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  `issue_key` varchar(64) NOT NULL,
  `ai_summary` longtext NOT NULL,
  `reply_text` longtext NOT NULL,
  `evidence_payload` json NOT NULL,
  `confidence` double NOT NULL DEFAULT 0,
  `risk_notes` longtext NOT NULL,
  `needs_user_confirmation` tinyint(1) NOT NULL DEFAULT 1,
  `comment_status` varchar(32) NOT NULL DEFAULT 'NOT_CONFIRMED',
  `commented_at` datetime(6) DEFAULT NULL,
  `last_error` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `geely2_analysisresult_analysis_task_id_uniq` (`analysis_task_id`),
  KEY `geely2_analysisresult_user_id_idx` (`user_id`),
  CONSTRAINT `geely2_analysisresult_analysis_task_id_fk` FOREIGN KEY (`analysis_task_id`) REFERENCES `geely2_analyzer_geely2analysistask` (`id`) ON DELETE CASCADE,
  CONSTRAINT `geely2_analysisresult_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
