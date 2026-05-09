import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSession } from './hooks/useSession';
import { useWebSocket } from './hooks/useWebSocket';
import { VideoUpload } from './components/VideoUpload';
import { FrameGallery } from './components/FrameGallery';
import { ChatPanel } from './components/ChatPanel';
import { ModelAssignment } from './components/ModelAssignment';
import { ProgressPanel } from './components/ProgressPanel';
import { ExportPanel } from './components/ExportPanel';
import type { FrameAssignment } from './types';

const queryClient = new QueryClient();

function MainApp() {
  const {
    session, frames, products, segments, loading, error,
    start, upload, extract, removeFrame, addProduct, segment, process, exportVid,
  } = useSession();

  const { messages, connected, clearMessages } = useWebSocket(session?.session_id ?? null);

  const [fps, setFps] = useState(30);
  const [assignments, setAssignments] = useState<FrameAssignment[]>([]);
  const [step, setStep] = useState<'start' | 'upload' | 'frames' | 'products' | 'assign' | 'process' | 'export'>('start');

  const handleAssign = (frame: string, maskPath: string, productTag: string) => {
    setAssignments(prev => {
      const existing = prev.findIndex(a => a.frame === frame);
      const updated = [...prev];
      if (existing >= 0) {
        updated[existing] = { frame, mask_path: maskPath, product_tag: productTag };
      } else {
        updated.push({ frame, mask_path: maskPath, product_tag: productTag });
      }
      return updated;
    });
  };

  const handleBatchAssign = (productTag: string) => {
    setAssignments(
      segments.map(s => ({ frame: s.frame, mask_path: s.mask_path, product_tag: productTag }))
    );
  };

  const handleProcess = async () => {
    clearMessages();
    await process(assignments);
    setStep('export');
  };

  return (
    <div style={{ minHeight: '100vh', background: '#080808', color: '#ddd', fontFamily: 'sans-serif', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '12px 24px', borderBottom: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', gap: 16 }}>
        <span style={{ fontWeight: 700, fontSize: 18, color: '#fff' }}>Video Product Overlay</span>
        {session && <span style={{ color: '#555', fontSize: 12, fontFamily: 'monospace' }}>session: {session.session_id.slice(0, 8)}</span>}
        {error && <span style={{ color: '#ff8888', fontSize: 13 }}>Error: {error}</span>}
        {loading && <span style={{ color: '#888', fontSize: 13 }}>Working…</span>}
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left main area */}
        <div style={{ flex: 1, padding: 24, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Step 1: Start session */}
          {step === 'start' && (
            <div>
              <h2 style={{ color: '#ccc', marginBottom: 16 }}>Start a new session</h2>
              <button
                onClick={async () => { await start(); setStep('upload'); }}
                style={{ background: '#1a3a5c', color: '#7ec8ff', border: 'none', borderRadius: 6, padding: '10px 24px', cursor: 'pointer', fontSize: 15 }}
              >
                New Session
              </button>
            </div>
          )}

          {/* Step 2: Upload video */}
          {step === 'upload' && (
            <div>
              <h2 style={{ color: '#ccc', marginBottom: 12 }}>Upload Video</h2>
              <VideoUpload
                onFile={async (file) => {
                  await upload(file);
                  setStep('frames');
                }}
                disabled={loading}
              />
            </div>
          )}

          {/* Step 3: Extract frames */}
          {step === 'frames' && (
            <div>
              <h2 style={{ color: '#ccc', marginBottom: 12 }}>Extract Frames</h2>
              <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center' }}>
                <label style={{ color: '#aaa', fontSize: 14 }}>FPS:</label>
                {[30, 45, 60].map(f => (
                  <button
                    key={f}
                    onClick={() => setFps(f)}
                    style={{
                      background: fps === f ? '#1a3a5c' : '#1a1a1a',
                      color: fps === f ? '#7ec8ff' : '#888',
                      border: `1px solid ${fps === f ? '#3a6a9c' : '#333'}`,
                      borderRadius: 4, padding: '4px 12px', cursor: 'pointer', fontSize: 13,
                    }}
                  >
                    {f}
                  </button>
                ))}
                <input
                  type="number"
                  min={1} max={60}
                  value={fps}
                  onChange={e => setFps(Number(e.target.value))}
                  style={{ width: 60, background: '#111', color: '#ccc', border: '1px solid #333', borderRadius: 4, padding: '4px 8px', fontSize: 13 }}
                />
              </div>
              <button
                onClick={async () => { await extract(fps); }}
                disabled={loading}
                style={{ background: '#2a2a2a', color: '#ccc', border: 'none', borderRadius: 4, padding: '8px 20px', cursor: 'pointer', fontSize: 14, marginBottom: 16 }}
              >
                Extract Frames
              </button>
              {frames.length > 0 && (
                <>
                  <FrameGallery frames={frames} sessionId={session!.session_id} onDelete={removeFrame} />
                  <button
                    onClick={() => setStep('products')}
                    style={{ marginTop: 16, background: '#1a4a1a', color: '#7fff7f', border: 'none', borderRadius: 4, padding: '8px 20px', cursor: 'pointer', fontSize: 14 }}
                  >
                    Confirm Frames → Add Products
                  </button>
                </>
              )}
            </div>
          )}

          {/* Step 5-6: Segmentation + Assignment */}
          {(step === 'assign' || step === 'process') && (
            <div>
              <h2 style={{ color: '#ccc', marginBottom: 12 }}>Assign Products to Frames</h2>
              <button
                onClick={segment}
                disabled={loading}
                style={{ background: '#2a2a2a', color: '#ccc', border: 'none', borderRadius: 4, padding: '8px 20px', cursor: 'pointer', fontSize: 14, marginBottom: 16 }}
              >
                Run Segmentation
              </button>
              <ModelAssignment
                segments={segments}
                products={products}
                assignments={assignments}
                onAssign={handleAssign}
                onBatchAssign={handleBatchAssign}
              />
              {assignments.length > 0 && (
                <button
                  onClick={handleProcess}
                  disabled={loading}
                  style={{ marginTop: 16, background: '#4a1a1a', color: '#ff8888', border: 'none', borderRadius: 4, padding: '8px 20px', cursor: 'pointer', fontSize: 14 }}
                >
                  Start Inpainting ({assignments.length} frames)
                </button>
              )}
            </div>
          )}

          {/* Step 7: Export */}
          {step === 'export' && (
            <div>
              <h2 style={{ color: '#ccc', marginBottom: 12 }}>Export</h2>
              <ProgressPanel messages={messages} connected={connected} total={assignments.length} />
              <div style={{ marginTop: 16 }}>
                <ExportPanel sessionId={session!.session_id} onExport={exportVid} />
              </div>
            </div>
          )}
        </div>

        {/* Right: Chat panel (always visible after session start) */}
        {session && (step === 'products' || step === 'assign' || step === 'process' || step === 'export') && (
          <div style={{ width: 320, borderLeft: '1px solid #1a1a1a', display: 'flex', flexDirection: 'column' }}>
            <ChatPanel
              sessionId={session.session_id}
              products={products}
              onAddProduct={async (file, tag) => {
                await addProduct(file, tag);
                if (step === 'products' && products.length >= 0) setStep('assign');
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MainApp />
    </QueryClientProvider>
  );
}
