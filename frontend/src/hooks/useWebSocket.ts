import { useEffect, useRef, useState } from 'react';
import { ProgressMessage } from '../types';

export function useWebSocket(sessionId: string | null) {
  const [messages, setMessages] = useState<ProgressMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/session/${sessionId}/progress`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg: ProgressMessage = JSON.parse(event.data);
        setMessages(prev => [...prev, msg]);
      } catch {
        // ignore malformed messages
      }
    };

    return () => {
      ws.close();
    };
  }, [sessionId]);

  const clearMessages = () => setMessages([]);

  return { messages, connected, clearMessages };
}
