import client from './client';
import type { Frame } from '../types';

export const uploadVideo = async (sessionId: string, file: File): Promise<void> => {
  const form = new FormData();
  form.append('file', file);
  await client.post(`/api/session/${sessionId}/upload`, form);
};

export const extractFrames = async (sessionId: string, fps: number): Promise<{ count: number }> => {
  const res = await client.post(`/api/session/${sessionId}/extract`, { fps });
  return res.data;
};

export const listFrames = async (sessionId: string): Promise<Frame[]> => {
  const res = await client.get(`/api/session/${sessionId}/frames`);
  return res.data;
};

export const deleteFrame = async (sessionId: string, index: number): Promise<void> => {
  await client.delete(`/api/session/${sessionId}/frames/${index}`);
};

export const frameImageUrl = (sessionId: string, filename: string): string =>
  `http://localhost:8000/api/session/${sessionId}/frames/${filename}/image`;
