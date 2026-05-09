import type { ProgressMessage } from '../types';

interface Props {
  messages: ProgressMessage[];
  connected: boolean;
  total: number;
}

export function ProgressPanel({ messages, connected, total }: Props) {
  const done = messages.filter(m => m.status === 'done').length;
  const failed = messages.filter(m => m.status === 'failed').length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div style={{ padding: 12, background: '#0d0d0d', border: '1px solid #333', borderRadius: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ color: '#ccc', fontSize: 14 }}>
          Processing — {done}/{total} frames
        </span>
        <span style={{ color: connected ? '#7fff7f' : '#ff8888', fontSize: 12 }}>
          {connected ? 'connected' : 'disconnected'}
        </span>
      </div>
      <div style={{ background: '#222', borderRadius: 4, height: 8, marginBottom: 8 }}>
        <div
          style={{
            background: failed > 0 ? '#c04040' : '#3a9a3a',
            width: `${pct}%`,
            height: '100%',
            borderRadius: 4,
            transition: 'width 0.3s',
          }}
        />
      </div>
      <div style={{ maxHeight: 200, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {messages.slice(-30).map((m, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, fontSize: 12 }}>
            <span style={{ color: m.status === 'done' ? '#7fff7f' : m.status === 'failed' ? '#ff8888' : '#888' }}>
              {m.status === 'done' ? '✓' : m.status === 'failed' ? '✗' : '…'}
            </span>
            <span style={{ color: '#aaa', fontFamily: 'monospace' }}>{m.frame}</span>
            {m.error && <span style={{ color: '#ff6666' }}>{m.error}</span>}
          </div>
        ))}
      </div>
      {failed > 0 && (
        <div style={{ color: '#ff8888', fontSize: 12, marginTop: 8 }}>
          {failed} frame{failed !== 1 ? 's' : ''} failed — re-trigger individually from the frame gallery.
        </div>
      )}
    </div>
  );
}
