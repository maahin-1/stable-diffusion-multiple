import { useState, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import type { Product } from '../types';
import { ProductTag } from './ProductTag';

interface ChatMessage {
  id: string;
  text: string;
  products: Product[];
  timestamp: Date;
}

interface Props {
  sessionId: string;
  products: Product[];
  onAddProduct: (file: File, tag: string) => Promise<Product | null>;
}

export function ChatPanel({ sessionId, products, onAddProduct }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pendingTag, setPendingTag] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => {
      if (files[0]) {
        setPendingFile(files[0]);
        const auto = `product-${products.length + 1}`;
        setPendingTag(auto);
      }
    },
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] },
    maxFiles: 1,
    noClick: false,
  });

  const confirmUpload = async () => {
    if (!pendingFile || !pendingTag.trim()) return;
    const tag = pendingTag.trim();
    const file = pendingFile;
    setPendingFile(null);
    setPendingTag('');
    const uploaded = await onAddProduct(file, tag);
    setMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        text: `Uploaded image as @${tag}`,
        products: uploaded ? [uploaded] : [],
        timestamp: new Date(),
      },
    ]);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
  };

  const sendMessage = () => {
    if (!input.trim()) return;
    const mentionedProducts = products.filter(p => input.includes(`@${p.tag}`));
    setMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        text: input,
        products: mentionedProducts,
        timestamp: new Date(),
      },
    ]);
    setInput('');
    setTimeout(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
  };

  return (
    <div
      {...getRootProps()}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#0d0d0d',
        border: '1px solid #333',
        borderRadius: 8,
        position: 'relative',
      }}
    >
      <input {...getInputProps()} />
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #222', color: '#888', fontSize: 13 }}>
        Chat — drag images here to upload products
      </div>

      {/* Message list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.map(m => (
          <div key={m.id}>
            <div style={{ color: '#ccc', fontSize: 13 }}>{m.text}</div>
            {m.products.length > 0 && (
              <div style={{ display: 'flex', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
                {m.products.map(p => (
                  <ProductTag key={p.tag} product={p} sessionId={sessionId} />
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* Pending file upload */}
      {pendingFile && (
        <div style={{ padding: '8px 12px', background: '#1a1a1a', borderTop: '1px solid #222' }}>
          <div style={{ color: '#aaa', fontSize: 12, marginBottom: 4 }}>
            Ready to upload: <strong style={{ color: '#fff' }}>{pendingFile.name}</strong>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              value={pendingTag}
              onChange={e => setPendingTag(e.target.value)}
              placeholder="Tag name"
              style={{ flex: 1, background: '#111', color: '#fff', border: '1px solid #444', borderRadius: 4, padding: '4px 8px', fontSize: 13 }}
            />
            <button
              onClick={confirmUpload}
              style={{ background: '#1e5c1e', color: '#7fff7f', border: 'none', borderRadius: 4, padding: '4px 12px', cursor: 'pointer', fontSize: 13 }}
            >
              Upload
            </button>
            <button
              onClick={() => { setPendingFile(null); setPendingTag(''); }}
              style={{ background: '#3a1a1a', color: '#ff8888', border: 'none', borderRadius: 4, padding: '4px 12px', cursor: 'pointer', fontSize: 13 }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {isDragActive && (
        <div style={{ position: 'absolute', inset: 0, background: 'rgba(30,60,90,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8, pointerEvents: 'none', fontSize: 18, color: '#7ec8ff' }}>
          Drop image to add product
        </div>
      )}

      {/* Input */}
      <div style={{ padding: 8, borderTop: '1px solid #222', display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Type a message or use @tag..."
          style={{ flex: 1, background: '#111', color: '#fff', border: '1px solid #333', borderRadius: 4, padding: '6px 10px', fontSize: 14 }}
        />
        <button
          onClick={sendMessage}
          style={{ background: '#1a3a5c', color: '#7ec8ff', border: 'none', borderRadius: 4, padding: '6px 14px', cursor: 'pointer', fontSize: 14 }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
