import { useEffect, useRef, useState } from 'react';
import { Canvas, Rect, FabricImage } from 'fabric';
import { Frame, PersonBox } from '../types';

interface Props {
  frame: Frame;
  sessionId: string;
  persons: PersonBox[];
  onMaskUpdate?: (rect: { left: number; top: number; width: number; height: number }) => void;
}

export function CanvasOverlay({ frame, sessionId, persons, onMaskUpdate }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<Canvas | null>(null);
  const [canvasReady, setCanvasReady] = useState(false);

  const imgSrc = `http://localhost:8000/api/session/${sessionId}/frames/${frame.filename}/image`;

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = new Canvas(canvasRef.current, {
      width: 640,
      height: 360,
      selection: true,
    });
    fabricRef.current = canvas;
    setCanvasReady(true);

    // Load frame as background
    canvas.backgroundImage = undefined;
    const imgEl = new Image();
    imgEl.crossOrigin = 'anonymous';
    imgEl.onload = () => {
      const fabricImg = new FabricImage(imgEl, {
        scaleX: 640 / imgEl.naturalWidth,
        scaleY: 360 / imgEl.naturalHeight,
        selectable: false,
        evented: false,
      });
      canvas.backgroundImage = fabricImg;
      canvas.renderAll();

      // Draw person bounding boxes
      persons.forEach(p => {
        const scaleX = 640 / imgEl.naturalWidth;
        const scaleY = 360 / imgEl.naturalHeight;
        const rect = new Rect({
          left: p.xmin * scaleX,
          top: p.ymin * scaleY,
          width: (p.xmax - p.xmin) * scaleX,
          height: (p.ymax - p.ymin) * scaleY,
          stroke: '#00ff88',
          strokeWidth: 2,
          fill: 'rgba(0,255,136,0.08)',
          selectable: false,
          evented: false,
        });
        canvas.add(rect);
      });

      canvas.renderAll();
    };
    imgEl.src = imgSrc;

    // Allow drawing manual selection rect
    canvas.on('mouse:up', () => {
      const active = canvas.getActiveObject();
      if (active && onMaskUpdate) {
        onMaskUpdate({
          left: active.left ?? 0,
          top: active.top ?? 0,
          width: (active.width ?? 0) * (active.scaleX ?? 1),
          height: (active.height ?? 0) * (active.scaleY ?? 1),
        });
      }
    });

    return () => {
      canvas.dispose();
    };
  }, [frame.filename, sessionId]);

  return (
    <div style={{ border: '1px solid #333', borderRadius: 4, overflow: 'hidden', display: 'inline-block' }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
