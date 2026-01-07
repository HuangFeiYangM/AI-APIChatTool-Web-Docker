-- ============================================
-- 数据库初始化脚本 for mysql8db
-- 版本: 2.0
-- 创建时间: 根据当前需求生成
-- ============================================

-- 1. 创建数据库（如果不存在则创建）
CREATE DATABASE IF NOT EXISTS `mysql8db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 2. 使用数据库
USE `mysql8db`;

-- 3. 创建表结构（按依赖顺序）

-- 3.1 用户表（基础表）
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(255) NOT NULL COMMENT '用户名',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
    `email` VARCHAR(255) COMMENT '邮箱',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `is_locked` BOOLEAN DEFAULT FALSE COMMENT '是否锁定',
    `locked_reason` VARCHAR(500) COMMENT '锁定原因',
    `locked_until` DATETIME COMMENT '锁定到期时间',
    `failed_login_attempts` INT DEFAULT 0 COMMENT '登录失败次数',
    `last_login_at` DATETIME COMMENT '最后登录时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `idx_username` (`username`),
    UNIQUE KEY `idx_email` (`email`),
    INDEX `idx_status` (`is_active`, `is_locked`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 3.2 系统模型配置表（基础表）
CREATE TABLE IF NOT EXISTS `system_models` (
    `model_id` INT NOT NULL AUTO_INCREMENT COMMENT '模型ID',
    `model_name` VARCHAR(50) NOT NULL COMMENT '模型名称',
    `model_provider` VARCHAR(50) NOT NULL COMMENT '模型提供商',
    `model_type` ENUM('chat', 'completion', 'embedding') DEFAULT 'chat' COMMENT '模型类型',
    `api_endpoint` VARCHAR(255) NOT NULL COMMENT 'API端点',
    `api_version` VARCHAR(20) COMMENT 'API版本',
    `is_available` BOOLEAN DEFAULT TRUE COMMENT '是否可用',
    `is_default` BOOLEAN DEFAULT FALSE COMMENT '是否默认模型',
    `rate_limit_per_minute` INT DEFAULT 60 COMMENT '每分钟请求限制',
    `max_tokens` INT DEFAULT 4096 COMMENT '最大token数',
    `description` TEXT COMMENT '模型描述',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`model_id`),
    UNIQUE KEY `idx_model_name` (`model_name`),
    INDEX `idx_provider` (`model_provider`),
    INDEX `idx_available` (`is_available`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统模型配置表';

-- 3.3 用户模型配置表
CREATE TABLE IF NOT EXISTS `user_model_configs` (
    `config_id` INT NOT NULL AUTO_INCREMENT COMMENT '配置ID',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `model_id` INT NOT NULL COMMENT '模型ID',
    `is_enabled` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `api_key` VARCHAR(500) COMMENT 'API密钥',
    `api_key_encrypted` BLOB COMMENT '加密的API密钥',
    `custom_endpoint` VARCHAR(255) COMMENT '自定义端点',
    `max_tokens` INT COMMENT '自定义最大token数',
    `temperature` DECIMAL(3,2) DEFAULT 0.7 COMMENT '温度参数',
    `priority` INT DEFAULT 0 COMMENT '优先级',
    `last_used_at` DATETIME COMMENT '最后使用时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`config_id`),
    UNIQUE KEY `idx_user_model` (`user_id`, `model_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`model_id`) REFERENCES `system_models`(`model_id`) ON DELETE CASCADE,
    INDEX `idx_user_enabled` (`user_id`, `is_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户模型配置表';

-- 3.4 对话表
CREATE TABLE IF NOT EXISTS `conversations` (
    `conversation_id` INT NOT NULL AUTO_INCREMENT COMMENT '对话ID',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `title` VARCHAR(200) COMMENT '对话标题',
    `model_id` INT NOT NULL COMMENT '使用的模型ID',
    `total_tokens` INT DEFAULT 0 COMMENT '总token数',
    `message_count` INT DEFAULT 0 COMMENT '消息数量',
    `is_archived` BOOLEAN DEFAULT FALSE COMMENT '是否归档',
    `is_deleted` BOOLEAN DEFAULT FALSE COMMENT '是否删除',
    `deleted_at` DATETIME COMMENT '删除时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`conversation_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`model_id`) REFERENCES `system_models`(`model_id`) ON DELETE RESTRICT,
    INDEX `idx_user_created` (`user_id`, `created_at`),
    INDEX `idx_user_status` (`user_id`, `is_deleted`, `is_archived`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话表';

-- 3.5 消息表
CREATE TABLE IF NOT EXISTS `messages` (
    `message_id` INT NOT NULL AUTO_INCREMENT COMMENT '消息ID',
    `conversation_id` INT NOT NULL COMMENT '对话ID',
    `role` ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色',
    `content` MEDIUMTEXT NOT NULL COMMENT '消息内容',
    `tokens_used` INT DEFAULT 0 COMMENT '使用的token数',
    `model_id` INT COMMENT '使用的模型ID',
    `is_deleted` BOOLEAN DEFAULT FALSE COMMENT '是否删除',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`message_id`),
    FOREIGN KEY (`conversation_id`) REFERENCES `conversations`(`conversation_id`) ON DELETE CASCADE,
    FOREIGN KEY (`model_id`) REFERENCES `system_models`(`model_id`) ON DELETE SET NULL,
    INDEX `idx_conversation_created` (`conversation_id`, `created_at`),
    FULLTEXT INDEX `idx_content` (`content`(1000)) COMMENT '全文索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

-- 3.6 API调用日志表
CREATE TABLE IF NOT EXISTS `api_call_logs` (
    `log_id` INT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `model_id` INT NOT NULL COMMENT '模型ID',
    `conversation_id` INT COMMENT '对话ID',
    `endpoint` VARCHAR(255) NOT NULL COMMENT '调用端点',
    `request_tokens` INT DEFAULT 0 COMMENT '请求token数',
    `response_tokens` INT DEFAULT 0 COMMENT '响应token数',
    `total_tokens` INT DEFAULT 0 COMMENT '总token数',
    `response_time_ms` INT COMMENT '响应时间(毫秒)',
    `status_code` INT COMMENT '状态码',
    `is_success` BOOLEAN DEFAULT TRUE COMMENT '是否成功',
    `error_message` TEXT COMMENT '错误信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`log_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`model_id`) REFERENCES `system_models`(`model_id`) ON DELETE CASCADE,
    FOREIGN KEY (`conversation_id`) REFERENCES `conversations`(`conversation_id`) ON DELETE SET NULL,
    INDEX `idx_user_model_time` (`user_id`, `model_id`, `created_at`),
    INDEX `idx_success_rate` (`model_id`, `is_success`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API调用日志表';

-- 3.7 登录尝试表
CREATE TABLE IF NOT EXISTS `login_attempts` (
    `attempt_id` INT NOT NULL AUTO_INCREMENT COMMENT '尝试ID',
    `username` VARCHAR(255) NOT NULL COMMENT '用户名',
    `ip_address` VARCHAR(45) NOT NULL COMMENT 'IP地址',
    `user_agent` TEXT COMMENT '用户代理',
    `is_success` BOOLEAN DEFAULT FALSE COMMENT '是否成功',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`attempt_id`),
    INDEX `idx_username_time` (`username`, `created_at`),
    INDEX `idx_ip_time` (`ip_address`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录尝试表';

-- 4. 插入初始化数据

-- 4.1 插入默认模型配置
INSERT IGNORE INTO `system_models` (`model_name`, `model_provider`, `model_type`, `api_endpoint`, `api_version`, `is_default`, `description`) VALUES
('gpt-3.5-turbo', 'OpenAI', 'chat', 'https://api.openai.com/v1/chat/completions', 'v1', TRUE, 'OpenAI GPT-3.5 Turbo模型'),
('gpt-4', 'OpenAI', 'chat', 'https://api.openai.com/v1/chat/completions', 'v1', FALSE, 'OpenAI GPT-4模型'),
('deepseek-chat', 'DeepSeek', 'chat', 'https://api.deepseek.com/chat/completions', 'v1', FALSE, 'DeepSeek Chat模型'),
('deepseek-coder', 'DeepSeek', 'chat', 'https://api.deepseek.com/chat/completions', 'v1', FALSE, 'DeepSeek Coder模型'),
('ernie-bot', 'Baidu', 'chat', 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions', 'v2', FALSE, '百度文心一言模型'),
('claude-3-sonnet', 'Anthropic', 'chat', 'https://api.anthropic.com/v1/messages', '2023-06-01', FALSE, 'Anthropic Claude 3 Sonnet模型'),
('llama-3-8b', 'Meta', 'chat', 'https://api.replicate.com/v1/predictions', 'v1', FALSE, 'Meta Llama 3 8B模型');

-- 4.2 创建管理员用户
-- 注意：这里的密码哈希是占位符，实际使用时请替换为真实密码的bcrypt哈希值
-- 默认密码：admin123，需要替换$2b$12$YourBcryptHashHere为实际哈希值
INSERT IGNORE INTO `users` (`username`, `password_hash`, `email`, `is_active`, `is_locked`) 
VALUES ('admin', '$12$7CtiYRO9u0P84zPOceQE5ev/UDG2FqwH4jFGf/Q4E2Sg8IYH7iKoy', '1552472225@qq.com', TRUE, FALSE);

-- 5. 创建额外的索引（优化查询性能）
ALTER TABLE `conversations` ADD INDEX IF NOT EXISTS `idx_user_model_time` (`user_id`, `model_id`, `created_at`);
ALTER TABLE `messages` ADD INDEX IF NOT EXISTS `idx_role_conversation` (`role`, `conversation_id`);
ALTER TABLE `user_model_configs` ADD INDEX IF NOT EXISTS `idx_enabled_priority` (`is_enabled`, `priority`);
ALTER TABLE `api_call_logs` ADD INDEX IF NOT EXISTS `idx_date_success` (`created_at`, `is_success`);

-- 6. 创建存储过程和函数

-- 6.1 删除已存在的存储过程（确保可以重新创建）
DROP PROCEDURE IF EXISTS `lock_user_account`;
DROP PROCEDURE IF EXISTS `unlock_expired_accounts`;

-- 6.2 用户锁定/解锁存储过程
DELIMITER //

CREATE PROCEDURE `lock_user_account`(
    IN p_user_id INT,
    IN p_reason VARCHAR(500),
    IN p_lock_hours INT
)
BEGIN
    UPDATE `users` 
    SET `is_locked` = TRUE,
        `locked_reason` = p_reason,
        `locked_until` = DATE_ADD(NOW(), INTERVAL p_lock_hours HOUR),
        `updated_at` = NOW()
    WHERE `user_id` = p_user_id;
END //

-- 6.3 自动解锁过期账户的存储过程
CREATE PROCEDURE `unlock_expired_accounts`()
BEGIN
    UPDATE `users` 
    SET `is_locked` = FALSE,
        `locked_reason` = NULL,
        `locked_until` = NULL,
        `failed_login_attempts` = 0,
        `updated_at` = NOW()
    WHERE `is_locked` = TRUE 
    AND `locked_until` IS NOT NULL 
    AND `locked_until` < NOW();
END //

DELIMITER ;

-- ============================================
-- 初始化完成
-- 数据库: mysql8db
-- 表数量: 7
-- 存储过程: 2
-- ============================================
