import type { Frame } from '../types';

interface Props {
  frame: Frame;
  sessionId: string;
  onDelete: (index: number) => void;
}

export function FrameCard({ frame, sessionId, onDelete }: Props) {
  const src = `http://localhost:8000/api/session/${sessionId}/frames/${frame.filename}/image`;

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <img
        src={src}
        alt={`Frame ${frame.index}`}
        style={{ width: 160, height: 90, objectFit: 'cover', borderRadius: 4, display: 'block' }}
      />
      <div style={{ fontSize: 11, color: '#aaa', textAlign: 'center' }}>#{frame.index}</div>
      <button
        onClick={() => onDelete(frame.index)}
        style={{
          position: 'absolute',
          top: 2,
          right: 2,
          background: 'rgba(200,0,0,0.8)',
          color: '#fff',
          border: 'none',
          borderRadius: 3,
          cursor: 'pointer',
          fontSize: 11,
          padding: '1px 5px',
        }}
      >
        ✕
      </button>
    </div>
  );
}
