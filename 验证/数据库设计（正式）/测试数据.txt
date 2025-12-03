-- ============================================
-- 1. 用户表测试数据
-- ============================================
INSERT INTO `users` (`username`, `password_hash`, `email`, `is_active`, `is_locked`, `failed_login_attempts`, `last_login_at`) VALUES
-- 管理员用户（密码：Admin@123）
('admin', '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqh6W4qRZtAe8eFJWY9WQOq', 'admin@example.com', TRUE, FALSE, 0, '2024-01-15 10:30:00'),

-- 普通用户（密码：User@123）
('alice', '$2a$12$KjHf8dN7pQaVvLzT5XrB3uM9qW2sP4yR6tA7bC8dE9fG0hI1jK2lM3', 'alice@example.com', TRUE, FALSE, 0, '2024-01-16 14:20:00'),
('bob', '$2a$12$NpO8qR2sT4uV6wX8yZ0A1bC3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3x', 'bob@example.com', TRUE, FALSE, 0, '2024-01-17 09:15:00'),

-- 测试用户 - 已锁定
('charlie', '$2a$12$PqR8sT0uV2wX4yZ6A1bC3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY', 'charlie@example.com', TRUE, TRUE, 5, '2024-01-14 16:45:00'),

-- 测试用户 - 已禁用
('david', '$2a$12$QrS9tU1vW3xY5z7B2cD4eF6gH8jK0lM2nO4pQ6rS8tU0vW2xY4z6A1', 'david@example.com', FALSE, FALSE, 0, '2024-01-13 11:10:00'),

-- 开发者用户
('developer', '$2a$12$RrS8tU0vW2xY4z6A1bC3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5', 'dev@example.com', TRUE, FALSE, 0, '2024-01-18 13:25:00');

-- ============================================
-- 2. 系统模型配置表测试数据（补充）
-- ============================================
INSERT INTO `system_models` (`model_name`, `model_provider`, `model_type`, `api_endpoint`, `api_version`, `is_default`, `is_available`, `rate_limit_per_minute`, `max_tokens`, `description`) VALUES
-- 补充一些测试模型
('gpt-3.5-turbo-16k', 'OpenAI', 'chat', 'https://api.openai.com/v1/chat/completions', 'v1', FALSE, TRUE, 120, 16384, 'OpenAI GPT-3.5 Turbo 16K上下文版本'),
('gpt-4-turbo', 'OpenAI', 'chat', 'https://api.openai.com/v1/chat/completions', 'v1', FALSE, TRUE, 30, 128000, 'OpenAI GPT-4 Turbo模型'),
('claude-3-haiku', 'Anthropic', 'chat', 'https://api.anthropic.com/v1/messages', '2023-06-01', FALSE, TRUE, 100, 200000, 'Anthropic Claude 3 Haiku模型（快速）'),
('claude-3-opus', 'Anthropic', 'chat', 'https://api.anthropic.com/v1/messages', '2023-06-01', FALSE, TRUE, 10, 200000, 'Anthropic Claude 3 Opus模型（最强）'),
('llama-3-70b', 'Meta', 'chat', 'https://api.replicate.com/v1/predictions', 'v1', FALSE, TRUE, 20, 8192, 'Meta Llama 3 70B模型'),
('text-embedding-ada-002', 'OpenAI', 'embedding', 'https://api.openai.com/v1/embeddings', 'v1', FALSE, TRUE, 3000, 8191, 'OpenAI文本嵌入模型'),
('text-davinci-003', 'OpenAI', 'completion', 'https://api.openai.com/v1/completions', 'v1', FALSE, TRUE, 60, 4097, 'OpenAI文本补全模型');

-- ============================================
-- 3. 用户模型配置表测试数据
-- ============================================
-- 获取模型ID（假设已有数据）
SET @gpt35_id = (SELECT model_id FROM system_models WHERE model_name = 'gpt-3.5-turbo');
SET @gpt4_id = (SELECT model_id FROM system_models WHERE model_name = 'gpt-4');
SET @deepseek_id = (SELECT model_id FROM system_models WHERE model_name = 'deepseek-chat');
SET @claude_id = (SELECT model_id FROM system_models WHERE model_name = 'claude-3-sonnet');

