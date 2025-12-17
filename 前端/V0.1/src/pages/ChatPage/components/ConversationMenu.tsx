// src/pages/ChatPage/components/ConversationMenu.tsx - 最小化版本
import React, { useState } from 'react';
import { MoreOutlined, EditOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { Dropdown, Modal, Input, Button, message, Tag } from 'antd';
import type { MenuProps } from 'antd';
import type { StoreConversation } from '@/store/chatStore';
import chatApi from '@/api/chat';
import styles from '../ChatPage.module.css';

interface ConversationMenuProps {
  conversation: StoreConversation;
  onUpdate: (conversation: StoreConversation) => void;
  onDelete: (conversationId: string) => void;
}

const ConversationMenu: React.FC<ConversationMenuProps> = ({ 
  conversation, 
  onUpdate, 
  onDelete 
}) => {
  const [renameModalVisible, setRenameModalVisible] = useState(false);
  const [infoModalVisible, setInfoModalVisible] = useState(false);
  const [newTitle, setNewTitle] = useState(conversation.title);
  const [loading, setLoading] = useState(false);

  // 处理重命名
  const handleRename = async () => {
    if (!newTitle.trim()) {
      message.warning('请输入对话标题');
      return;
    }

    try {
      setLoading(true);
      const response = await chatApi.updateConversation(parseInt(conversation.id), {
        title: newTitle
      });

      if (response.success) {
        const updatedConv = {
          ...conversation,
          title: newTitle,
          updatedAt: new Date()
        };
        onUpdate(updatedConv);
        message.success('重命名成功');
        setRenameModalVisible(false);
      } else {
        message.error(response.message || '重命名失败');
      }
    } catch (error: any) {
      console.error('重命名失败:', error);
      const errorMsg = error.response?.data?.detail || error.message || '重命名失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 下拉菜单项
  const menuItems: MenuProps['items'] = [
    {
      key: 'rename',
      label: '重命名',
      icon: <EditOutlined />,
      onClick: () => {
        setNewTitle(conversation.title);
        setRenameModalVisible(true);
      }
    },
    {
      key: 'info',
      label: '对话信息',
      icon: <InfoCircleOutlined />,
      onClick: () => setInfoModalVisible(true)
    },
    {
      type: 'divider',
    },
    {
      key: 'delete',
      label: '删除对话',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => {
        Modal.confirm({
          title: '确认删除',
          content: '确定要删除这个对话吗？此操作不可恢复。',
          okText: '删除',
          cancelText: '取消',
          okType: 'danger',
          onOk: () => {
            onDelete(conversation.id);
          },
        });
      }
    }
  ];

  return (
    <>
      <Dropdown
        menu={{ items: menuItems }}
        trigger={['click']}
        placement="bottomRight"
        overlayClassName={styles.conversationMenuOverlay}
        overlayStyle={{ zIndex: 9999 }}
      >
        <Button
          type="text"
          icon={<MoreOutlined />}
          size="small"
          className={styles.menuButton}
          onClick={(e) => e.stopPropagation()}
        />
      </Dropdown>

      {/* 重命名模态框 */}
      <Modal
        title="重命名对话"
        open={renameModalVisible}
        onOk={handleRename}
        onCancel={() => setRenameModalVisible(false)}
        confirmLoading={loading}
        okText="保存"
        cancelText="取消"
      >
        <Input
          placeholder="输入新标题"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onPressEnter={handleRename}
          maxLength={50}
        />
      </Modal>

      {/* 对话信息模态框 */}
      <Modal
        title="对话信息"
        open={infoModalVisible}
        onCancel={() => setInfoModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setInfoModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={500}
      >
        <div className={styles.conversationInfo}>
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>对话标题：</span>
            <span className={styles.infoValue}>{conversation.title}</span>
          </div>
          
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>对话ID：</span>
            <span className={styles.infoValue}>{conversation.id}</span>
          </div>
          
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>使用模型：</span>
            <Tag color="blue">{conversation.model}</Tag>
          </div>
          
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>创建时间：</span>
            <span className={styles.infoValue}>
              {conversation.createdAt.toLocaleString('zh-CN')}
            </span>
          </div>
          
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>更新时间：</span>
            <span className={styles.infoValue}>
              {conversation.updatedAt.toLocaleString('zh-CN')}
            </span>
          </div>
          
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>消息数量：</span>
            <span className={styles.infoValue}>
              {conversation.messages.length} 条
            </span>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default ConversationMenu;
