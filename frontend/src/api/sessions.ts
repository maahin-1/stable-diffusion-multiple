import client from './client';
import type { Session } from '../types';

export const createSession = async (): Promise<Session> => {
  const res = await client.post('/api/session');
  return res.data;
};

export const deleteSession = async (id: string): Promise<void> => {
  await client.delete(`/api/session/${id}`);
};
