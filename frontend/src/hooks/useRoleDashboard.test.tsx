import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useRoleDashboard, ROLE_DASHBOARD_KEY, DashboardWorkbench } from './useRoleDashboard';

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useRoleDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('uses correct query key', async () => {
    const mockData: DashboardWorkbench = {
      role: 'sales',
      scope: 'personal',
      metrics: [],
      todos: [],
      risks: [],
      quick_actions: [],
      generated_at: '2024-01-01T00:00:00Z',
    };

    const api = await import('../services/api');
    vi.mocked(api.default.get).mockResolvedValueOnce({ data: mockData });

    const { result } = renderHook(() => useRoleDashboard(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockData);
    expect(api.default.get).toHaveBeenCalledWith('/dashboard/workbench');
  });

  it('returns role and scope from response', async () => {
    const mockData: DashboardWorkbench = {
      role: 'channel_ops',
      scope: 'team',
      metrics: [{ key: 'leads', title: '渠道线索', value: 10 }],
      todos: [],
      risks: [],
      quick_actions: [],
      generated_at: '2024-01-01T00:00:00Z',
    };

    const api = await import('../services/api');
    vi.mocked(api.default.get).mockResolvedValueOnce({ data: mockData });

    const { result } = renderHook(() => useRoleDashboard(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.role).toBe('channel_ops');
    expect(result.current.data?.scope).toBe('team');
  });

  it('handles error response', async () => {
    const api = await import('../services/api');
    vi.mocked(api.default.get).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useRoleDashboard(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });
});

describe('ROLE_DASHBOARD_KEY', () => {
  it('exports correct key constant', () => {
    expect(ROLE_DASHBOARD_KEY).toBe('role-dashboard');
  });
});