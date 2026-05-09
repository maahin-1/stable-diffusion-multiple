import client from './client';
import { SegmentResult } from '../types';

export const runSegmentation = async (sessionId: string): Promise<SegmentResult[]> => {
  const res = await client.post(`/api/session/${sessionId}/segment`);
  return res.data;
};
