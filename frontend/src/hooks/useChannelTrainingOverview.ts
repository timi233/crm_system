import { useQuery } from '@tanstack/react-query';

import api from '../services/api';
import { Channel } from './useChannels';
import { FollowUp } from './useFollowUps';

export const CHANNEL_TRAINING_OVERVIEW_KEY = 'channel-training-overview';

type ExecutionPlan = {
  id: number;
  channel_id: number;
  channel_name?: string | null;
  user_id: number;
  user_name?: string | null;
  plan_type: string;
  plan_category?: string;
  plan_period: string;
  plan_content: string;
  execution_status?: string | null;
  next_steps?: string | null;
  status: string;
  created_at?: string | null;
};

export type ChannelTrainingPlanRow = {
  id: number;
  channel_id: number;
  channel_name: string;
  plan_type: string;
  plan_period: string;
  plan_content: string;
  status: string;
  user_name?: string | null;
  created_at?: string | null;
};

export type ChannelTrainingFollowUpRow = {
  id: number;
  channel_id?: number;
  channel_name?: string;
  follow_up_date: string;
  follow_up_method: string;
  visit_purpose?: string;
  follow_up_content: string;
  follower_name?: string;
};

export type ChannelTrainingOverview = {
  training_plan_count: number;
  completed_training_plan_count: number;
  training_follow_up_count: number;
  covered_channel_count: number;
  plans: ChannelTrainingPlanRow[];
  follow_ups: ChannelTrainingFollowUpRow[];
};

const containsTrainingKeyword = (value?: string | null) => (value || '').includes('培训');

export const useChannelTrainingOverview = () => {
  return useQuery({
    queryKey: [CHANNEL_TRAINING_OVERVIEW_KEY],
    queryFn: async (): Promise<ChannelTrainingOverview> => {
      const [followUpsResult, plansResult, channelsResult] = await Promise.allSettled([
        api.get<FollowUp[]>('/follow-ups/?follow_up_type=channel'),
        api.get<ExecutionPlan[]>('/execution-plans/?plan_category=training'),
        api.get<Channel[]>('/channels/'),
      ]);

      const followUps =
        followUpsResult.status === 'fulfilled' ? followUpsResult.value.data || [] : [];
      const plans = plansResult.status === 'fulfilled' ? plansResult.value.data || [] : [];
      const channels =
        channelsResult.status === 'fulfilled' ? channelsResult.value.data || [] : [];

      const channelNameMap = new Map<number, string>();
      channels.forEach((channel) => {
        channelNameMap.set(channel.id, channel.company_name);
      });

      const trainingPlans = plans
        .map((plan) => ({
          id: plan.id,
          channel_id: plan.channel_id,
          channel_name:
            plan.channel_name ||
            channelNameMap.get(plan.channel_id) ||
            `渠道#${plan.channel_id}`,
          plan_type: plan.plan_type,
          plan_period: plan.plan_period,
          plan_content: plan.plan_content,
          status: plan.status,
          user_name: plan.user_name,
          created_at: plan.created_at,
        }))
        .sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')));

      const trainingFollowUps = followUps
        .filter(
          (followUp) =>
            containsTrainingKeyword(followUp.visit_purpose) ||
            containsTrainingKeyword(followUp.follow_up_content)
        )
        .map((followUp) => ({
          id: followUp.id,
          channel_id: followUp.channel_id,
          channel_name:
            followUp.channel_name ||
            (followUp.channel_id ? channelNameMap.get(followUp.channel_id) : undefined) ||
            (followUp.channel_id ? `渠道#${followUp.channel_id}` : undefined),
          follow_up_date: followUp.follow_up_date,
          follow_up_method: followUp.follow_up_method,
          visit_purpose: followUp.visit_purpose,
          follow_up_content: followUp.follow_up_content,
          follower_name: followUp.follower_name,
        }))
        .sort((a, b) => String(b.follow_up_date || '').localeCompare(String(a.follow_up_date || '')));

      const coveredChannelIds = new Set<number>();
      trainingPlans.forEach((plan) => coveredChannelIds.add(plan.channel_id));
      trainingFollowUps.forEach((followUp) => {
        if (followUp.channel_id) {
          coveredChannelIds.add(followUp.channel_id);
        }
      });

      return {
        training_plan_count: trainingPlans.length,
        completed_training_plan_count: trainingPlans.filter((plan) => plan.status === 'completed').length,
        training_follow_up_count: trainingFollowUps.length,
        covered_channel_count: coveredChannelIds.size,
        plans: trainingPlans,
        follow_ups: trainingFollowUps,
      };
    },
  });
};