-- 获取用户ID
SET @admin_id = (SELECT user_id FROM users WHERE username = 'admin');
SET @alice_id = (SELECT user_id FROM users WHERE username = 'alice');
SET @bob_id = (SELECT user_id FROM users WHERE username = 'bob');
SET @dev_id = (SELECT user_id FROM users WHERE username = 'developer');

INSERT INTO `user_model_configs` (`user_id`, `model_id`, `is_enabled`, `api_key`, `temperature`, `priority`, `last_used_at`) VALUES
-- 管理员配置（使用所有模型）
(@admin_id, @gpt35_id, TRUE, 'sk-admin-gpt35-123456', 0.7, 10, '2024-01-18 10:30:00'),
(@admin_id, @gpt4_id, TRUE, 'sk-admin-gpt4-789012', 0.8, 20, '2024-01-18 11:45:00'),
(@admin_id, @deepseek_id, TRUE, 'sk-admin-deepseek-345678', 0.6, 5, '2024-01-17 14:20:00'),

-- Alice配置（主要用GPT-3.5）
(@alice_id, @gpt35_id, TRUE, 'sk-alice-gpt35-abcdef', 0.9, 15, '2024-01-18 09:15:00'),
(@alice_id, @claude_id, TRUE, 'sk-alice-claude-ghijkl', 0.5, 10, '2024-01-17 16:30:00'),

-- Bob配置（只用免费模型）
(@bob_id, @deepseek_id, TRUE, 'sk-bob-deepseek-mnopqr', 0.7, 10, '2024-01-18 13:45:00'),

-- 开发者配置（测试各种参数）
(@dev_id, @gpt35_id, TRUE, 'sk-dev-gpt35-stuvwx', 0.3, 5, '2024-01-18 08:20:00'),
(@dev_id, @gpt4_id, TRUE, 'sk-dev-gpt4-yzabcd', 1.2, 15, '2024-01-18 12:10:00'),
(@dev_id, @claude_id, FALSE, 'sk-dev-claude-efghij', 0.7, 0, NULL);  -- 禁用状态

-- ============================================
-- 4. 对话表测试数据
-- ============================================
INSERT INTO `conversations` (`user_id`, `title`, `model_id`, `total_tokens`, `message_count`, `is_archived`, `created_at`) VALUES
-- 管理员对话
(@admin_id, '系统配置讨论', @gpt4_id, 2450, 8, FALSE, '2024-01-15 10:00:00'),
(@admin_id, 'API接口设计', @gpt35_id, 1200, 5, FALSE, '2024-01-16 14:30:00'),
(@admin_id, '旧项目归档', @deepseek_id, 850, 3, TRUE, '2024-01-10 09:15:00'),

-- Alice对话
(@alice_id, 'Python学习', @gpt35_id, 3200, 12, FALSE, '2024-01-16 09:00:00'),
(@alice_id, '数据分析问题', @claude_id, 1800, 7, FALSE, '2024-01-17 11:20:00'),
(@alice_id, '周末计划讨论', @gpt35_id, 450, 2, FALSE, '2024-01-18 08:45:00'),

-- Bob对话
(@bob_id, '代码调试帮助', @deepseek_id, 5600, 15, FALSE, '2024-01-17 13:00:00'),
(@bob_id, '学习算法', @deepseek_id, 2900, 9, FALSE, '2024-01-18 10:30:00'),

-- 开发者对话
(@dev_id, '温度参数测试', @gpt35_id, 800, 4, FALSE, '2024-01-18 08:00:00'),
(@dev_id, '长上下文测试', @gpt4_id, 12500, 6, FALSE, '2024-01-18 11:00:00');

