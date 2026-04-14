import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Descriptions, Card, Button, Space, Tag, Form, Select, Input, Rate, Modal, message, Divider } from 'antd';
import { ArrowLeftOutlined, CheckCircleOutlined, UserAddOutlined, StarOutlined } from '@ant-design/icons';
import { useWorkOrder, useUpdateWorkOrderStatus, useAssignTechnicians, useCreateEvaluation, useEvaluations, useUsers } from '../hooks/useWorkOrders';

const { Option } = Select;
const { TextArea } = Input;

const STATUS_LABELS = { PENDING: '待处理', ACCEPTED: '已接收', IN_SERVICE: '服务中', DONE: '已完成', CANCELLED: '已取消', REJECTED: '已拒绝' };
const ORDER_TYPE_LABELS = { CF: '首次安装', CO: '续保服务', MF: '维修保养', MO: '其他' };
const PRIORITY_LABELS = { NORMAL: '普通', URGENT: '紧急', VERY_URGENT: '非常紧急' };
const STATUS_FLOW = ['PENDING', 'ACCEPTED', 'IN_SERVICE', 'DONE'];

const WorkOrderDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const workOrderId = id ? parseInt(id, 10) : null;
  const [isAssignModalVisible, setIsAssignModalVisible] = useState(false);
  const [isEvaluationModalVisible, setIsEvaluationModalVisible] = useState(false);
  const [serviceSummary, setServiceSummary] = useState('');
  const { data: workOrder, isLoading } = useWorkOrder(workOrderId);
  const { data: users = [] } = useUsers();
  const { data: evaluations = [] } = useEvaluations(workOrderId || undefined);
  const updateStatusMutation = useUpdateWorkOrderStatus();
  const assignTechniciansMutation = useAssignTechnicians();
  const createEvaluationMutation = useCreateEvaluation();
  const [evaluationForm] = Form.useForm();
  const [assignForm] = Form.useForm();
  const technicianOptions = users.filter(u => u.role && !u.role.includes('customer')).map(u => ({ value: u.id, label: u.name }));

  const getStatusColor = (status) => {
    const colors = { PENDING: 'blue', ACCEPTED: 'green', IN_SERVICE: 'orange', DONE: 'success', CANCELLED: 'red', REJECTED: 'red' };
    return colors[status] || 'default';
  };

  const handleStatusChange = async (newStatus) => {
    if (!workOrderId) return;
    let summary = serviceSummary;
    if (newStatus === 'DONE' && !summary) {
      Modal.info({ title: '请填写服务摘要', content: <Input.TextArea rows={4} placeholder="请简要描述服务内容和结果" value={summary} onChange={(e) => setServiceSummary(e.target.value)} />, onOk: () => handleStatusChange(newStatus) });
      return;
    }
    try {
      await updateStatusMutation.mutateAsync({ id: workOrderId, statusUpdate: { status: newStatus, service_summary: summary || undefined } });
      message.success('状态更新成功');
      setServiceSummary('');
    } catch (error) { if (error?.response?.data?.detail) message.error(error.response.data.detail); }
  };

  const handleAssignTechnicians = async () => {
    if (!workOrderId) return;
    try {
      const values = await assignForm.validateFields();
      await assignTechniciansMutation.mutateAsync({ id: workOrderId, assignRequest: { technician_ids: values.technician_ids } });
      message.success('技术员分配成功');
      setIsAssignModalVisible(false);
      assignForm.resetFields();
    } catch (error) { if (error?.response?.data?.detail) message.error(error.response.data.detail); }
  };

  const handleCreateEvaluation = async () => {
    if (!workOrderId) return;
    try {
      const values = await evaluationForm.validateFields();
      await createEvaluationMutation.mutateAsync({ work_order_id: workOrderId, quality_rating: values.quality_rating, response_rating: values.response_rating, customer_feedback: values.customer_feedback, improvement_suggestion: values.improvement_suggestion, recommend: values.recommend });
      message.success('评价提交成功');
      setIsEvaluationModalVisible(false);
      evaluationForm.resetFields();
    } catch (error) { if (error?.response?.data?.detail) message.error(error.response.data.detail); }
  };

  const nextStatus = workOrder?.status ? STATUS_FLOW[STATUS_FLOW.indexOf(workOrder.status) + 1] : null;
  const canEvaluate = workOrder?.status === 'DONE' && evaluations.length === 0;
  if (isLoading || !workOrder) return <Card loading />;

  return (
    <Card title={<Space><Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/work-orders')}>返回</Button><span>{workOrder.work_order_no} - {workOrder.customer_name}</span></Space>}
      extra={<Space>
        {workOrder.status !== 'DONE' && workOrder.status !== 'CANCELLED' && workOrder.status !== 'REJECTED' && <><Button type="primary" icon={<CheckCircleOutlined />} onClick={() => nextStatus && handleStatusChange(nextStatus)} disabled={!nextStatus}>{nextStatus ? `流转到${STATUS_LABELS[nextStatus]}` : '已完成'}</Button>{workOrder.status === 'PENDING' && <Button icon={<UserAddOutlined />} onClick={() => setIsAssignModalVisible(true)}>分配技术员</Button>}</>}
        {canEvaluate && <Button type="primary" icon={<StarOutlined />} onClick={() => setIsEvaluationModalVisible(true)}>评价服务</Button>}
      </Space>}>
      <Descriptions bordered column={2} size="middle">
        <Descriptions.Item label="工单号">{workOrder.work_order_no}</Descriptions.Item>
        <Descriptions.Item label="状态"><Tag color={getStatusColor(workOrder.status)}>{STATUS_LABELS[workOrder.status]}</Tag></Descriptions.Item>
        <Descriptions.Item label="订单类型">{ORDER_TYPE_LABELS[workOrder.order_type]}</Descriptions.Item>
        <Descriptions.Item label="优先级"><Tag color={workOrder.priority === 'VERY_URGENT' ? 'red' : workOrder.priority === 'URGENT' ? 'orange' : 'blue'}>{PRIORITY_LABELS[workOrder.priority]}</Tag></Descriptions.Item>
        <Descriptions.Item label="客户名称">{workOrder.customer_name}</Descriptions.Item>
        <Descriptions.Item label="提交人">{workOrder.submitter_name || '-'}</Descriptions.Item>
        <Descriptions.Item label="技术员" span={2}>{workOrder.technician_names.length > 0 ? <Space>{workOrder.technician_names.map((name, i) => <Tag key={i} color="blue">{name}</Tag>)}</Space> : <span style={{ color: '#999' }}>未分配</span>}</Descriptions.Item>
        <Descriptions.Item label="预计开始时间" span={2}>{workOrder.estimated_start_date ? new Date(workOrder.estimated_start_date).toLocaleDateString('zh-CN') : '-'}</Descriptions.Item>
        <Descriptions.Item label="预计结束时间" span={2}>{workOrder.estimated_end_date ? new Date(workOrder.estimated_end_date).toLocaleDateString('zh-CN') : '-'}</Descriptions.Item>
        <Descriptions.Item label="服务摘要" span={2}>{workOrder.service_summary || '-'}</Descriptions.Item>
        {workOrder.cancel_reason && <Descriptions.Item label="取消原因" span={2}><span style={{ color: '#ff4d4f' }}>{workOrder.cancel_reason}</span></Descriptions.Item>}
        <Descriptions.Item label="描述" span={2}>{workOrder.description}</Descriptions.Item>
        <Descriptions.Item label="创建时间">{workOrder.created_at ? new Date(workOrder.created_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
      </Descriptions>
      {evaluations.length > 0 && <><Divider orientation="left">客户评价</Divider><Card type="inner" style={{ marginTop: 16 }}><Space direction="vertical" size="middle" style={{ width: '100%' }}>{evaluations.map(e => <div key={e.id}><Space><span>服务质量:</span><Rate disabled defaultValue={e.quality_rating} /><Divider type="vertical" /><span>响应速度:</span><Rate disabled defaultValue={e.response_rating} />{e.customer_feedback && <><Divider type="vertical" /><span>反馈：{e.customer_feedback}</span></>}<Divider type="vertical" /><span>{e.recommend ? '会推荐' : '不会推荐'}</span></Space></div>)}</Space></Card></>}
      <Modal title="分配技术员" open={isAssignModalVisible} onOk={handleAssignTechnicians} onCancel={() => { setIsAssignModalVisible(false); assignForm.resetFields(); }} okText="确认分配" cancelText="取消" confirmLoading={assignTechniciansMutation.isPending}><Form form={assignForm} layout="vertical"><Form.Item name="technician_ids" label="选择技术员" rules={[{ required: true, message: '请至少选择一名技术员!' }]}><Select mode="multiple" placeholder="请选择技术员" showSearch optionFilterProp="children">{technicianOptions.map(opt => <Option key={opt.value} value={opt.value}>{opt.label}</Option>)}</Select></Form.Item></Form></Modal>
      <Modal title="服务评价" open={isEvaluationModalVisible} onOk={handleCreateEvaluation} onCancel={() => { setIsEvaluationModalVisible(false); evaluationForm.resetFields(); }} okText="提交评价" cancelText="取消" width={500} confirmLoading={createEvaluationMutation.isPending}><Form form={evaluationForm} layout="vertical"><Form.Item name="quality_rating" label="服务质量" rules={[{ required: true, message: '请评分!' }]}><Rate /></Form.Item><Form.Item name="response_rating" label="响应速度" rules={[{ required: true, message: '请评分!' }]}><Rate /></Form.Item><Form.Item name="customer_feedback" label="客户反馈"><TextArea rows={3} placeholder="请描述您的服务体验" /></Form.Item><Form.Item name="improvement_suggestion" label="改进建议"><TextArea rows={2} placeholder="帮助我们提供更好服务的建议" /></Form.Item><Form.Item name="recommend" label="是否推荐" valuePropName="checked" rules={[{ required: true, message: '请选择是否推荐!' }]}><Select><Option value={true}>会推荐</Option><Option value={false}>不会推荐</Option></Select></Form.Item></Form></Modal>
    </Card>
  );
};

export default WorkOrderDetailPage;
