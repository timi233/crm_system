import React, { useState, useEffect } from 'react';
import { App, Button, Descriptions, Skeleton, Select, DatePicker, Radio, Space, Row, Col, Steps, Result, Typography, Tag } from 'antd';
import { UserOutlined, PhoneOutlined, CheckCircleOutlined, LoadingOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons';
import api from '../../services/api';
import dayjs from 'dayjs';
import PageModal from './PageModal';

const { Text } = Typography;

interface DispatchInfo {
  customer_name?: string;
  contact?: string;
  phone?: string;
  entity_name?: string;
  entity_type?: string;
}

interface Technician {
  id: number;
  name: string;
  phone?: string;
  department?: string;
}

interface DispatchModalProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: (data: DispatchFormData) => Promise<void>;
  loading: boolean;
  dispatchInfo?: DispatchInfo;
}

interface DispatchFormData {
  technicianIds: number[];
  startDate: string;
  startPeriod: string;
  endDate: string;
  endPeriod: string;
  workType: string;
  serviceMode: 'online' | 'offline';
}

const WORK_TYPES = [
  { value: '售前交流', label: '售前交流' },
  { value: '功能测试', label: '功能测试' },
  { value: '实施交付', label: '实施交付' },
  { value: '问题处理', label: '问题处理' },
  { value: '培训', label: '培训' },
  { value: '巡检', label: '巡检' },
  { value: '其他', label: '其他' },
];

const TIME_PERIODS = [
  { value: '上午', label: '上午' },
  { value: '下午', label: '下午' },
];

