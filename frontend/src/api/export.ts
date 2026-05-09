import client from './client';

export const exportVideo = async (
  sessionId: string,
  mode: 'preview' | 'hq'
): Promise<{ output_path: string }> => {
  const res = await client.post(`/api/session/${sessionId}/export`, { mode });
  return res.data;
};

export const downloadUrl = (sessionId: string, filename: string): string =>
  `http://localhost:8000/api/session/${sessionId}/export/${filename}`;
