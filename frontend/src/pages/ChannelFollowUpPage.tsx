import React, { useMemo } from 'react';
import { Breadcrumb, Button, Select, Space, Typography } from 'antd';
import { useNavigate, useSearchParams } from 'react-router-dom';

import FollowUpList from '../components/lists/FollowUpList';
import { useChannels } from '../hooks/useChannels';

const ChannelFollowUpPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { data: channels = [] } = useChannels();

  const selectedChannelId = useMemo(() => {
    const rawValue = searchParams.get('channel_id');
    if (!rawValue) {
      return undefined;
    }
    const parsedValue = Number(rawValue);
    return Number.isNaN(parsedValue) ? undefined : parsedValue;
  }, [searchParams]);

  const handleChannelChange = (value?: number) => {
    const nextParams = new URLSearchParams(searchParams);
    if (value === undefined) {
      nextParams.delete('channel_id');
    } else {
      nextParams.set('channel_id', String(value));
    }
    setSearchParams(nextParams);
  };

  const selectedChannel = useMemo(
    () => channels.find((channel) => channel.id === selectedChannelId),
    [channels, selectedChannelId]
  );

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <div>
        <Breadcrumb
          items={[
            { title: '渠道管理' },
            { title: '渠道跟进' },
          ]}
          style={{ marginBottom: 8 }}
        />
        <Typography.Title level={3} style={{ margin: 0 }}>
          渠道跟进
        </Typography.Title>
        <Typography.Text type="secondary">
          集中维护渠道拜访记录，支持新增、编辑、查看和按渠道检索。
        </Typography.Text>
      </div>
      <Space wrap>
        <Select
          allowClear
          showSearch
          placeholder="按渠道筛选"
          style={{ width: 320 }}
          optionFilterProp="label"
          value={selectedChannelId}
          onChange={handleChannelChange}
          options={channels.map((channel) => ({
            value: channel.id,
            label: `${channel.channel_code} - ${channel.company_name}`,
          }))}
        />
        {selectedChannelId ? (
          <Button onClick={() => navigate(`/channels/${selectedChannelId}/full`)}>
            查看渠道档案
          </Button>
        ) : null}
      </Space>
      {selectedChannel ? (
        <Typography.Text type="secondary">
          当前查看：{selectedChannel.channel_code} - {selectedChannel.company_name}
        </Typography.Text>
      ) : null}
      <FollowUpList mode="channel" channel_id={selectedChannelId} />
    </Space>
  );
};

export default ChannelFollowUpPage;
