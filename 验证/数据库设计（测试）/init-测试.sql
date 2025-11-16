-- 创建数据库（可根据需要修改数据库名）
CREATE DATABASE IF NOT EXISTS `test_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `test_db`;

-- 创建用户储存表
CREATE TABLE IF NOT EXISTS `user_storage` (
    `user` VARCHAR(255) NOT NULL COMMENT '用户名',
    `password` VARCHAR(255) NOT NULL COMMENT '密码',
    `deepseek_bool` BOOLEAN DEFAULT FALSE COMMENT '是否启用DeepSeek',
    `deepseek_api` VARCHAR(500) COMMENT 'DeepSeek API密钥或URL',
    PRIMARY KEY (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户储存表';

-- 创建对话储存表
CREATE TABLE IF NOT EXISTS `conversation_storage` (
    `id_conversation` INT NOT NULL COMMENT '对话ID',
    `id_part` INT NOT NULL COMMENT '对话部分ID',
    `user` VARCHAR(255) NOT NULL COMMENT '用户名（外键引用user_storage表）',
    `markdown` LONGTEXT COMMENT 'Markdown内容',
    PRIMARY KEY (`id_conversation`, `id_part`),
    FOREIGN KEY (`user`) REFERENCES `user_storage`(`user`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话储存表';
