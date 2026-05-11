import client from './client';
import type { SegmentResult } from '../types';

export const runSegmentation = async (sessionId: string): Promise<SegmentResult[]> => {
  const res = await client.post(`/api/session/${sessionId}/segment`, {}, { timeout: 300000 });
  return res.data.results ?? res.data;
};