const DispatchModal: React.FC<DispatchModalProps> = ({
  visible,
  onClose,
  onSubmit,
  loading,
  dispatchInfo,
}) => {
  const { message } = App.useApp();
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [techniciansLoading, setTechniciansLoading] = useState(false);
  const [selectedTechnicians, setSelectedTechnicians] = useState<number[]>([]);
  const [startDate, setStartDate] = useState<dayjs.Dayjs | null>(dayjs());
  const [startPeriod, setStartPeriod] = useState<string>('上午');
  const [endDate, setEndDate] = useState<dayjs.Dayjs | null>(dayjs());
  const [endPeriod, setEndPeriod] = useState<string>('下午');
  const [workType, setWorkType] = useState<string>('售前交流');
  const [serviceMode, setServiceMode] = useState<'online' | 'offline'>('offline');
  const [currentStep, setCurrentStep] = useState(0);
  const [submitStatus, setSubmitStatus] = useState<'pending' | 'success' | 'error' | null>(null);

  useEffect(() => {
    if (visible) {
      fetchTechnicians();
    }
  }, [visible]);

  const fetchTechnicians = async () => {
    setTechniciansLoading(true);
    try {
      const response = await api.get<Technician[]>('/dispatch/technicians');
      setTechnicians(response.data);
    } catch (error) {
      message.error('获取服务工程师列表失败');
    } finally {
      setTechniciansLoading(false);
    }
  };

  const isValidTimeOrder = () => {
    if (!startDate || !endDate) return true;
    if (endDate.isBefore(startDate, 'day')) return false;
    if (endDate.isSame(startDate, 'day')) {
      if (startPeriod === '下午' && endPeriod === '上午') return false;
    }
    return true;
  };

  const calculateDuration = () => {
    if (!startDate || !endDate) return '-';
    if (!isValidTimeOrder()) return '无效';
    const days = endDate.diff(startDate, 'day');
    let duration = days;
    if (startPeriod === '上午' && endPeriod === '下午') {
      duration = days + 1;
    } else if (startPeriod === '下午' && endPeriod === '上午') {
      duration = days;
    } else if (startPeriod === endPeriod) {
      duration = days + 0.5;
    }
    return `${duration}天`;
  };

const resetFormState = () => {
    setSelectedTechnicians([]);
    setStartDate(dayjs());
    setStartPeriod('上午');
    setEndDate(dayjs());
    setEndPeriod('下午');
    setServiceMode('offline');
    setWorkType('售前交流');
    setCurrentStep(0);
    setSubmitStatus(null);
  };

  const handleOk = async () => {
    if (selectedTechnicians.length === 0) {
      message.warning('请选择至少一位服务工程师');
      return;
    }
    if (!startDate || !endDate) {
      message.warning('请选择预约时间');
      return;
    }
    if (!workType) {
      message.warning('请选择工作类型');
      return;
    }
    if (!isValidTimeOrder()) {
      message.warning('结束时间不能早于开始时间（同一天时上午应在下午之前）');
      return;
    }

    setCurrentStep(1);
    setSubmitStatus('pending');

    try {
      const formData: DispatchFormData = {
        technicianIds: selectedTechnicians,
        startDate: startDate.format('YYYY-MM-DD'),
        startPeriod: startPeriod,
        endDate: endDate.format('YYYY-MM-DD'),
        endPeriod: endPeriod,
        workType: workType,
        serviceMode: serviceMode,
      };
      await onSubmit(formData);
      setCurrentStep(2);
      setSubmitStatus('success');
      message.success('派工创建成功！');
      setTimeout(() => {
        resetFormState();
        onClose();
      }, 1500);
    } catch (error) {
      setCurrentStep(1);
      setSubmitStatus('error');
      message.error('派工创建失败，请重试');
    }
  };

  const handleClose = () => {
    resetFormState();
    onClose();
  };

  return (
    <PageModal
      title="申请技术专家支持"
      open={visible}
      onClose={handleClose}
      width={640}
      footer={
        submitStatus === 'success' ? null : (
          <Space size={12}>
            <Button onClick={handleClose}>放弃</Button>
            <Button
              type="primary"
              className="btn--gradient"
              loading={submitStatus === 'pending'}
              onClick={handleOk}
              disabled={selectedTechnicians.length === 0 || submitStatus === 'pending'}
            >
              {submitStatus === 'pending' ? '正在提交申请...' : '确认发布派工'}
            </Button>
          </Space>
        )
      }
    >
      <Steps
        current={currentStep}
        size="small"
        style={{ marginBottom: 32 }}
        items={[
          { title: '填写申请', status: currentStep === 0 ? 'process' : 'finish' },
          { title: '提交审批', status: currentStep === 1 && submitStatus === 'pending' ? 'process' : currentStep > 1 ? 'finish' : 'wait', icon: submitStatus === 'pending' ? <LoadingOutlined /> : undefined },
          { title: '完成', status: currentStep === 2 ? 'finish' : 'wait', icon: submitStatus === 'success' ? <CheckCircleOutlined /> : submitStatus === 'error' ? <CloseCircleOutlined /> : undefined },
        ]}
      />

      {submitStatus === 'success' && (
        <Result
          status="success"
          title="派工申请已成功提交"
          subTitle="工单已通过飞书即时推送到选定的技术专家，请在详情页查看进度反馈。"
          extra={<Button type="primary" className="btn--gradient" onClick={handleClose}>回到列表</Button>}
        />
      )}

      {submitStatus === 'error' && (
        <Result
          status="error"
          title="系统响应异常"
          subTitle="暂时无法处理您的派工申请，请检查网络连接或稍后再试。"
          extra={<Button type="primary" onClick={() => { setSubmitStatus(null); setCurrentStep(0); }}>重新发起申请</Button>}
        />
      )}

      {!submitStatus && (
        <div className="fade-in">
          {dispatchInfo ? (
            <div style={{ background: '#f8fafc', padding: '16px 20px', borderRadius: '12px', border: '1px solid #f1f5f9', marginBottom: 24 }}>
              <Descriptions column={2} size="small">
                <Descriptions.Item label="客户名称" span={2}>
                  <span style={{ fontWeight: 700, color: '#0f172a' }}>{dispatchInfo.customer_name || '-'}</span>
                </Descriptions.Item>
                <Descriptions.Item label="联系人">
                  <Space size={4}>
                    <UserOutlined style={{ color: '#64748b' }} />
                    {dispatchInfo.contact || '-'}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="联系电话">
                  <Space size={4}>
                    <PhoneOutlined style={{ color: '#64748b' }} />
                    {dispatchInfo.phone || '-'}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label={`关联${dispatchInfo.entity_type || '记录'}`} span={2}>
                  <Text type="secondary">{dispatchInfo.entity_name || '-'}</Text>
                </Descriptions.Item>
              </Descriptions>
            </div>
          ) : (
            <Skeleton active paragraph={{ rows: 3 }} />
          )}

          <Space direction="vertical" size={20} style={{ width: '100%' }}>
            <div>
              <div style={{ marginBottom: 8, fontWeight: 700, color: '#475569', fontSize: '13px' }}>
                服务交付方式 <Text type="danger">*</Text>
              </div>
              <Radio.Group
                value={serviceMode}
                onChange={(e) => setServiceMode(e.target.value)}
                disabled={loading}
                optionType="button"
                buttonStyle="solid"
              >
                <Radio value="offline">线下外勤服务</Radio>
                <Radio value="online">线上远程支持</Radio>
              </Radio.Group>
            </div>

            <div>
              <div style={{ marginBottom: 8, fontWeight: 700, color: '#475569', fontSize: '13px' }}>
                选择执行专家 <Text type="danger">*</Text>
              </div>
              <Select
                mode="multiple"
                style={{ width: '100%' }}
                placeholder="搜索并选择服务工程师（可多选）"
                value={selectedTechnicians}
                onChange={setSelectedTechnicians}
                loading={techniciansLoading}
                disabled={loading}
                showSearch
                size="large"
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={technicians.map(t => {
                  const parts = [t.name];
                  if (t.department) parts.push(`(${t.department})`);
                  return { value: t.id, label: parts.join(' ') };
                })}
              />
              {selectedTechnicians.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Tag color="blue" style={{ border: 'none', background: '#e0e7ff', color: '#4338ca' }}>
                    已选中 {selectedTechnicians.length} 位工程师
                  </Tag>
                </div>
              )}
            </div>

            <div>
              <div style={{ marginBottom: 8, fontWeight: 700, color: '#475569', fontSize: '13px' }}>
                预约时间区间 <Text type="danger">*</Text>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
                <DatePicker
                  value={startDate}
                  onChange={(date) => setStartDate(date)}
                  disabled={loading}
                  style={{ width: 140 }}
                  placeholder="开始日期"
                />
                <Select
                  value={startPeriod}
                  onChange={setStartPeriod}
                  disabled={loading}
                  options={TIME_PERIODS}
                  style={{ width: 80 }}
                />
                <Text type="secondary">至</Text>
                <DatePicker
                  value={endDate}
                  onChange={(date) => setEndDate(date)}
                  disabled={loading}
                  style={{ width: 140 }}
                  placeholder="结束日期"
                />
                <Select
                  value={endPeriod}
                  onChange={setEndPeriod}
                  disabled={loading}
                  options={TIME_PERIODS}
                  style={{ width: 80 }}
                />
              </div>
              <div style={{ marginTop: 8, textAlign: 'right' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  预计投入工时：<span style={{ fontWeight: 700, color: '#0052cc' }}>{calculateDuration()}</span>
                </Text>
              </div>
            </div>

            <div>
              <div style={{ marginBottom: 8, fontWeight: 700, color: '#475569', fontSize: '13px' }}>
                工作类型定义 <Text type="danger">*</Text>
              </div>
              <Select
                style={{ width: '100%' }}
                value={workType}
                onChange={setWorkType}
                disabled={loading}
                options={WORK_TYPES}
                size="large"
              />
            </div>
          </Space>

          <div style={{
            padding: '16px',
            background: '#fff7ed',
            borderRadius: '12px',
            border: '1px solid #ffedd5',
            marginTop: 24,
            display: 'flex',
            gap: '12px'
          }}>
            <WarningOutlined style={{ color: '#f59e0b', marginTop: '2px' }} />
            <p style={{ margin: 0, fontSize: '12px', color: '#9a3412', lineHeight: 1.5 }}>
              <b>派工须知：</b>提交后申请将立即通过飞书推送给相关负责人。请确保已与工程师进行过初步沟通，并真实准确填写预计时长。
            </p>
          </div>
        </div>
      )}
    </PageModal>
  );
};

export default DispatchModal;
