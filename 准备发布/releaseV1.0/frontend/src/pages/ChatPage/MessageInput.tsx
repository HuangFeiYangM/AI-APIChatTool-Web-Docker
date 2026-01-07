import React, { useState } from 'react';
import { Input, Button, Select } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useChatStore } from '@/store/chatStore';
import styles from './ChatPage.module.css';

const { TextArea } = Input;
const { Option } = Select;

const MessageInput: React.FC = () => {
  const [message, setMessage] = useState('');
  const { selectedModel, setSelectedModel, isGenerating } = useChatStore();

  // 可用模型列表
  const models = [
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'deepseek-chat', label: 'DeepSeek Chat' },
    { value: 'claude-2', label: 'Claude 2' },
    { value: 'llama-2-70b', label: 'Llama 2 70B' },
  ];

  const handleSend = () => {
    if (!message.trim() || isGenerating) return;
    // 发送逻辑在父组件中处理
    setMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={styles.messageInputContainer}>
      <div className={styles.modelSelector}>
        <Select
          value={selectedModel}
          onChange={setSelectedModel}
          style={{ width: 200 }}
          disabled={isGenerating}
        >
          {models.map((model) => (
            <Option key={model.value} value={model.value}>
              {model.label}
            </Option>
          ))}
        </Select>
      </div>
      
      <div className={styles.inputWrapper}>
        <TextArea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入消息... (Shift+Enter换行，Enter发送)"
          autoSize={{ minRows: 1, maxRows: 6 }}
          disabled={isGenerating}
          className={styles.textArea}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={isGenerating}
          disabled={!message.trim()}
          className={styles.sendButton}
        >
          发送
        </Button>
      </div>
    </div>
  );
};

export default MessageInput;