-- ============================================
-- 5. 消息表测试数据
-- ============================================
-- 获取对话ID
SET @conv1_id = (SELECT conversation_id FROM conversations WHERE title = 'Python学习' AND user_id = @alice_id);
SET @conv2_id = (SELECT conversation_id FROM conversations WHERE title = '代码调试帮助' AND user_id = @bob_id);
SET @conv3_id = (SELECT conversation_id FROM conversations WHERE title = '系统配置讨论' AND user_id = @admin_id);
SET @conv4_id = (SELECT conversation_id FROM conversations WHERE title = '温度参数测试' AND user_id = @dev_id);

-- 对话1：Python学习（Alice）
INSERT INTO `messages` (`conversation_id`, `role`, `content`, `tokens_used`, `model_id`, `created_at`) VALUES
(@conv1_id, 'user', '你好，我想学习Python，应该从哪里开始？', 15, NULL, '2024-01-16 09:00:00'),
(@conv1_id, 'assistant', '学习Python可以从以下几个方面开始：\n\n1. **基础语法**：变量、数据类型、控制流\n2. **函数和模块**：如何组织代码\n3. **面向对象编程**：类、对象、继承\n4. **常用库**：requests、pandas、numpy等\n\n建议先安装Python环境，然后找一个好的教程系统学习。', 120, @gpt35_id, '2024-01-16 09:00:30'),
(@conv1_id, 'user', '能给我一个简单的Python代码示例吗？比如计算斐波那契数列', 12, NULL, '2024-01-16 09:01:00'),
(@conv1_id, 'assistant', '当然可以！这是一个计算斐波那契数列的Python函数：\n\n```python\ndef fibonacci(n):\n    """计算斐波那契数列的第n项"""\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    else:\n        a, b = 0, 1\n        for _ in range(2, n + 1):\n            a, b = b, a + b\n        return b\n\n# 测试\nprint(fibonacci(10))  # 输出：55\nprint(fibonacci(20))  # 输出：6765\n```\n\n这个函数使用迭代方式计算，效率较高。', 180, @gpt35_id, '2024-01-16 09:01:30');

-- 对话2：代码调试帮助（Bob）
INSERT INTO `messages` (`conversation_id`, `role`, `content`, `tokens_used`, `model_id`, `created_at`) VALUES
(@conv2_id, 'user', '我的JavaScript代码有错误，能帮我看看吗？\n\n```javascript\nfunction calculateTotal(items) {\n    let total = 0;\n    for (let i = 0; i < items.length; i++) {\n        total += items[i].price * items[i].quantity;\n    }\n    return total;\n}\n\nconst cart = [\n    { name: "Apple", price: 1.5, quantity: 3 },\n    { name: "Banana", price: 0.8, quantity: 5 }\n];\n\nconsole.log("Total:", calculateTotal(cart));\n```', 85, NULL, '2024-01-17 13:00:00'),
(@conv2_id, 'assistant', '你的代码看起来是正确的！让我运行一下看看...\n\n实际上，这段代码应该能正常工作。输出应该是：\n```\nTotal: 8.5\n```\n\n计算过程：\n- Apple: 1.5 * 3 = 4.5\n- Banana: 0.8 * 5 = 4.0\n- Total: 4.5 + 4.0 = 8.5\n\n如果你遇到了错误，可能是其他部分的代码有问题。你能告诉我具体的错误信息吗？', 150, @deepseek_id, '2024-01-17 13:00:45'),
(@conv2_id, 'user', '错误信息是：ReferenceError: items is not defined', 8, NULL, '2024-01-17 13:01:30'),
(@conv2_id, 'assistant', '这个错误说明 `items` 变量未定义。可能的原因：\n\n1. **函数调用问题**：确保正确调用了 `calculateTotal` 函数\n2. **变量作用域**：检查 `items` 是否在函数作用域内\n3. **拼写错误**：确认变量名拼写正确\n\n请检查调用函数的地方，确保传递了正确的参数。', 95, @deepseek_id, '2024-01-17 13:02:00');

