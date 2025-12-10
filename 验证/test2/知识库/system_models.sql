/*
 Navicat Premium Dump SQL

 Source Server         : mysql8.0-本地
 Source Server Type    : MySQL
 Source Server Version : 80043 (8.0.43)
 Source Host           : localhost:3309
 Source Schema         : testdb1

 Target Server Type    : MySQL
 Target Server Version : 80043 (8.0.43)
 File Encoding         : 65001

 Date: 30/01/2008 02:54:55
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for system_models
-- ----------------------------
DROP TABLE IF EXISTS `system_models`;
CREATE TABLE `system_models`  (
  `model_id` int NOT NULL AUTO_INCREMENT COMMENT '模型ID',
  `model_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型名称',
  `model_provider` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型提供商',
  `model_type` enum('chat','completion','embedding') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'chat' COMMENT '模型类型',
  `api_endpoint` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'API端点',
  `api_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'API版本',
  `is_available` tinyint(1) NULL DEFAULT 1 COMMENT '是否可用',
  `is_default` tinyint(1) NULL DEFAULT 0 COMMENT '是否默认模型',
  `rate_limit_per_minute` int NULL DEFAULT 60 COMMENT '每分钟请求限制',
  `max_tokens` int NULL DEFAULT 4096 COMMENT '最大token数',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '模型描述',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`model_id`) USING BTREE,
  UNIQUE INDEX `idx_model_name`(`model_name` ASC) USING BTREE,
  INDEX `idx_provider`(`model_provider` ASC) USING BTREE,
  INDEX `idx_available`(`is_available` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统模型配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of system_models
-- ----------------------------
INSERT INTO `system_models` VALUES (1, 'gpt-3.5-turbo', 'OpenAI', 'chat', 'https://api.openai.com/v1/chat/completions', 'v1', 1, 1, 60, 4096, 'OpenAI GPT-3.5 Turbo模型', '2025-12-01 07:35:40', '2025-12-01 07:35:40');
INSERT INTO `system_models` VALUES (2, 'gpt-4', 'OpenAI', 'chat', 'https://api.openai.com/v1/chat/completions', 'v1', 1, 0, 60, 4096, 'OpenAI GPT-4模型', '2025-12-01 07:35:40', '2025-12-01 07:35:40');
INSERT INTO `system_models` VALUES (3, 'deepseek-chat', 'DeepSeek', 'chat', 'https://api.deepseek.com/chat/completions', 'v1', 1, 0, 60, 4096, 'DeepSeek Chat模型', '2025-12-01 07:35:40', '2025-12-01 07:35:40');
INSERT INTO `system_models` VALUES (4, 'deepseek-coder', 'DeepSeek', 'chat', 'https://api.deepseek.com/chat/completions', 'v1', 1, 0, 60, 4096, 'DeepSeek Coder模型', '2025-12-01 07:35:40', '2025-12-01 07:35:40');
INSERT INTO `system_models` VALUES (5, 'ernie-bot', 'Baidu', 'chat', 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions', 'v2', 1, 0, 60, 4096, '百度文心一言模型', '2025-12-01 07:35:40', '2025-12-01 07:35:40');
INSERT INTO `system_models` VALUES (6, 'claude-3-sonnet', 'Anthropic', 'chat', 'https://api.anthropic.com/v1/messages', '2023-06-01', 1, 0, 60, 4096, 'Anthropic Claude 3 Sonnet模型', '2025-12-01 07:35:40', '2025-12-01 07:35:40');
INSERT INTO `system_models` VALUES (7, 'llama-3-8b', 'Meta', 'chat', 'https://api.replicate.com/v1/predictions', 'v1', 1, 0, 60, 4096, 'Meta Llama 3 8B模型', '2025-12-01 07:35:40', '2025-12-01 07:35:40');
INSERT INTO `system_models` VALUES (8, 'gpt-3.5-turbo-16k', 'OpenAI', 'chat', 'https://api.openai.com/v1/chat/completions', 'v1', 1, 0, 120, 16384, 'OpenAI GPT-3.5 Turbo 16K上下文版本', '2025-12-01 08:13:56', '2025-12-01 08:13:56');
INSERT INTO `system_models` VALUES (9, 'gpt-4-turbo', 'OpenAI', 'chat', 'https://api.openai.com/v1/chat/completions', 'v1', 1, 0, 30, 128000, 'OpenAI GPT-4 Turbo模型', '2025-12-01 08:13:56', '2025-12-01 08:13:56');
INSERT INTO `system_models` VALUES (10, 'claude-3-haiku', 'Anthropic', 'chat', 'https://api.anthropic.com/v1/messages', '2023-06-01', 1, 0, 100, 200000, 'Anthropic Claude 3 Haiku模型（快速）', '2025-12-01 08:13:56', '2025-12-01 08:13:56');
INSERT INTO `system_models` VALUES (11, 'claude-3-opus', 'Anthropic', 'chat', 'https://api.anthropic.com/v1/messages', '2023-06-01', 1, 0, 10, 200000, 'Anthropic Claude 3 Opus模型（最强）', '2025-12-01 08:13:56', '2025-12-01 08:13:56');
INSERT INTO `system_models` VALUES (12, 'llama-3-70b', 'Meta', 'chat', 'https://api.replicate.com/v1/predictions', 'v1', 1, 0, 20, 8192, 'Meta Llama 3 70B模型', '2025-12-01 08:13:56', '2025-12-01 08:13:56');
INSERT INTO `system_models` VALUES (13, 'text-embedding-ada-002', 'OpenAI', 'embedding', 'https://api.openai.com/v1/embeddings', 'v1', 1, 0, 3000, 8191, 'OpenAI文本嵌入模型', '2025-12-01 08:13:56', '2025-12-01 08:13:56');
INSERT INTO `system_models` VALUES (14, 'text-davinci-003', 'OpenAI', 'completion', 'https://api.openai.com/v1/completions', 'v1', 1, 0, 60, 4097, 'OpenAI文本补全模型', '2025-12-01 08:13:56', '2025-12-01 08:13:56');

SET FOREIGN_KEY_CHECKS = 1;
