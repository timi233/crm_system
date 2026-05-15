import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getApiBaseUrl, getApiUrl, formatErrorDetail } from './api';

vi.mock('../utils/appFeedback', () => ({
  appMessage: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

describe('getApiBaseUrl', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
  });

  it('returns /api by default when VITE_API_URL is not set', () => {
    vi.stubEnv('VITE_API_URL', undefined);
    expect(getApiBaseUrl()).toBe('/api');
  });

  it('returns VITE_API_URL when set', () => {
    vi.stubEnv('VITE_API_URL', 'http://api.example.com');
    expect(getApiBaseUrl()).toBe('http://api.example.com');
  });

  it('returns /api when VITE_API_URL is empty string', () => {
    vi.stubEnv('VITE_API_URL', '');
    expect(getApiBaseUrl()).toBe('/api');
  });
});

describe('getApiUrl', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
  });

  it('constructs URL with default base', () => {
    vi.stubEnv('VITE_API_URL', undefined);
    expect(getApiUrl('/users')).toBe('/api/users');
  });

  it('constructs URL with custom base', () => {
    vi.stubEnv('VITE_API_URL', 'http://api.example.com');
    expect(getApiUrl('/users')).toBe('http://api.example.com/users');
  });
});

describe('formatErrorDetail', () => {
  it('returns string detail unchanged', () => {
    expect(formatErrorDetail('Error message')).toBe('Error message');
  });

  it('extracts msg from object with msg field', () => {
    expect(formatErrorDetail({ msg: 'Validation failed' })).toBe('Validation failed');
  });

  it('extracts and joins messages from array of objects', () => {
    const detail = [
      { msg: 'Field A is required' },
      { msg: 'Field B must be positive' },
    ];
    expect(formatErrorDetail(detail)).toBe('Field A is required; Field B must be positive');
  });

  it('filters out items without msg in array', () => {
    const detail = [
      { msg: 'Valid error' },
      'String error',
      { loc: ['body', 'field'] },
    ];
    expect(formatErrorDetail(detail)).toBe('Valid error; String error');
  });

  it('returns undefined for non-object detail without msg', () => {
    expect(formatErrorDetail({ code: 500 })).toBeUndefined();
  });

  it('returns undefined for empty array', () => {
    expect(formatErrorDetail([])).toBeUndefined();
  });

  it('returns undefined for null', () => {
    expect(formatErrorDetail(null)).toBeUndefined();
  });

  it('returns undefined for undefined', () => {
    expect(formatErrorDetail(undefined)).toBeUndefined();
  });
});