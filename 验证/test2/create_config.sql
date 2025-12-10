-- create_config.sql
-- 为test2用户创建DeepSeek模型配置

-- 1. 查看当前数据
SELECT '当前用户信息:' as info;
SELECT user_id, username, email FROM users WHERE username = 'test2';

SELECT '当前DeepSeek模型:' as info;
SELECT model_id, model_name, model_provider FROM system_models 
WHERE model_provider = 'DeepSeek' OR model_name LIKE 'deepseek%';

-- 2. 插入配置（如果不存在）
INSERT INTO `user_model_configs` 
(`user_id`, `model_id`, `is_enabled`, `api_key`, `temperature`, `max_tokens`, `priority`) 
SELECT 
    u.user_id, 
    sm.model_id, 
    TRUE, 
    'sk-d35fc57d5206433bb336ea0fb2b5878b', 
    0.7, 
    2048, 
    1
FROM users u, system_models sm
WHERE u.username = 'test2' 
AND sm.model_name = 'deepseek-chat'
AND NOT EXISTS (
    SELECT 1 FROM user_model_configs umc
    WHERE umc.user_id = u.user_id 
    AND umc.model_id = sm.model_id
);

-- 3. 验证配置
SELECT '创建的配置:' as info;
SELECT 
    umc.config_id,
    u.username,
    sm.model_name,
    umc.is_enabled,
    umc.priority,
    umc.created_at
FROM user_model_configs umc
JOIN users u ON umc.user_id = u.user_id
JOIN system_models sm ON umc.model_id = sm.model_id
WHERE u.username = 'test2';
