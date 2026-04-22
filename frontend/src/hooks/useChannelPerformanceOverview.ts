import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '../services/api';
import { Channel } from './useChannels';
import { ChannelFullView } from './useChannelFullView';
import { UnifiedTarget } from './useUnifiedTargets';

export const CHANNEL_PERFORMANCE_OVERVIEW_KEY = 'channel-performance-overview';

export type ChannelPerformanceRow = {
  channel_id: number;
  channel_code: string;
  company_name: string;
  channel_type: string;
  status: string;
  can_edit?: boolean;
  customers_count: number;
  leads_count: number;
  opportunities_count: number;
  projects_count: number;
  total_contract_amount: number;
  performance_target: number | null;
  achieved_performance: number | null;
  completion_rate: number | null;
  is_target_met: boolean;
};

export type ChannelPerformanceOverview = {
  rows: ChannelPerformanceRow[];
  channel_count: number;
  total_contract_amount: number;
  avg_completion_rate: number;
  target_met_count: number;
};

export type ChannelPerformanceFilters = {
  year?: number;
  quarter?: number;
  month?: number;
};

const sortTargetsByPeriodDesc = (
  targets: Array<
    Pick<UnifiedTarget, 'year' | 'quarter' | 'month' | 'performance_target' | 'achieved_performance'>
  > = []
) => {
  if (!targets || targets.length === 0) {
    return [];
  }
  return [...targets].sort((a, b) => {
    const aScore = a.year * 10000 + (Number(a.quarter) || 0) * 100 + (Number(a.month) || 0);
    const bScore = b.year * 10000 + (Number(b.quarter) || 0) * 100 + (Number(b.month) || 0);
    return bScore - aScore;
  });
};

const pickTargetForFilters = (
  targets: Array<
    Pick<UnifiedTarget, 'year' | 'quarter' | 'month' | 'performance_target' | 'achieved_performance'>
  > = [],
  filters?: ChannelPerformanceFilters
) => {
  const sortedTargets = sortTargetsByPeriodDesc(targets);
  if (sortedTargets.length === 0) {
    return null;
  }

  if (filters?.month !== undefined) {
    return (
      sortedTargets.find(
        (target) =>
          (filters.year === undefined || target.year === filters.year) &&
          target.month === filters.month
      ) || null
    );
  }

  if (filters?.quarter !== undefined) {
    return (
      sortedTargets.find(
        (target) =>
          (filters.year === undefined || target.year === filters.year) &&
          target.quarter === filters.quarter &&
          target.month == null
      ) || null
    );
  }

  if (filters?.year !== undefined) {
    return (
      sortedTargets.find(
        (target) =>
          target.year === filters.year && target.quarter == null && target.month == null
      ) || null
    );
  }

  return (
    sortedTargets.find((target) => target.quarter == null && target.month == null) ||
    sortedTargets[0]
  );
};

export const useChannelPerformanceOverview = (filters?: ChannelPerformanceFilters) => {
  return useQuery({
    queryKey: [CHANNEL_PERFORMANCE_OVERVIEW_KEY, filters],
    queryFn: async (): Promise<ChannelPerformanceOverview> => {
      const channelsResponse = await api.get<Channel[]>('/channels/');
      const targetParams = new URLSearchParams();
      if (filters?.year) targetParams.append('year', String(filters.year));
      if (filters?.quarter) targetParams.append('quarter', String(filters.quarter));
      if (filters?.month) targetParams.append('month', String(filters.month));
      const targetsResponse = await api.get<UnifiedTarget[]>(
        `/unified-targets/${targetParams.toString() ? `?${targetParams.toString()}` : ''}`
      );
      const channels = channelsResponse.data || [];
      const targetRows = (targetsResponse.data || []).filter((target) => target.target_type === 'channel');

      const detailResults = await Promise.allSettled(
        channels.map((channel) =>
          api
            .get<ChannelFullView>(`/channels/${channel.id}/full-view?active_only=true`)
            .then((res) => ({ channel, fullView: res.data }))
        )
      );

      const rows: ChannelPerformanceRow[] = detailResults
        .filter(
          (
            result
          ): result is PromiseFulfilledResult<{ channel: Channel; fullView: ChannelFullView }> =>
            result.status === 'fulfilled'
        )
        .map(({ value }) => {
          const matchedTarget = pickTargetForFilters(
            targetRows.filter((target) => target.channel_id === value.channel.id),
            filters
          );
          const performanceTarget =
            matchedTarget?.performance_target !== undefined && matchedTarget?.performance_target !== null
              ? Number(matchedTarget.performance_target)
              : null;
          const achievedPerformance =
            matchedTarget?.achieved_performance !== undefined && matchedTarget?.achieved_performance !== null
              ? Number(matchedTarget.achieved_performance)
              : null;
          const completionRate =
            performanceTarget && performanceTarget > 0 && achievedPerformance !== null
              ? Number(((achievedPerformance / performanceTarget) * 100).toFixed(2))
              : null;

          return {
            channel_id: value.channel.id,
            channel_code: value.channel.channel_code,
            company_name: value.channel.company_name,
            channel_type: value.channel.channel_type,
            status: value.channel.status,
            can_edit: value.channel.can_edit,
            customers_count: value.fullView.summary.customers_count || 0,
            leads_count: value.fullView.summary.leads_count || 0,
            opportunities_count: value.fullView.summary.opportunities_count || 0,
            projects_count: value.fullView.summary.projects_count || 0,
            total_contract_amount: Number(value.fullView.summary.total_contract_amount || 0),
            performance_target: performanceTarget,
            achieved_performance: achievedPerformance,
            completion_rate: completionRate,
            is_target_met: completionRate !== null && completionRate >= 100,
          };
        })
        .sort((a, b) => b.total_contract_amount - a.total_contract_amount);

      const completionRates = rows
        .map((row) => row.completion_rate)
        .filter((rate): rate is number => rate !== null);
      const avgCompletionRate =
        completionRates.length > 0
          ? Number((completionRates.reduce((sum, rate) => sum + rate, 0) / completionRates.length).toFixed(2))
          : 0;

      return {
        rows,
        channel_count: rows.length,
        total_contract_amount: rows.reduce((sum, row) => sum + row.total_contract_amount, 0),
        avg_completion_rate: avgCompletionRate,
        target_met_count: rows.filter((row) => row.is_target_met).length,
      };
    },
  });
};

export const useRefreshChannelPerformance = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (channelId: number) => {
      await api.post(`/channels/${channelId}/refresh-performance`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CHANNEL_PERFORMANCE_OVERVIEW_KEY] });
      queryClient.invalidateQueries({ queryKey: ['channel-full-view'] });
      queryClient.invalidateQueries({ queryKey: ['channel-targets'] });
    },
  });
};
