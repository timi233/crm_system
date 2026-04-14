import React, { useState, useEffect } from 'react';
import { Modal, Button, Descriptions, Spin, Select, DatePicker, Radio, message, Space, Row, Col } from 'antd';
import { UserOutlined, PhoneOutlined } from '@ant-design/icons';
import api from '../../services/api';
import dayjs from 'dayjs';

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
  technicianId: number;
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
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [techniciansLoading, setTechniciansLoading] = useState(false);
  const [selectedTechnician, setSelectedTechnician] = useState<number>();
  const [startDate, setStartDate] = useState<dayjs.Dayjs | null>(dayjs());
  const [startPeriod, setStartPeriod] = useState<string>('上午');
  const [endDate, setEndDate] = useState<dayjs.Dayjs | null>(dayjs());
  const [endPeriod, setEndPeriod] = useState<string>('下午');
  const [workType, setWorkType] = useState<string>('售前交流');
  const [serviceMode, setServiceMode] = useState<'online' | 'offline'>('offline');

  useEffect(() => {
    if (visible) {
      fetchTechnicians();
    }
  }, [visible]);

  const fetchTechnicians = async () => {
    setTechniciansLoading(true);
    try {
      const response = await api.get<Technician[]>('/users', {
        params: { functional_role: 'TECHNICIAN' }
      });
      setTechnicians(response.data);
    } catch (error) {
      message.error('获取技术人员列表失败');
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

  const handleOk = async () => {
    if (!selectedTechnician) {
      message.warning('请选择技术人员');
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
    try {
      const formData: DispatchFormData = {
        technicianId: selectedTechnician,
        startDate: startDate.format('YYYY-MM-DD'),
        startPeriod: startPeriod,
        endDate: endDate.format('YYYY-MM-DD'),
        endPeriod: endPeriod,
        workType: workType,
        serviceMode: serviceMode,
      };
      await onSubmit(formData);
      onClose();
    } catch (error) {
      console.error('Dispatch creation failed:', error);
    }
  };

  const handleClose = () => {
    setSelectedTechnician(undefined);
    setStartDate(dayjs());
    setStartPeriod('上午');
    setEndDate(dayjs());
    setEndPeriod('下午');
    setServiceMode('offline');
    setWorkType('售前交流');
    onClose();
  };

  return (
    <Modal
      title="新增派工"
      open={visible}
      onCancel={handleClose}
      footer={[
        <Button key="cancel" onClick={handleClose}>
          取消
        </Button>,
        <Button 
          key="submit" 
          type="primary" 
          loading={loading} 
          onClick={handleOk}
          disabled={!selectedTechnician}
        >
          确认创建
        </Button>,
      ]}
      width={650}
    >
      <div style={{ marginBottom: 16 }}>
        {dispatchInfo ? (
          <Descriptions bordered column={1} size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label="客户名称">
              {dispatchInfo.customer_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="联系人">
              {dispatchInfo.contact ? (
                <span>
                  <UserOutlined style={{ marginRight: 4 }} />
                  {dispatchInfo.contact}
                </span>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="联系电话">
              {dispatchInfo.phone ? (
                <span>
                  <PhoneOutlined style={{ marginRight: 4 }} />
                  {dispatchInfo.phone}
                </span>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label={`关联${dispatchInfo.entity_type || '记录'}`}>
              {dispatchInfo.entity_name || '-'}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Spin tip="正在加载派工信息..." />
        )}

        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
              服务方式 *
            </label>
            <Radio.Group 
              value={serviceMode} 
              onChange={(e) => setServiceMode(e.target.value)}
              disabled={loading}
            >
              <Radio value="offline">线下服务（公司外勤）</Radio>
              <Radio value="online">线上服务（公司内勤）</Radio>
            </Radio.Group>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
              选择技术人员 *
            </label>
            <Select
              style={{ width: '100%' }}
              placeholder="请选择技术人员"
              value={selectedTechnician}
              onChange={setSelectedTechnician}
              loading={techniciansLoading}
              disabled={loading}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={technicians.map(t => {
                const parts = [t.name];
                if (t.department) parts.push(`(${t.department})`);
                return { value: t.id, label: parts.join(' ') };
              })}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
              预约时间区间 *
            </label>
            <Row gutter={8}>
              <Col span={6}>
                <DatePicker 
                  value={startDate}
                  onChange={(date) => setStartDate(date)}
                  disabled={loading}
                  style={{ width: '100%' }}
                  placeholder="开始日期"
                />
              </Col>
              <Col span={4}>
                <Select
                  value={startPeriod}
                  onChange={setStartPeriod}
                  disabled={loading}
                  options={TIME_PERIODS}
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={2} style={{ textAlign: 'center', paddingTop: 4 }}>
                至
              </Col>
              <Col span={6}>
                <DatePicker 
                  value={endDate}
                  onChange={(date) => setEndDate(date)}
                  disabled={loading}
                  style={{ width: '100%' }}
                  placeholder="结束日期"
                />
              </Col>
              <Col span={4}>
                <Select
                  value={endPeriod}
                  onChange={setEndPeriod}
                  disabled={loading}
                  options={TIME_PERIODS}
                  style={{ width: '100%' }}
                />
              </Col>
            </Row>
            <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
              预计时长：{calculateDuration()}
            </div>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
              工作类型 *
            </label>
            <Select
              style={{ width: '100%' }}
              value={workType}
              onChange={setWorkType}
              disabled={loading}
              options={WORK_TYPES}
            />
          </div>
        </Space>
      </div>

      <div style={{ 
        padding: 12, 
        background: '#f0f2f5', 
        borderRadius: 4,
      }}>
        <p style={{ margin: 0, fontSize: 12, color: '#999' }}>
          提示：派工申请将发送给选定的技术人员，您可以在"派工历史"中查看工单状态和进度。
        </p>
      </div>
    </Modal>
  );
};

export default DispatchModal;