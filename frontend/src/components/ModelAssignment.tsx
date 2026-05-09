import { SegmentResult, Product, FrameAssignment } from '../types';

interface Props {
  segments: SegmentResult[];
  products: Product[];
  assignments: FrameAssignment[];
  onAssign: (frame: string, maskPath: string, productTag: string) => void;
  onBatchAssign: (productTag: string) => void;
}

export function ModelAssignment({ segments, products, assignments, onAssign, onBatchAssign }: Props) {
  if (segments.length === 0) {
    return <p style={{ color: '#888' }}>Run segmentation first to see detected regions.</p>;
  }

  const getAssigned = (frame: string) =>
    assignments.find(a => a.frame === frame)?.product_tag ?? '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {/* Batch apply */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #222' }}>
        <span style={{ color: '#888', fontSize: 13 }}>Apply to all:</span>
        <select
          defaultValue=""
          onChange={e => { if (e.target.value) onBatchAssign(e.target.value); }}
          style={{ background: '#1a1a1a', color: '#ccc', border: '1px solid #444', borderRadius: 4, padding: '4px 8px', fontSize: 13 }}
        >
          <option value="">— pick product —</option>
          {products.map(p => (
            <option key={p.tag} value={p.tag}>@{p.tag}</option>
          ))}
        </select>
      </div>

      {/* Per-frame assignment */}
      {segments.map(seg => (
        <div
          key={seg.frame}
          style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 0', borderBottom: '1px solid #111' }}
        >
          <span style={{ color: '#aaa', fontSize: 12, fontFamily: 'monospace', minWidth: 80 }}>
            {seg.frame}
          </span>
          <span style={{ color: '#555', fontSize: 12 }}>
            {seg.persons.length} person{seg.persons.length !== 1 ? 's' : ''}
          </span>
          <select
            value={getAssigned(seg.frame)}
            onChange={e => onAssign(seg.frame, seg.mask_path, e.target.value)}
            style={{ background: '#1a1a1a', color: '#ccc', border: '1px solid #444', borderRadius: 4, padding: '4px 8px', fontSize: 13 }}
          >
            <option value="">— pick product —</option>
            {products.map(p => (
              <option key={p.tag} value={p.tag}>@{p.tag}</option>
            ))}
          </select>
          {getAssigned(seg.frame) && (
            <span style={{ color: '#7ec8ff', fontSize: 12, fontFamily: 'monospace' }}>
              @{getAssigned(seg.frame)} ✓
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
