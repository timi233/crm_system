import React from 'react';
import { Empty, List, Tag, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import BrandCard from '../common/BrandCard';
import { DashboardRiskItem } from '../../hooks/useRoleDashboard';

const { Text } = Typography;

type Props = {
  risks: DashboardRiskItem[];
};

const SEVERITY_COLORS: Record<string, string> = {
  low: 'blue',
  medium: 'orange',
  high: 'red',
  critical: 'magenta',
};

const DashboardRiskList: React.FC<Props> = ({ risks }) => {
  const navigate = useNavigate();

  return (
    <BrandCard title="风险提醒" variant="secondary">
      {risks.length === 0 ? (
        <Empty description="暂无风险提醒" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={risks}
          renderItem={(item) => (
            <List.Item
              onClick={() => item.link && navigate(item.link)}
              style={{ cursor: item.link ? 'pointer' : 'default' }}
            >
              <List.Item.Meta
                title={
                  <>
                    <Tag color={SEVERITY_COLORS[item.severity || 'low'] || 'default'}>
                      {item.severity || 'low'}
                    </Tag>
                    {item.title}
                  </>
                }
                description={item.description || ' '}
              />
              {item.link && <Text type="secondary">查看</Text>}
            </List.Item>
          )}
        />
      )}
    </BrandCard>
  );
};

export default DashboardRiskList;
