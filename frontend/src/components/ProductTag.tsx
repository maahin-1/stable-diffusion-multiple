import { Product } from '../types';

interface Props {
  product: Product;
  sessionId: string;
}

export function ProductTag({ product, sessionId }: Props) {
  const src = `http://localhost:8000/api/session/${sessionId}/products/${product.filename}/image`;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        background: '#1e3a5f',
        borderRadius: 4,
        padding: '2px 8px',
        fontSize: 13,
        color: '#7ec8ff',
        fontFamily: 'monospace',
      }}
    >
      <img src={src} alt={product.tag} style={{ width: 20, height: 20, objectFit: 'cover', borderRadius: 2 }} />
      @{product.tag}
    </span>
  );
}
