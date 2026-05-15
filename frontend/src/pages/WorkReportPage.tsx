import React, { useState } from 'react';
import { Card, Table, Button, Space, Tag, Select, DatePicker, Modal, message, Tabs } from 'antd';
import { PlusOutlined, EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import dayjs from 'dayjs';
import { RootState } from '../store/store';
import { useWorkReports, useTeamWorkReports, useGenerateDraft, WorkReport } from '../hooks/useWorkReports';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { confirm } = Modal;

type ReportType = 'daily' | 'weekly';
type ReportStatus = 'draft' | 'submitted' | 'withdrawn';

const STATUS_LABELS: Record<ReportStatus, string> = {
  draft: '草稿',
  submitted: '已提交',
  withdrawn: '已撤回',
};

const STATUS_COLORS: Record<ReportStatus, string> = {
  draft: 'default',
  submitted: 'success',
  withdrawn: 'warning',
};

const TYPE_LABELS: Record<ReportType, string> = {
  daily: '日报',
  weekly: '周报',
};

const getMonday = (value: dayjs.Dayjs) => value.subtract((value.day() + 6) % 7, 'day');

const WorkReportPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, capabilities } = useSelector((state: RootState) => state.auth);
  const canCreateReport = Boolean(capabilities['work_report:create']);
  const canUseWorkReports = Boolean(capabilities['work_report:read']) && user?.role !== 'finance';
  const canTeamRead = Boolean(capabilities['work_report:team_read'] || capabilities['dashboard:team']);
  const isFinance = user?.role === 'finance';

  const [activeTab, setActiveTab] = useState<'personal' | 'team'>('personal');
  const [reportType, setReportType] = useState<ReportType>('daily');
  const [status, setStatus] = useState<ReportStatus | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

  const personalQuery = useWorkReports(
    {
      report_type: reportType,
      status,
      date_from: dateRange?.[0]?.format('YYYY-MM-DD'),
      date_to: dateRange?.[1]?.format('YYYY-MM-DD'),
      limit: 50,
    },
    activeTab === 'personal' && canUseWorkReports
  );

  const teamQuery = useTeamWorkReports(
    {
      report_type: reportType,
      status,
      date_from: dateRange?.[0]?.format('YYYY-MM-DD'),
      date_to: dateRange?.[1]?.format('YYYY-MM-DD'),
      limit: 50,
    },
    activeTab === 'team' && canTeamRead
  );

  const generateDraftMutation = useGenerateDraft();

  const data = activeTab === 'personal' ? personalQuery.data : teamQuery.data;
  const isLoading = activeTab === 'personal' ? personalQuery.isLoading : teamQuery.isLoading;

  const handleGenerateDraft = (type: ReportType) => {
    if (!canCreateReport) {
      message.warning('当前账号无权生成报告草稿');
      return;
    }

    const today = dayjs();
    const reportDate = type === 'daily' ? today : getMonday(today);

    confirm({
      title: `生成${TYPE_LABELS[type]}草稿`,
      content: `确定生成 ${reportDate.format('YYYY-MM-DD')} 的${TYPE_LABELS[type]}草稿吗？`,
      onOk: async () => {
        try {
          const result = await generateDraftMutation.mutateAsync({
            report_type: type,
            report_date: reportDate.format('YYYY-MM-DD'),
          });
          message.success('草稿生成成功');
          navigate(`/work-reports/${result.id}`);
        } catch (error) {
          message.error('生成失败');
        }
      },
    });
  };

  const columns = [
    {
      title: '类型',
      dataIndex: 'report_type',
      key: 'report_type',
      width: 80,
      render: (type: ReportType) => <Tag color={type === 'daily' ? 'blue' : 'purple'}>{TYPE_LABELS[type]}</Tag>,
    },
    {
      title: '日期',
      dataIndex: 'report_date',
      key: 'report_date',
      width: 120,
      render: (date: string, record: WorkReport) => {
        if (record.report_type === 'weekly' && record.week_start && record.week_end) {
          return `${record.week_start} ~ ${record.week_end}`;
        }
        return date;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: ReportStatus) => <Tag color={STATUS_COLORS[status]}>{STATUS_LABELS[status]}</Tag>,
    },
    {
      title: '提交时间',
      dataIndex: 'submitted_at',
      key: 'submitted_at',
      width: 160,
      render: (time: string | null) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time: string | null) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: WorkReport) => (
        <Button icon={<EyeOutlined />} onClick={() => navigate(`/work-reports/${record.id}`)}>
          查看
        </Button>
      ),
    },
  ];

  if (isFinance) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          财务角色暂不支持日报/周报功能
        </div>
      </Card>
    );
  }

  return (
    <Card
      title="日报/周报管理"
      extra={
        canCreateReport && (
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => handleGenerateDraft('daily')}
              loading={generateDraftMutation.isPending}
            >
              生成日报草稿
            </Button>
            <Button
              icon={<PlusOutlined />}
              onClick={() => handleGenerateDraft('weekly')}
              loading={generateDraftMutation.isPending}
            >
              生成周报草稿
            </Button>
          </Space>
        )
      }
    >
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key as 'personal' | 'team')}
        items={[
          {
            key: 'personal',
            label: '我的报告',
            disabled: !canUseWorkReports,
          },
          ...(canTeamRead
            ? [{
                key: 'team',
                label: '团队报告',
              }]
            : []),
        ]}
      />

      <div style={{ marginBottom: 16 }}>
        <Space>
          <Select
            value={reportType}
            onChange={(v) => setReportType(v as ReportType)}
            style={{ width: 120 }}
          >
            <Option value="daily">日报</Option>
            <Option value="weekly">周报</Option>
          </Select>

          <Select
            value={status}
            onChange={(v) => setStatus(v as ReportStatus | undefined)}
            style={{ width: 120 }}
            allowClear
            placeholder="状态筛选"
          >
            <Option value="draft">草稿</Option>
            <Option value="submitted">已提交</Option>
            <Option value="withdrawn">已撤回</Option>
          </Select>

          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
            style={{ width: 240 }}
          />

          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              if (activeTab === 'personal') {
                personalQuery.refetch();
              } else {
                teamQuery.refetch();
              }
            }}
          >
            刷新
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
    </Card>
  );
};

export default WorkReportPage;
