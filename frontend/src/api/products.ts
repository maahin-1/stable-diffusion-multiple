import client from './client';
import type { Product } from '../types';

export const uploadProduct = async (sessionId: string, file: File, tag: string): Promise<Product> => {
  const form = new FormData();
  form.append('file', file);
  form.append('tag', tag);
  const res = await client.post(`/api/session/${sessionId}/products`, form);
  return res.data;
};

export const listProducts = async (sessionId: string): Promise<Product[]> => {
  const res = await client.get(`/api/session/${sessionId}/products`);
  return res.data;
};
