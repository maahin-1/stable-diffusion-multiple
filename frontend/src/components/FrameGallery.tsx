import { Frame } from '../types';
import { FrameCard } from './FrameCard';

interface Props {
  frames: Frame[];
  sessionId: string;
  onDelete: (index: number) => void;
}

export function FrameGallery({ frames, sessionId, onDelete }: Props) {
  if (frames.length === 0) {
    return <p style={{ color: '#888' }}>No frames extracted yet.</p>;
  }

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 8,
        maxHeight: 400,
        overflowY: 'auto',
        padding: 8,
      }}
    >
      {frames.map(f => (
        <FrameCard key={f.index} frame={f} sessionId={sessionId} onDelete={onDelete} />
      ))}
    </div>
  );
}
