import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Modal, Input, Select, Tag, message, Space, Popconfirm,
  Form, Switch, Row, Col, Divider, Spin, Tabs, Card, Statistic
} from 'antd';
import { 
  SearchOutlined, DeleteOutlined, LockOutlined, 
  UnlockOutlined, UserOutlined, MailOutlined,
  CalendarOutlined, ClockCircleOutlined, MessageOutlined, 
  SettingOutlined, BarChartOutlined, DatabaseOutlined, EyeOutlined,
  CloseCircleOutlined, CheckOutlined, CloseOutlined
} from '@ant-design/icons';
import settingsApi from '@/api/settings';
import styles from '../SettingsPage.module.css';

const { Search } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

interface User {
  user_id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_locked: boolean;
  locked_reason?: string;
  locked_until?: string;
  failed_login_attempts: number;
  last_login_at?: string;
  conversation_count: number;
  created_at: string;
  updated_at: string;
}

// 用户详情接口定义
interface UserDetail extends User {
  conversations?: any[];
  model_configs?: any[];
  api_stats?: any;
}

const UserManagementPanel: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [lockReason, setLockReason] = useState('');

  // 添加的状态
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [editForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('basic');

  // 加载用户列表
  const loadUsers = async () => {
    setLoading(true);
    try {
      const params: any = {
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
      };
      
      if (searchText) {
        params.username = searchText;
        // 注意：根据后端API，同时搜索用户名和邮箱可能需要分别处理
        // 或者后端支持模糊搜索，这里我们只传username
      }
      
      if (filterStatus === 'active') params.is_active = true;
      if (filterStatus === 'inactive') params.is_active = false;
      if (filterStatus === 'locked') params.is_locked = true;
      
      console.log('加载用户列表参数:', params);
      
      // 使用 settingsApi.getUsers 方法
      const response = await settingsApi.getUsers(params);
      console.log('用户列表响应:', response);
      
      if (response.success) {
        setUsers(response.data);
        setTotal(response.total);
      } else {
        message.error(response.message || '加载用户列表失败');
      }
    } catch (error) {
      console.error('加载用户列表失败:', error);
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [currentPage, pageSize, filterStatus]);

  const handleSearch = () => {
    setCurrentPage(1);
    loadUsers();
  };

  // 获取用户详情的函数
  const fetchUserDetail = async (userId: number) => {
    setDetailLoading(true);
    try {
      console.log('正在获取用户详情，用户ID:', userId);
      
      // 使用 settingsApi.getUserDetail 方法
      const response = await settingsApi.getUserDetail(userId);
      console.log('用户详情API响应:', response);
      
      if (response.success) {
        setSelectedUser(response.data);
        // 设置表单初始值
        editForm.setFieldsValue({
          user_id: response.data.user_id,
          username: response.data.username,
          email: response.data.email,
          is_active: response.data.is_active,
          is_locked: response.data.is_locked,
          locked_reason: response.data.locked_reason || '',
          locked_until: response.data.locked_until || null
        });
        setDetailModalVisible(true);
        setActiveTab('basic');
      } else {
        message.error(response.message || '获取用户详情失败');
      }
    } catch (error: any) {
      console.error('获取用户详情失败，详细错误:', error);
      
      let errorMsg = '获取用户详情失败';
      if (error.response) {
        errorMsg = `服务器错误: ${error.response.status}`;
      } else if (error.request) {
        errorMsg = '无法连接到服务器，请检查网络连接';
      } else {
        errorMsg = error.message || '未知错误';
      }
      
      message.error(errorMsg);
    } finally {
      setDetailLoading(false);
    }
  };

  // 处理详情按钮点击
  const handleViewDetail = (user: User) => {
    fetchUserDetail(user.user_id);
  };

  // 处理保存修改
  const handleSaveEdit = async () => {
    try {
      const values = await editForm.validateFields();
      
      if (!selectedUser) return;
      
      // 准备更新数据 - 只发送修改的字段
      const updateData: any = {};
      
      if (values.username !== selectedUser.username) {
        updateData.username = values.username;
      }
      if (values.email !== selectedUser.email) {
        updateData.email = values.email;
      }
      if (values.is_active !== selectedUser.is_active) {
        updateData.is_active = values.is_active;
      }
      
      // 注意：锁定状态应该通过专门的锁定/解锁按钮修改
      // 这里不更新 is_locked，locked_reason，locked_until
      
      if (Object.keys(updateData).length === 0) {
        message.info('没有修改任何信息');
        return;
      }
      
      console.log('更新用户数据:', updateData);
      
      // 使用 settingsApi.updateUser 方法
      const response = await settingsApi.updateUser(selectedUser.user_id, updateData);
      
      if (response.success) {
        message.success('用户信息更新成功');
        setDetailModalVisible(false);
        loadUsers(); // 刷新用户列表
      } else {
        message.error(response.message || '更新失败');
      }
    } catch (error: any) {
      console.error('保存失败:', error);
      message.error(`保存失败: ${error.message || '未知错误'}`);
    }
  };

  // 处理锁定用户
  const handleLockUser = async (userId: number) => {
    Modal.confirm({
      title: '锁定用户确认',
      content: (
        <div>
          <p>确定要锁定该用户吗？</p>
          <Input 
            placeholder="请输入锁定原因（可选）"
            onChange={(e) => setLockReason(e.target.value)}
            style={{ marginTop: 8 }}
          />
        </div>
      ),
      onOk: async () => {
        try {
          const response = await settingsApi.lockUser(userId, lockReason || '管理员操作', 24);
          if (response.success) {
            message.success('用户已锁定');
            setLockReason(''); // 清空锁定原因
            loadUsers();
          }
        } catch (error) {
          message.error('锁定用户失败');
        }
      }
    });
  };

  // 处理解锁用户
  const handleUnlockUser = async (userId: number) => {
    Modal.confirm({
      title: '解锁用户确认',
      content: '确定要解锁该用户吗？',
      onOk: async () => {
        try {
          const response = await settingsApi.unlockUser(userId);
          if (response.success) {
            message.success('用户已解锁');
            loadUsers();
          }
        } catch (error) {
          message.error('解锁用户失败');
        }
      }
    });
  };

  // 处理删除用户
  const handleDeleteUser = async (userId: number) => {
    try {
      // 这里应该调用删除用户的API
      // 暂时模拟成功
      message.success('用户删除成功（演示）');
      loadUsers();
    } catch (error) {
      message.error('删除用户失败');
    }
  };

  // 列定义
  const columns = [
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 150,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200,
    },
    {
      title: '状态',
      key: 'status',
      width: 150,
      render: (_: any, record: User) => (
        <Space size="small">
          {record.is_active ? <Tag color="success">活跃</Tag> : <Tag color="default">未激活</Tag>}
          {record.is_locked ? <Tag color="error">锁定</Tag> : null}
          {record.failed_login_attempts > 0 && <Tag color="warning">登录失败: {record.failed_login_attempts}</Tag>}
        </Space>
      ),
    },
    {
      title: '对话数量',
      dataIndex: 'conversation_count',
      key: 'conversation_count',
      width: 100,
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login_at',
      key: 'last_login_at',
      width: 180,
      render: (text: string) => text ? new Date(text).toLocaleString() : '从未登录',
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: any, record: User) => {
        const isCurrentUser = record.username === 'admin'; // 这里应该从store获取当前用户
        
        return (
          <Space size="small">
            <Button
              type="link"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => handleViewDetail(record)}
              style={{ color: '#1890ff' }}
            >
              详情
            </Button>
            {record.is_locked ? (
              <Button
                type="link"
                icon={<UnlockOutlined />}
                size="small"
                onClick={() => handleUnlockUser(record.user_id)}
                disabled={isCurrentUser}
                style={{ color: '#52c41a' }}
              >
                解锁
              </Button>
            ) : (
              <Button
                type="link"
                icon={<LockOutlined />}
                size="small"
                onClick={() => handleLockUser(record.user_id)}
                disabled={isCurrentUser}
                style={{ color: '#ff4d4f' }}
              >
                锁定
              </Button>
            )}
            <Popconfirm
              title="确定要删除这个用户吗？"
              description="此操作将永久删除该用户及其所有数据，请谨慎操作！"
              onConfirm={() => handleDeleteUser(record.user_id)}
              okText="确定"
              cancelText="取消"
              disabled={isCurrentUser}
            >
              <Button
                type="link"
                icon={<DeleteOutlined />}
                size="small"
                danger
                disabled={isCurrentUser}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  // 渲染用户详情模态框
  const renderUserDetailModal = () => (
    <Modal
      title={
        <div>
          <UserOutlined style={{ marginRight: 8 }} />
          用户详情 - {selectedUser?.username}
          <Tag 
            color={selectedUser?.is_active ? 'success' : 'default'} 
            style={{ marginLeft: 12 }}
          >
            {selectedUser?.is_active ? '活跃' : '禁用'}
          </Tag>
          {selectedUser?.is_locked && (
            <Tag color="error" style={{ marginLeft: 8 }}>锁定</Tag>
          )}
        </div>
      }
      open={detailModalVisible}
      onCancel={() => {
        setDetailModalVisible(false);
        setActiveTab('basic');
      }}
      width={900}
      footer={[
        <Button key="cancel" onClick={() => {
          setDetailModalVisible(false);
          setActiveTab('basic');
        }}>
          关闭
        </Button>,
        <Button 
          key="save" 
          type="primary" 
          onClick={handleSaveEdit}
          loading={detailLoading}
        >
          保存修改
        </Button>
      ]}
    >
      {selectedUser && (
        <Spin spinning={detailLoading}>
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            {/* 基本信息 Tab */}
            <TabPane 
              tab={
                <span>
                  <UserOutlined />
                  基本信息
                </span>
              } 
              key="basic"
            >
              <Form
                form={editForm}
                layout="vertical"
                style={{ marginTop: 16 }}
              >
                <Row gutter={24}>
                  <Col span={12}>
                    <Form.Item
                      label={
                        <span>
                          <UserOutlined style={{ marginRight: 8 }} />
                          用户ID
                        </span>
                      }
                      name="user_id"
                      initialValue={selectedUser.user_id}
                    >
                      <Input placeholder="用户ID" disabled />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label={
                        <span>
                          <UserOutlined style={{ marginRight: 8 }} />
                          用户名
                        </span>
                      }
                      name="username"
                      rules={[{ required: true, message: '请输入用户名' }]}
                    >
                      <Input placeholder="请输入用户名" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={24}>
                  <Col span={12}>
                    <Form.Item
                      label={
                        <span>
                          <MailOutlined style={{ marginRight: 8 }} />
                          邮箱
                        </span>
                      }
                      name="email"
                      rules={[
                        { required: true, message: '请输入邮箱' },
                        { type: 'email', message: '请输入有效的邮箱地址' }
                      ]}
                    >
                      <Input placeholder="user@example.com" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label={
                        <span>
                          <SettingOutlined style={{ marginRight: 8 }} />
                          账户状态
                        </span>
                      }
                      name="is_active"
                      valuePropName="checked"
                    >
                      <Switch 
                        checkedChildren="启用" 
                        unCheckedChildren="禁用"
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Divider>账户安全信息</Divider>
                
                <Row gutter={24}>
                  <Col span={8}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                        {selectedUser.failed_login_attempts}
                      </div>
                      <div style={{ color: '#666', fontSize: 12 }}>登录失败次数</div>
                    </div>
                  </Col>
                  <Col span={8}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, fontWeight: 'bold', color: selectedUser.is_locked ? '#ff4d4f' : '#52c41a' }}>
                        {selectedUser.is_locked ? '已锁定' : '正常'}
                      </div>
                      <div style={{ color: '#666', fontSize: 12 }}>账户状态</div>
                    </div>
                  </Col>
                  <Col span={8}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, fontWeight: 'bold', color: '#722ed1' }}>
                        {selectedUser.conversation_count}
                      </div>
                      <div style={{ color: '#666', fontSize: 12 }}>对话数量</div>
                    </div>
                  </Col>
                </Row>

                {/* 锁定信息 - 仅在锁定时显示 */}
                {selectedUser.is_locked && (
                  <div style={{ 
                    background: '#fff2f0', 
                    padding: 12, 
                    borderRadius: 6,
                    marginTop: 16,
                    border: '1px solid #ffccc7'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                      <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
                      <strong style={{ color: '#ff4d4f' }}>账户已被锁定</strong>
                    </div>
                    {selectedUser.locked_reason && (
                      <div style={{ marginBottom: 4 }}>
                        <strong>锁定原因：</strong>{selectedUser.locked_reason}
                      </div>
                    )}
                    {selectedUser.locked_until && (
                      <div>
                        <strong>解锁时间：</strong>
                        {new Date(selectedUser.locked_until).toLocaleString()}
                      </div>
                    )}
                  </div>
                )}

                <Divider>时间信息</Divider>
                
                <Row gutter={24}>
                  <Col span={12}>
                    <div style={{ background: '#fafafa', padding: 12, borderRadius: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                        <CalendarOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                        <strong>注册时间</strong>
                      </div>
                      <div>{new Date(selectedUser.created_at).toLocaleString()}</div>
                    </div>
                  </Col>
                  <Col span={12}>
                    <div style={{ background: '#fafafa', padding: 12, borderRadius: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                        <ClockCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                        <strong>最后登录</strong>
                      </div>
                      <div>
                        {selectedUser.last_login_at 
                          ? new Date(selectedUser.last_login_at).toLocaleString()
                          : '从未登录'}
                      </div>
                    </div>
                  </Col>
                </Row>
              </Form>
            </TabPane>

            {/* 对话列表 Tab */}
            <TabPane 
              tab={
                <span>
                  <MessageOutlined />
                  对话记录
                  <Tag style={{ marginLeft: 8, fontSize: 12 }}>
                    {selectedUser.conversations?.length || 0}
                  </Tag>
                </span>
              } 
              key="conversations"
            >
              <Table
                dataSource={selectedUser.conversations || []}
                columns={[
                  {
                    title: '对话ID',
                    dataIndex: 'conversation_id',
                    key: 'conversation_id',
                    width: 100,
                  },
                  {
                    title: '标题',
                    dataIndex: 'title',
                    key: 'title',
                    ellipsis: true,
                  },
                  {
                    title: '模型ID',
                    dataIndex: 'model_id',
                    key: 'model_id',
                    width: 100,
                  },
                  {
                    title: '消息数',
                    dataIndex: 'message_count',
                    key: 'message_count',
                    width: 100,
                  },
                  {
                    title: 'Token数',
                    dataIndex: 'total_tokens',
                    key: 'total_tokens',
                    width: 100,
                  },
                  {
                    title: '创建时间',
                    dataIndex: 'created_at',
                    key: 'created_at',
                    width: 180,
                    render: (text: string) => new Date(text).toLocaleString(),
                  },
                ]}
                pagination={{ pageSize: 5 }}
                size="small"
                rowKey="conversation_id"
              />
            </TabPane>

            {/* 模型配置 Tab */}
            <TabPane 
              tab={
                <span>
                  <SettingOutlined />
                  模型配置
                  <Tag style={{ marginLeft: 8, fontSize: 12 }}>
                    {selectedUser.model_configs?.length || 0}
                  </Tag>
                </span>
              } 
              key="configs"
            >
              <Table
                dataSource={selectedUser.model_configs || []}
                columns={[
                  {
                    title: '配置ID',
                    dataIndex: 'config_id',
                    key: 'config_id',
                    width: 100,
                  },
                  {
                    title: '模型ID',
                    dataIndex: 'model_id',
                    key: 'model_id',
                    width: 100,
                  },
                  {
                    title: '启用状态',
                    dataIndex: 'is_enabled',
                    key: 'is_enabled',
                    width: 100,
                    render: (enabled: boolean) => (
                      <Tag color={enabled ? 'success' : 'default'}>
                        {enabled ? '启用' : '禁用'}
                      </Tag>
                    ),
                  },
                  {
                    title: '优先级',
                    dataIndex: 'priority',
                    key: 'priority',
                    width: 100,
                  },
                  {
                    title: '最后使用',
                    dataIndex: 'last_used_at',
                    key: 'last_used_at',
                    width: 180,
                    render: (text: string) => text ? new Date(text).toLocaleString() : '从未使用',
                  },
                ]}
                pagination={{ pageSize: 5 }}
                size="small"
                rowKey="config_id"
              />
            </TabPane>

            {/* API统计 Tab */}
            <TabPane 
              tab={
                <span>
                  <BarChartOutlined />
                  API统计
                </span>
              } 
              key="stats"
            >
              {selectedUser.api_stats ? (
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Card size="small" style={{ textAlign: 'center' }}>
                      <Statistic
                        title="总调用次数"
                        value={selectedUser.api_stats.total_calls}
                        valueStyle={{ color: '#1890ff' }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" style={{ textAlign: 'center' }}>
                      <Statistic
                        title="请求Token"
                        value={selectedUser.api_stats.total_request_tokens}
                        suffix="tokens"
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" style={{ textAlign: 'center' }}>
                      <Statistic
                        title="响应Token"
                        value={selectedUser.api_stats.total_response_tokens}
                        suffix="tokens"
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" style={{ textAlign: 'center' }}>
                      <Statistic
                        title="总Token数"
                        value={selectedUser.api_stats.total_tokens}
                        suffix="tokens"
                        valueStyle={{ color: '#52c41a' }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" style={{ textAlign: 'center' }}>
                      <Statistic
                        title="平均响应时间"
                        value={selectedUser.api_stats.avg_response_time}
                        suffix="ms"
                        precision={0}
                        valueStyle={{ 
                          color: selectedUser.api_stats.avg_response_time > 2000 ? '#ff4d4f' : '#722ed1' 
                        }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" style={{ textAlign: 'center' }}>
                      <Statistic
                        title="成功率"
                        value={selectedUser.api_stats.success_rate * 100}
                        suffix="%"
                        precision={2}
                        valueStyle={{ 
                          color: selectedUser.api_stats.success_rate > 0.9 ? '#52c41a' : 
                                 selectedUser.api_stats.success_rate > 0.7 ? '#faad14' : '#ff4d4f' 
                        }}
                      />
                    </Card>
                  </Col>
                </Row>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <DatabaseOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                  <p>暂无API使用统计</p>
                </div>
              )}
            </TabPane>
          </Tabs>
        </Spin>
      )}
    </Modal>
  );

  return (
    <div className={styles.userManagementPanel}>
      <div className={styles.panelHeader}>
        <h2>用户管理</h2>
        <p>管理系统用户，包括锁定、解锁和删除用户</p>
      </div>

      <div className={styles.filterBar}>
        <div className={styles.searchBar}>
          <Search
            placeholder="搜索用户名或邮箱"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 300 }}
            allowClear
          />
        </div>
        
        <div className={styles.filterControls}>
          <Select
            value={filterStatus}
            onChange={setFilterStatus}
            style={{ width: 120 }}
          >
            <Option value="all">全部状态</Option>
            <Option value="active">活跃用户</Option>
            <Option value="inactive">未激活</Option>
            <Option value="locked">已锁定</Option>
          </Select>
          
          <Button type="primary" onClick={loadUsers} loading={loading}>
            刷新
          </Button>
        </div>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="user_id"
        loading={loading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 个用户`,
          onChange: (page, pageSize) => {
            setCurrentPage(page);
            setPageSize(pageSize);
          },
        }}
        scroll={{ x: 1400 }}
      />
      
      {/* 使用新设计的用户详情模态框 */}
      {renderUserDetailModal()}
    </div>
  );
};

export default UserManagementPanel;