-- 对话3：系统配置讨论（Admin）
INSERT INTO `messages` (`conversation_id`, `role`, `content`, `tokens_used`, `model_id`, `created_at`) VALUES
(@conv3_id, 'user', '我们需要设计一个多模型AI平台的数据库架构，有什么建议？', 18, NULL, '2024-01-15 10:00:00'),
(@conv3_id, 'assistant', '设计多模型AI平台数据库时，建议考虑以下核心表：\n\n1. **用户表**：管理用户账户和权限\n2. **模型配置表**：存储不同AI模型的API配置\n3. **对话表**：记录用户的对话会话\n4. **消息表**：存储具体的对话消息\n5. **API日志表**：监控API调用情况\n\n关键设计点：\n- 支持多种模型提供商（OpenAI、DeepSeek、Claude等）\n- 用户级API密钥管理\n- 对话上下文管理\n- 使用统计和计费', 210, @gpt4_id, '2024-01-15 10:00:40'),
(@conv3_id, 'user', '如何设计消息表的全文搜索功能？', 12, NULL, '2024-01-15 10:01:30'),
(@conv3_id, 'assistant', '对于消息表的全文搜索，有几种方案：\n\n**方案1：MySQL全文索引**\n```sql\nCREATE FULLTEXT INDEX idx_content ON messages(content(1000));\n```\n- 优点：简单易用，无需额外组件\n- 缺点：性能有限，不支持复杂搜索\n\n**方案2：Elasticsearch集成**\n- 优点：高性能，支持复杂查询\n- 缺点：需要维护额外服务\n\n**方案3：混合方案**\n- 短消息用MySQL全文索引\n- 长文档用外部搜索引擎\n\n根据数据量选择合适方案。', 180, @gpt4_id, '2024-01-15 10:02:10');

-- 对话4：温度参数测试（Developer）
INSERT INTO `messages` (`conversation_id`, `role`, `content`, `tokens_used`, `model_id`, `created_at`) VALUES
(@conv4_id, 'user', '用temperature=0.3生成一段关于春天的描述', 10, NULL, '2024-01-18 08:00:00'),
(@conv4_id, 'assistant', '春天来了，大地苏醒。树木抽出新芽，花朵绽放。阳光温暖，微风轻拂。鸟儿在枝头歌唱，万物充满生机。这是一个充满希望的季节。', 45, @gpt35_id, '2024-01-18 08:00:30'),
(@conv4_id, 'user', '同样的主题，用temperature=1.2再生成一段', 9, NULL, '2024-01-18 08:01:00'),
(@conv4_id, 'assistant', '啊！春天这位神奇的画家，挥舞着调色板在天地间肆意挥洒！嫩绿的草芽像顽皮的孩子，从泥土里探出好奇的脑袋。樱花如粉色的云朵，轻轻飘落在潺潺的小溪上。蜜蜂在花丛中跳着圆舞曲，蝴蝶的翅膀闪烁着彩虹般的光芒。空气里弥漫着泥土的芬芳和花朵的甜香，仿佛整个宇宙都在庆祝这生命的狂欢节！', 95, @gpt35_id, '2024-01-18 08:01:30');

-- ============================================
-- 6. API调用日志表测试数据
-- ============================================
INSERT INTO `api_call_logs` (`user_id`, `model_id`, `conversation_id`, `endpoint`, `request_tokens`, `response_tokens`, `total_tokens`, `response_time_ms`, `status_code`, `is_success`, `error_message`, `created_at`) VALUES
-- 成功调用记录
(@admin_id, @gpt4_id, @conv3_id, '/v1/chat/completions', 150, 850, 1000, 2450, 200, TRUE, NULL, '2024-01-15 10:00:40'),
(@admin_id, @gpt4_id, @conv3_id, '/v1/chat/completions', 120, 720, 840, 2100, 200, TRUE, NULL, '2024-01-15 10:02:10'),
(@alice_id, @gpt35_id, @conv1_id, '/v1/chat/completions', 85, 520, 605, 1200, 200, TRUE, NULL, '2024-01-16 09:00:30'),
(@alice_id, @gpt35_id, @conv1_id, '/v1/chat/completions', 95, 650, 745, 1350, 200, TRUE, NULL, '2024-01-16 09:01:30'),
(@bob_id, @deepseek_id, @conv2_id, '/chat/completions', 120, 480, 600, 1800, 200, TRUE, NULL, '2024-01-17 13:00:45'),
(@bob_id, @deepseek_id, @conv2_id, '/chat/completions', 85, 320, 405, 950, 200, TRUE, NULL, '2024-01-17 13:02:00'),
(@dev_id, @gpt35_id, @conv4_id, '/v1/chat/completions', 65, 180, 245, 800, 200, TRUE, NULL, '2024-01-18 08:00:30'),
(@dev_id, @gpt35_id, @conv4_id, '/v1/chat/completions', 70, 380, 450, 1100, 200, TRUE, NULL, '2024-01-18 08:01:30'),

