import client from './client';
import { FrameAssignment } from '../types';

export const startProcessing = async (
  sessionId: string,
  assignments: FrameAssignment[]
): Promise<{ job_id: string }> => {
  const res = await client.post(`/api/session/${sessionId}/process`, { assignments });
  return res.data;
};
