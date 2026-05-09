import { useState } from 'react';
import { downloadUrl } from '../api/export';

interface Props {
  sessionId: string;
  onExport: (mode: 'preview' | 'hq') => Promise<{ output_path: string } | null>;
}

export function ExportPanel({ sessionId, onExport }: Props) {
  const [exporting, setExporting] = useState(false);
  const [result, setResult] = useState<{ output_path: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handle = async (mode: 'preview' | 'hq') => {
    setExporting(true);
    setError(null);
    try {
      const r = await onExport(mode);
      setResult(r);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setExporting(false);
    }
  };

  const filename = result?.output_path.split('/').pop() ?? '';

  return (
    <div style={{ padding: 12, background: '#0d0d0d', border: '1px solid #333', borderRadius: 8 }}>
      <div style={{ color: '#ccc', fontSize: 14, marginBottom: 12 }}>Export Video</div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          onClick={() => handle('preview')}
          disabled={exporting}
          style={{ background: '#1a3a5c', color: '#7ec8ff', border: 'none', borderRadius: 4, padding: '8px 16px', cursor: 'pointer', fontSize: 13 }}
        >
          Preview (720p)
        </button>
        <button
          onClick={() => handle('hq')}
          disabled={exporting}
          style={{ background: '#1a4a1a', color: '#7fff7f', border: 'none', borderRadius: 4, padding: '8px 16px', cursor: 'pointer', fontSize: 13 }}
        >
          High Quality
        </button>
      </div>
      {exporting && <div style={{ color: '#888', fontSize: 12, marginTop: 8 }}>Exporting…</div>}
      {error && <div style={{ color: '#ff8888', fontSize: 12, marginTop: 8 }}>{error}</div>}
      {result && filename && (
        <div style={{ marginTop: 12 }}>
          <a
            href={downloadUrl(sessionId, filename)}
            download={filename}
            style={{ color: '#7ec8ff', fontSize: 13 }}
          >
            Download {filename}
          </a>
        </div>
      )}
    </div>
  );
}