-- 失败调用记录（用于测试错误处理）
(@alice_id, @gpt35_id, NULL, '/v1/chat/completions', 120, 0, 120, 5000, 429, FALSE, 'Rate limit exceeded. Please try again in 20 seconds.', '2024-01-17 15:30:00'),
(@bob_id, @deepseek_id, NULL, '/chat/completions', 85, 0, 85, 30000, 504, FALSE, 'Gateway timeout. The server took too long to respond.', '2024-01-17 16:45:00'),
(@dev_id, @gpt4_id, NULL, '/v1/chat/completions', 200, 0, 200, 15000, 401, FALSE, 'Invalid API key provided.', '2024-01-18 09:30:00'),

-- 大量调用测试（性能监控）
(@admin_id, @gpt35_id, NULL, '/v1/chat/completions', 50, 150, 200, 450, 200, TRUE, NULL, '2024-01-18 10:00:00'),
(@admin_id, @gpt35_id, NULL, '/v1/chat/completions', 60, 180, 240, 520, 200, TRUE, NULL, '2024-01-18 10:01:00'),
(@admin_id, @gpt35_id, NULL, '/v1/chat/completions', 55, 165, 220, 480, 200, TRUE, NULL, '2024-01-18 10:02:00'),
(@admin_id, @gpt35_id, NULL, '/v1/chat/completions', 70, 210, 280, 550, 200, TRUE, NULL, '2024-01-18 10:03:00');

-- ============================================
-- 7. 登录尝试表测试数据
-- ============================================
INSERT INTO `login_attempts` (`username`, `ip_address`, `user_agent`, `is_success`, `created_at`) VALUES
-- 成功登录
('admin', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', TRUE, '2024-01-15 10:29:30'),
('alice', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', TRUE, '2024-01-16 14:19:30'),
('bob', '192.168.1.102', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15', TRUE, '2024-01-17 09:14:30'),

-- 失败登录（密码错误）
('admin', '192.168.1.200', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0', FALSE, '2024-01-15 09:30:00'),
('admin', '192.168.1.200', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0', FALSE, '2024-01-15 09:31:00'),
('alice', '192.168.1.201', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36', FALSE, '2024-01-16 13:45:00'),

-- Charlie的多次失败登录（导致账户锁定）
('charlie', '192.168.1.103', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0', FALSE, '2024-01-14 16:40:00'),
('charlie', '192.168.1.103', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0', FALSE, '2024-01-14 16:41:00'),
('charlie', '192.168.1.103', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0', FALSE, '2024-01-14 16:42:00'),
('charlie', '192.168.1.103', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0', FALSE, '2024-01-14 16:43:00'),
('charlie', '192.168.1.103', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0', FALSE, '2024-01-14 16:44:00'),

-- 可疑IP尝试
('admin', '203.0.113.5', 'python-requests/2.28.1', FALSE, '2024-01-18 03:00:00'),
('alice', '203.0.113.5', 'python-requests/2.28.1', FALSE, '2024-01-18 03:01:00'),
('bob', '203.0.113.5', 'python-requests/2.28.1', FALSE, '2024-01-18 03:02:00');

