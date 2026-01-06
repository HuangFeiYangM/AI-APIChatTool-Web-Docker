import React from 'react';
import { Card, Alert, Row, Col, Typography } from 'antd';
import { UserOutlined, MailOutlined } from '@ant-design/icons';
import type { FrontendUser } from '@/types/api';

interface GeneralSettingsPanelProps {
  user: FrontendUser;
  onUpdateUser: (updates: Partial<FrontendUser>) => Promise<void>;
}

const { Title, Text } = Typography;

const GeneralSettingsPanel: React.FC<GeneralSettingsPanelProps> = ({ user }) => {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ marginBottom: 8 }}>账户信息</Title>
        <Text type="secondary">查看您的账户基本信息</Text>
      </div>

      <Alert
        message="信息提示"
        description="用户信息由系统管理，不可修改。如需修改请联系管理员。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card title="基本信息" style={{ marginBottom: 24 }}>
            <Row gutter={[48, 16]}>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>
                    <UserOutlined style={{ marginRight: 8 }} />
                    用户名
                  </Text>
                  <Text>{user.username}</Text>
                </div>
                
                <div>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>
                    <MailOutlined style={{ marginRight: 8 }} />
                    邮箱地址
                  </Text>
                  <Text>{user.email || '未设置'}</Text>
                </div>
              </Col>
              
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>
                    用户ID
                  </Text>
                  <Text>{user.id || user.user_id}</Text>
                </div>
                
                <div>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>
                    账户状态
                  </Text>
                  <Text style={{ color: user.is_active ? '#52c41a' : '#ff4d4f' }}>
                    {user.is_active ? '活跃' : '禁用'}
                  </Text>
                </div>
              </Col>
            </Row>
          </Card>

          <Card title="账户统计">
            <Row gutter={[48, 16]}>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>
                    注册时间
                  </Text>
                  <Text>{new Date(user.created_at).toLocaleString()}</Text>
                </div>
                
                <div>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>
                    账户角色
                  </Text>
                  <Text>{user.is_admin ? '管理员' : '普通用户'}</Text>
                </div>
              </Col>
              
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>
                    最后登录
                  </Text>
                  <Text>{user.last_login_at ? new Date(user.last_login_at).toLocaleString() : '从未登录'}</Text>
                </div>
                
                <div>
                  <Text strong style={{ display: 'block', marginBottom: 4 }}>
                    账户创建时间
                  </Text>
                  <Text>{new Date(user.created_at).toLocaleDateString()}</Text>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <Card title="安全提示" style={{ marginTop: 24 }}>
        <Alert
          message="安全建议"
          description={
            <div>
              <p>1. 请妥善保管您的登录凭证，不要与他人分享</p>
              <p>2. 定期检查账户活动，确保没有异常登录</p>
              <p>3. 如发现任何异常情况，请立即联系管理员</p>
            </div>
          }
          type="warning"
          showIcon
        />
      </Card>
    </div>
  );
};

export default GeneralSettingsPanel;
