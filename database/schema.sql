-- AI Voice Bot Database Schema
-- Auto-generated

CREATE DATABASE IF NOT EXISTS ai_voice_bot_new;
USE ai_voice_bot_new;

-- Table: answer
DROP TABLE IF EXISTS answer;
CREATE TABLE `answer` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question_id` int NOT NULL,
  `text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `answer_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `question` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: department
DROP TABLE IF EXISTS department;
CREATE TABLE `department` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: department_new
DROP TABLE IF EXISTS department_new;
CREATE TABLE `department_new` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: department_topic_mapping
DROP TABLE IF EXISTS department_topic_mapping;
CREATE TABLE `department_topic_mapping` (
  `id` int NOT NULL AUTO_INCREMENT,
  `department_id` int NOT NULL,
  `topic_id` int NOT NULL,
  `is_mandatory` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_mapping` (`department_id`,`topic_id`),
  KEY `topic_id` (`topic_id`),
  CONSTRAINT `department_topic_mapping_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `department_new` (`id`),
  CONSTRAINT `department_topic_mapping_ibfk_2` FOREIGN KEY (`topic_id`) REFERENCES `training_topic` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=187 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: employee
DROP TABLE IF EXISTS employee;
CREATE TABLE `employee` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `machine` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `employee_id` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `full_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `father_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `department` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `designation` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_img` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `line_unit` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_of_joining` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mobile_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reporting_head` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1477 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: employee_new
DROP TABLE IF EXISTS employee_new;
CREATE TABLE `employee_new` (
  `id` int NOT NULL AUTO_INCREMENT,
  `emp_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department_id` int DEFAULT NULL,
  `designation` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `join_date` date DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `emp_id` (`emp_id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `employee_new_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `department_new` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: machine
DROP TABLE IF EXISTS machine;
CREATE TABLE `machine` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sub_department_id` int DEFAULT NULL,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'General',
  `code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: machine_training
DROP TABLE IF EXISTS machine_training;
CREATE TABLE `machine_training` (
  `id` int NOT NULL AUTO_INCREMENT,
  `machine_id` int NOT NULL,
  `good_examples` text COLLATE utf8mb4_unicode_ci,
  `bad_examples` text COLLATE utf8mb4_unicode_ci,
  `instructions` text COLLATE utf8mb4_unicode_ci,
  `question_style` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'technical',
  `preferred_language` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'Hindi',
  `difficulty_focus` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'mixed',
  `total_corrections` int DEFAULT '0',
  `last_trained_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `machine_id` (`machine_id`),
  CONSTRAINT `machine_training_ibfk_1` FOREIGN KEY (`machine_id`) REFERENCES `machine` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: qa_bank
DROP TABLE IF EXISTS qa_bank;
CREATE TABLE `qa_bank` (
  `id` int NOT NULL AUTO_INCREMENT,
  `machine_id` int NOT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `expected_answer` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` int DEFAULT '1',
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT 'General',
  `keywords` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `language` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'Hindi',
  `is_active` tinyint(1) DEFAULT '1',
  `times_asked` int DEFAULT '0',
  `times_correct` int DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `machine_id` (`machine_id`),
  CONSTRAINT `qa_bank_ibfk_1` FOREIGN KEY (`machine_id`) REFERENCES `machine` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: qa_bank_new
DROP TABLE IF EXISTS qa_bank_new;
CREATE TABLE `qa_bank_new` (
  `id` int NOT NULL AUTO_INCREMENT,
  `topic_id` int NOT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `expected_answer` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` int DEFAULT '1' COMMENT '1=Easy, 2=Medium, 3=Hard',
  `language` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'Hindi',
  `keywords` text COLLATE utf8mb4_unicode_ci,
  `times_asked` int DEFAULT '0',
  `times_correct` int DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `topic_id` (`topic_id`),
  CONSTRAINT `qa_bank_new_ibfk_1` FOREIGN KEY (`topic_id`) REFERENCES `training_topic` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=566 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: question
DROP TABLE IF EXISTS question;
CREATE TABLE `question` (
  `id` int NOT NULL AUTO_INCREMENT,
  `machine_id` int NOT NULL,
  `text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `machine_id` (`machine_id`),
  CONSTRAINT `question_ibfk_1` FOREIGN KEY (`machine_id`) REFERENCES `machine` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: score
DROP TABLE IF EXISTS score;
CREATE TABLE `score` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int DEFAULT NULL,
  `score` int DEFAULT NULL,
  `passed` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `score_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: study_material
DROP TABLE IF EXISTS study_material;
CREATE TABLE `study_material` (
  `id` int NOT NULL AUTO_INCREMENT,
  `machine_id` int NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `machine_id` (`machine_id`),
  CONSTRAINT `study_material_ibfk_1` FOREIGN KEY (`machine_id`) REFERENCES `machine` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: sub_department
DROP TABLE IF EXISTS sub_department;
CREATE TABLE `sub_department` (
  `id` int NOT NULL AUTO_INCREMENT,
  `department_id` int NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `sub_department_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: training_category
DROP TABLE IF EXISTS training_category;
CREATE TABLE `training_category` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: training_record
DROP TABLE IF EXISTS training_record;
CREATE TABLE `training_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `topic_id` int NOT NULL,
  `training_date` date NOT NULL,
  `trainer_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `training_type` enum('New Joiner','Refresher','Upgrade') COLLATE utf8mb4_unicode_ci DEFAULT 'New Joiner',
  `status` enum('Completed','Pending Viva','Passed','Failed') COLLATE utf8mb4_unicode_ci DEFAULT 'Completed',
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  KEY `topic_id` (`topic_id`),
  CONSTRAINT `training_record_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employee_new` (`id`),
  CONSTRAINT `training_record_ibfk_2` FOREIGN KEY (`topic_id`) REFERENCES `training_topic` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: training_topic
DROP TABLE IF EXISTS training_topic;
CREATE TABLE `training_topic` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `category_id` int DEFAULT NULL,
  `is_common` tinyint(1) DEFAULT '0',
  `duration_hours` decimal(4,1) DEFAULT '1.0',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `training_topic_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `training_category` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: viva_level
DROP TABLE IF EXISTS viva_level;
CREATE TABLE `viva_level` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` int NOT NULL,
  `level` int NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `questions_count` int DEFAULT NULL,
  `correct_answers` int DEFAULT NULL,
  `score` float DEFAULT NULL,
  `passing_threshold` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `viva_level_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `viva_session` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: viva_question
DROP TABLE IF EXISTS viva_question;
CREATE TABLE `viva_question` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` int NOT NULL,
  `question_id` int DEFAULT NULL,
  `level` int NOT NULL,
  `question_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `expected_answer` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_answer` text COLLATE utf8mb4_unicode_ci,
  `audio_file_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `score` float DEFAULT NULL,
  `is_correct` tinyint(1) DEFAULT NULL,
  `time_taken` int DEFAULT NULL,
  `asked_at` datetime DEFAULT NULL,
  `answered_at` datetime DEFAULT NULL,
  `is_ai_generated` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `session_id` (`session_id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `viva_question_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `viva_session` (`id`),
  CONSTRAINT `viva_question_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `question` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: viva_records
DROP TABLE IF EXISTS viva_records;
CREATE TABLE `viva_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `employee_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `department` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `designation` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `topic_id` int DEFAULT NULL,
  `topic_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_questions` int DEFAULT '0',
  `correct_answers` int DEFAULT '0',
  `partial_answers` int DEFAULT '0',
  `wrong_answers` int DEFAULT '0',
  `score_percent` decimal(5,2) DEFAULT '0.00',
  `result` enum('Pass','Fail','Pending') COLLATE utf8mb4_unicode_ci DEFAULT 'Pending',
  `video_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `answers_json` longtext COLLATE utf8mb4_unicode_ci,
  `language` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'Hindi',
  `duration_seconds` int DEFAULT '0',
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_employee` (`employee_id`),
  KEY `idx_topic` (`topic_id`),
  KEY `idx_date` (`completed_at`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: viva_result_new
DROP TABLE IF EXISTS viva_result_new;
CREATE TABLE `viva_result_new` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `employee_id` int NOT NULL,
  `topic_id` int NOT NULL,
  `total_questions` int NOT NULL,
  `correct_answers` int NOT NULL,
  `total_score` int NOT NULL,
  `percentage` decimal(5,2) NOT NULL,
  `grade` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `passed` tinyint(1) NOT NULL,
  `detailed_results` json DEFAULT NULL,
  `evaluated_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remarks` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  KEY `topic_id` (`topic_id`),
  CONSTRAINT `viva_result_new_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employee_new` (`id`),
  CONSTRAINT `viva_result_new_ibfk_2` FOREIGN KEY (`topic_id`) REFERENCES `training_topic` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: viva_session
DROP TABLE IF EXISTS viva_session;
CREATE TABLE `viva_session` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `machine_id` int NOT NULL,
  `current_level` int DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `total_score` float DEFAULT NULL,
  `level_1_score` float DEFAULT NULL,
  `level_2_score` float DEFAULT NULL,
  `level_3_score` float DEFAULT NULL,
  `questions_attempted` int DEFAULT NULL,
  `questions_correct` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  KEY `machine_id` (`machine_id`),
  CONSTRAINT `viva_session_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employee` (`id`),
  CONSTRAINT `viva_session_ibfk_2` FOREIGN KEY (`machine_id`) REFERENCES `machine` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: viva_session_new
DROP TABLE IF EXISTS viva_session_new;
CREATE TABLE `viva_session_new` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `employee_id` int NOT NULL,
  `topic_id` int NOT NULL,
  `training_record_id` int DEFAULT NULL,
  `total_questions` int DEFAULT '20',
  `answered_questions` int DEFAULT '0',
  `status` enum('Active','Completed','Abandoned') COLLATE utf8mb4_unicode_ci DEFAULT 'Active',
  `started_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `completed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `session_id` (`session_id`),
  KEY `employee_id` (`employee_id`),
  KEY `topic_id` (`topic_id`),
  KEY `training_record_id` (`training_record_id`),
  CONSTRAINT `viva_session_new_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employee_new` (`id`),
  CONSTRAINT `viva_session_new_ibfk_2` FOREIGN KEY (`topic_id`) REFERENCES `training_topic` (`id`),
  CONSTRAINT `viva_session_new_ibfk_3` FOREIGN KEY (`training_record_id`) REFERENCES `training_record` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

