import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Typography, Spin, Alert, Tabs, DatePicker, message } from 'antd';
import { 
  UserOutlined, MessageOutlined, DatabaseOutlined, 
  LineChartOutlined, CheckCircleOutlined, WarningOutlined,
  DashboardOutlined, ClockCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import settingsApi from '@/api/settings';
import styles from '../SettingsPage.module.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

// 从粘贴文本中复制的接口定义
interface SystemStats {
  total_users: number;
  active_users: number;
  locked_users: number;
  total_conversations: number;
  total_messages: number;
  total_api_calls: number;
  total_tokens_used: number;
  system_uptime: number;
  avg_response_time: number;
  api_success_rate: number;
}

interface HealthStatus {
  status: string;
  database: boolean;
  disk_usage: number;
  memory_usage: number;
  cpu_usage: number;
  last_check: string;
}

// 保留原有的接口定义
interface DailyStats {
  date: string;
  user_count: number;
  conversation_count: number;
  message_count: number;
  api_calls: number;
}

interface ApiLog {
  log_id: number;
  created_at: string;
  username: string;
  model_name: string;
  is_success: boolean;
  response_time: number;
  tokens_used: number;
  client_ip: string;
}

const SystemStatsPanel: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [apiLogs, setApiLogs] = useState<ApiLog[]>([]);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(7, 'day'),
    dayjs(),
  ]);

  // 加载系统统计和健康状态
  const loadSystemStats = async () => {
    setLoading(true);
    try {
      // 获取系统统计
      const statsResponse = await settingsApi.getSystemStats();
      if (statsResponse.success) {
        setStats(statsResponse.data);
      }

      // 获取健康状态
      const healthResponse = await settingsApi.getSystemHealth();
      if (healthResponse.success) {
        setHealth(healthResponse.data);
      }
    } catch (error) {
      console.error('加载系统统计失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 加载每日统计
  const loadDailyStats = async () => {
    try {
      const response = await settingsApi.getDailyStats(7);
      if (response.success) {
        setDailyStats(response.data);
      }
    } catch (error) {
      console.error('加载每日统计失败:', error);
    }
  };

  // 加载API日志
  const loadApiLogs = async () => {
    try {
      const response = await settingsApi.getApiLogs({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        limit: 10,
      });

      if (response.success) {
        setApiLogs(response.data.logs || []);
      }
    } catch (error) {
      console.error('加载API日志失败:', error);
    }
  };

  // 加载所有数据
  const loadAllData = async () => {
    await loadSystemStats();
    await loadDailyStats();
    await loadApiLogs();
  };

  useEffect(() => {
    loadAllData();
    
    // 每5分钟刷新一次数据
    const interval = setInterval(loadSystemStats, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // 当日期范围变化时重新加载API日志
  useEffect(() => {
    if (activeTab === 'monitoring') {
      loadApiLogs();
    }
  }, [dateRange, activeTab]);

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#52c41a';
      case 'warning': return '#faad14';
      case 'critical': return '#f5222d';
      default: return '#d9d9d9';
    }
  };

  const getHealthStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return '健康';
      case 'warning': return '警告';
      case 'critical': return '严重';
      default: return '未知';
    }
  };

  const apiLogColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: '模型',
      dataIndex: 'model_name',
      key: 'model_name',
      width: 150,
    },
    {
      title: '状态',
      dataIndex: 'is_success',
      key: 'is_success',
      width: 100,
      render: (success: boolean) => (
        <span style={{ color: success ? '#52c41a' : '#f5222d' }}>
          {success ? '成功' : '失败'}
        </span>
      ),
    },
    {
      title: '响应时间',
      dataIndex: 'response_time',
      key: 'response_time',
      width: 120,
      render: (time: number) => `${time}ms`,
    },
    {
      title: '消耗令牌',
      dataIndex: 'tokens_used',
      key: 'tokens_used',
      width: 100,
    },
    {
      title: 'IP地址',
      dataIndex: 'client_ip',
      key: 'client_ip',
      width: 150,
    },
  ];

  if (loading && activeTab === 'overview') {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p>正在加载系统统计...</p>
      </div>
    );
  }

  return (
    <div className={styles.systemStatsPanel}>
      <div className={styles.panelHeader}>
        <Title level={2}>系统统计</Title>
        <Text type="secondary">平台运行状态和统计数据</Text>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="概览" key="overview">
          {/* 健康状态卡片 */}
          {health && (
            <Card 
              title="系统健康状态" 
              style={{ marginBottom: 16 }}
              extra={
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <div 
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: getHealthStatusColor(health.status),
                      marginRight: 8
                    }}
                  />
                  <span style={{ color: getHealthStatusColor(health.status) }}>
                    {getHealthStatusText(health.status)}
                  </span>
                </div>
              }
            >
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="数据库"
                    value={health.database ? '正常' : '异常'}
                    prefix={health.database ? <CheckCircleOutlined /> : <WarningOutlined />}
                    valueStyle={{ color: health.database ? '#52c41a' : '#f5222d' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="磁盘使用率"
                    value={health.disk_usage}
                    suffix="%"
                    valueStyle={{ color: health.disk_usage > 90 ? '#f5222d' : health.disk_usage > 80 ? '#faad14' : '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="内存使用率"
                    value={health.memory_usage}
                    suffix="%"
                    valueStyle={{ color: health.memory_usage > 90 ? '#f5222d' : health.memory_usage > 80 ? '#faad14' : '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="CPU使用率"
                    value={health.cpu_usage}
                    suffix="%"
                    valueStyle={{ color: health.cpu_usage > 90 ? '#f5222d' : health.cpu_usage > 80 ? '#faad14' : '#52c41a' }}
                  />
                </Col>
              </Row>
              {health.status === 'warning' && (
                <Alert
                  message="系统警告"
                  description="部分资源使用率较高，建议进行优化或扩容"
                  type="warning"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              )}
              {health.status === 'critical' && (
                <Alert
                  message="系统异常"
                  description="系统存在严重问题，请立即检查"
                  type="error"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              )}
            </Card>
          )}

          {/* 用户统计 */}
          <Card title="用户统计" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="总用户数"
                  value={stats?.total_users || 0}
                  prefix={<UserOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="活跃用户"
                  value={stats?.active_users || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="锁定用户"
                  value={stats?.locked_users || 0}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="系统运行时间"
                  value={stats?.system_uptime || 0}
                  suffix="小时"
                  precision={2}
                />
              </Col>
            </Row>
          </Card>

          {/* 内容统计 */}
          <Card title="内容统计" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="对话总数"
                  value={stats?.total_conversations || 0}
                  prefix={<DatabaseOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="消息总数"
                  value={stats?.total_messages || 0}
                  prefix={<MessageOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="API调用次数"
                  value={stats?.total_api_calls || 0}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="总token数"
                  value={stats?.total_tokens_used || 0}
                  suffix="tokens"
                />
              </Col>
            </Row>
          </Card>

          {/* API性能统计 */}
          <Card title="API性能统计">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="平均响应时间"
                  value={stats?.avg_response_time || 0}
                  suffix="ms"
                  precision={2}
                  valueStyle={{ color: stats && stats.avg_response_time > 5000 ? '#f5222d' : '#52c41a' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="API成功率"
                  value={stats?.api_success_rate || 0}
                  suffix="%"
                  precision={2}
                  valueStyle={{ color: stats && stats.api_success_rate < 90 ? '#f5222d' : '#52c41a' }}
                />
              </Col>
            </Row>
          </Card>
        </TabPane>

        <TabPane tab="监控详情" key="monitoring">
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card
                title="API调用日志"
                extra={
                  <RangePicker
                    value={dateRange}
                    onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
                  />
                }
              >
                <Table
                  columns={apiLogColumns}
                  dataSource={apiLogs}
                  rowKey="log_id"
                  pagination={false}
                  scroll={{ y: 300 }}
                  size="small"
                />
              </Card>
            </Col>

            <Col span={24}>
              <Card title="每日统计趋势">
                <Table
                  dataSource={dailyStats}
                  rowKey="date"
                  pagination={false}
                  scroll={{ y: 300 }}
                  size="small"
                >
                  <Table.Column
                    title="日期"
                    dataIndex="date"
                    key="date"
                    width={120}
                    render={(text: string) => dayjs(text).format('MM-DD')}
                  />
                  <Table.Column
                    title="新增用户"
                    dataIndex="user_count"
                    key="user_count"
                    width={100}
                  />
                  <Table.Column
                    title="新增对话"
                    dataIndex="conversation_count"
                    key="conversation_count"
                    width={100}
                  />
                  <Table.Column
                    title="新增消息"
                    dataIndex="message_count"
                    key="message_count"
                    width={100}
                  />
                  <Table.Column
                    title="API调用"
                    dataIndex="api_calls"
                    key="api_calls"
                    width={100}
                  />
                </Table>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      <div style={{ marginTop: 16, textAlign: 'center' }}>
        <Text type="secondary">
          最后更新: {new Date().toLocaleString()}
          <br />
          统计数据每5分钟自动更新
        </Text>
        <br />
        <Text 
          type="secondary" 
          style={{ cursor: 'pointer' }}
          onClick={loadAllData}
        >
          点击刷新数据
        </Text>
      </div>
    </div>
  );
};

export default SystemStatsPanel;
