import { useState } from 'react';
import type { Session, Frame, Product, SegmentResult, FrameAssignment } from '../types';
import { createSession, deleteSession } from '../api/sessions';
import { uploadVideo, extractFrames, listFrames, deleteFrame } from '../api/frames';
import { uploadProduct } from '../api/products';
import { runSegmentation } from '../api/segment';
import { startProcessing } from '../api/process';
import { exportVideo } from '../api/export';

export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [frames, setFrames] = useState<Frame[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [segments, setSegments] = useState<SegmentResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await createSession();
      setSession(s);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const upload = async (file: File) => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      await uploadVideo(session.session_id, file);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const extract = async (fps: number) => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      await extractFrames(session.session_id, fps);
      const f = await listFrames(session.session_id);
      setFrames(f);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const removeFrame = async (index: number) => {
    if (!session) return;
    try {
      await deleteFrame(session.session_id, index);
      setFrames(prev => prev.filter(f => f.index !== index));
    } catch (e: any) {
      setError(e.message);
    }
  };

  const addProduct = async (file: File, tag: string): Promise<Product | null> => {
    if (!session) return null;
    try {
      const p = await uploadProduct(session.session_id, file, tag);
      setProducts(prev => [...prev, p]);
      return p;
    } catch (e: any) {
      setError(e.message);
      return null;
    }
  };

  const segment = async () => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const results = await runSegmentation(session.session_id);
      setSegments(Array.isArray(results) ? results : []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const process = async (assignments: FrameAssignment[]) => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      await startProcessing(session.session_id, assignments);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const exportVid = async (mode: 'preview' | 'hq') => {
    if (!session) return null;
    setLoading(true);
    setError(null);
    try {
      const result = await exportVideo(session.session_id, mode);
      return result;
    } catch (e: any) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const cleanup = async () => {
    if (!session) return;
    try {
      await deleteSession(session.session_id);
      setSession(null);
      setFrames([]);
      setProducts([]);
      setSegments([]);
    } catch (e: any) {
      setError(e.message);
    }
  };

  return {
    session, frames, products, segments, loading, error,
    start, upload, extract, removeFrame, addProduct, segment, process, exportVid, cleanup,
  };
}
