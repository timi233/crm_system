import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Button, Space, Input, message, Spin, Modal, List, Avatar } from 'antd';
import { ArrowLeftOutlined, SaveOutlined, SendOutlined, RollbackOutlined, SyncOutlined, CommentOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { useWorkReport, useUpdateWorkReport, useSubmitWorkReport, useWithdrawWorkReport, useRegenerateSnapshot } from '../hooks/useWorkReports';
import { useNotifications } from '../hooks/useNotifications';
import WorkReportSummaryPanel from '../components/work-reports/WorkReportSummaryPanel';
import api from '../services/api';

const { TextArea } = Input;
const { confirm } = Modal;

type ReportStatus = 'draft' | 'submitted' | 'withdrawn';
type ReportType = 'daily' | 'weekly';

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

const WorkReportDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { capabilities } = useSelector((state: RootState) => state.auth);
  const reportId = Number(id);
  const hasValidReportId = Number.isInteger(reportId) && reportId > 0;

  const { data: report, isLoading, error } = useWorkReport(reportId, hasValidReportId);
  const updateMutation = useUpdateWorkReport();
  const submitMutation = useSubmitWorkReport();
  const withdrawMutation = useWithdrawWorkReport();
  const regenerateMutation = useRegenerateSnapshot();

  const [remark, setRemark] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState<any[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const { refetch: refetchNotifications } = useNotifications();

  useEffect(() => {
    if (report) {
      setRemark(report.remark || '');
      fetchComments();
    }
  }, [report]);

  const fetchComments = async () => {
    setCommentsLoading(true);
    try {
      const { data } = await api.get(`/work-reports/${reportId}/comments`);
      setComments(data);
    } catch {
      message.error('加载评论失败');
    } finally {
      setCommentsLoading(false);
    }
  };

  const handleCommentSubmit = async () => {
    if (!commentText.trim()) {
      message.warning('评论内容不能为空');
      return;
    }
    try {
      await api.post(`/work-reports/${reportId}/comments`, { content: commentText });
      message.success('评论成功');
      setCommentText('');
      await fetchComments();
      refetchNotifications();
    } catch {
      message.error('评论失败');
    }
  };

  if (isLoading) {
    return (
      <Card>
        <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
      </Card>
    );
  }

  if (!hasValidReportId || error || !report) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          加载失败或报告不存在
          <Button onClick={() => navigate('/work-reports')} style={{ marginLeft: 16 }}>
            返回列表
          </Button>
        </div>
      </Card>
    );
  }

  const canEdit = report.status === 'draft' || report.status === 'withdrawn';
  const canSubmit = canEdit && Boolean(capabilities['work_report:submit']);
  const canWithdraw = report.status === 'submitted' && Boolean(capabilities['work_report:withdraw']);
  const canRegenerate = canEdit && Boolean(capabilities['work_report:update']);

  const handleSave = async () => {
    try {
      await updateMutation.mutateAsync({
        id: reportId,
        data: { remark },
      });
      message.success('保存成功');
      setIsEditing(false);
    } catch {
      message.error('保存失败');
    }
  };

  const handleSubmit = () => {
    confirm({
      title: '提交报告',
      content: '确定要提交此报告吗？提交后不可直接编辑内容。',
      onOk: async () => {
        try {
          await submitMutation.mutateAsync(reportId);
          message.success('提交成功');
        } catch {
          message.error('提交失败');
        }
      },
    });
  };

  const handleWithdraw = () => {
    confirm({
      title: '撤回报告',
      content: '确定要撤回此报告吗？撤回后可以重新编辑。',
      onOk: async () => {
        try {
          await withdrawMutation.mutateAsync(reportId);
          message.success('撤回成功');
        } catch {
          message.error('撤回失败');
        }
      },
    });
  };

  const handleRegenerate = () => {
    confirm({
      title: '重新生成汇总',
      content: '确定要重新生成结构化汇总吗？这将覆盖当前汇总数据。',
      onOk: async () => {
        try {
          await regenerateMutation.mutateAsync(reportId);
          message.success('重新生成成功');
        } catch {
          message.error('重新生成失败');
        }
      },
    });
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/work-reports')}>
            返回列表
          </Button>
        </div>

        <Descriptions bordered column={2}>
          <Descriptions.Item label="报告类型">
            <Tag color={report.report_type === 'daily' ? 'blue' : 'purple'}>
              {TYPE_LABELS[report.report_type]}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={STATUS_COLORS[report.status]}>
              {STATUS_LABELS[report.status]}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="报告日期">
            {report.report_type === 'weekly' && report.week_start && report.week_end
              ? `${report.week_start} ~ ${report.week_end}`
              : report.report_date}
          </Descriptions.Item>
          <Descriptions.Item label="提交时间">
            {report.submitted_at ? dayjs(report.submitted_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {report.created_at ? dayjs(report.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="角色">
            {report.owner_role || '-'}
          </Descriptions.Item>
        </Descriptions>

        <div style={{ marginTop: 16 }}>
          <Space>
            {canEdit && (
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={updateMutation.isPending}
                disabled={!isEditing}
              >
                保存备注
              </Button>
            )}
            {canSubmit && (
              <Button
                icon={<SendOutlined />}
                onClick={handleSubmit}
                loading={submitMutation.isPending}
              >
                提交报告
              </Button>
            )}
            {canWithdraw && (
              <Button
                icon={<RollbackOutlined />}
                onClick={handleWithdraw}
                loading={withdrawMutation.isPending}
              >
                撤回报告
              </Button>
            )}
            {canRegenerate && (
              <Button
                icon={<SyncOutlined />}
                onClick={handleRegenerate}
                loading={regenerateMutation.isPending}
              >
                重新生成汇总
              </Button>
            )}
          </Space>
        </div>
      </Card>

      <WorkReportSummaryPanel
        snapshot={report.structured_snapshot}
        reportType={report.report_type}
      />

      <Card title="备注">
        {canEdit ? (
          <>
            {!isEditing && (
              <Button onClick={() => setIsEditing(true)} style={{ marginBottom: 16 }}>
                编辑备注
              </Button>
            )}
            {isEditing ? (
              <TextArea
                value={remark}
                onChange={(e) => setRemark(e.target.value)}
                rows={4}
                placeholder="请输入备注内容..."
                style={{ marginBottom: 16 }}
              />
            ) : (
              <div style={{ minHeight: 100, padding: 16, background: '#f5f5f5', borderRadius: 4 }}>
                {remark || '暂无备注'}
              </div>
            )}
          </>
        ) : (
          <div style={{ minHeight: 100, padding: 16, background: '#f5f5f5', borderRadius: 4 }}>
            {remark || '暂无备注'}
          </div>
        )}
      </Card>

      <Card
        title={
          <Space>
            <CommentOutlined />
            评论
          </Space>
        }
      >
        <List
          dataSource={comments}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta
                avatar={<Avatar style={{ backgroundColor: '#1890ff' }}>{item.user_name?.[0]?.toUpperCase()}</Avatar>}
                title={
                  <Space>
                    <span>{item.user_name || '未知用户'}</span>
                    <span style={{ color: '#999', fontSize: 12 }}>
                      {dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}
                    </span>
                  </Space>
                }
                description={item.content}
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无评论' }}
          style={{ marginBottom: 16 }}
        />
        <Space.Compact style={{ width: '100%' }}>
          <Input.TextArea
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            placeholder="输入评论内容..."
            autoSize={{ minRows: 2, maxRows: 6 }}
            onPressEnter={(e) => {
              if (e.ctrlKey || e.metaKey) {
                handleCommentSubmit();
              }
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleCommentSubmit}
            loading={commentsLoading}
            disabled={!commentText.trim()}
            style={{ borderRadius: 0 }}
          >
            发送
          </Button>
        </Space.Compact>
      </Card>
    </Space>
  );
};

export default WorkReportDetailPage;
