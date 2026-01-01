import { useState, useEffect, useRef } from 'react';

export interface LogStats {
  total_logs: number;
  success_logs: number;
  error_logs: number;
  success_rate: number;
  last_updated?: string;
}

export interface LiveUpdate {
  type: 'new_log' | 'stats_update' | 'initial_stats';
  data?: any;
  stats?: LogStats;
  timestamp?: string;
}

export const useWebSocket = (url: string) => {
  const [stats, setStats] = useState<LogStats>({
    total_logs: 0,
    success_logs: 0,
    error_logs: 0,
    success_rate: 0
  });
  const [connected, setConnected] = useState(false);
  const [lastLog, setLastLog] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>();

  const connect = () => {
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setConnected(true);
        console.log('WebSocket Connected');
        
        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);

        ws.onclose = () => {
          clearInterval(pingInterval);
        };
      };

      ws.onmessage = (event) => {
        try {
          const message: LiveUpdate = JSON.parse(event.data);
          
          if (message.stats) {
            setStats(message.stats);
          }
          
          if (message.type === 'new_log' && message.data) {
            setLastLog(message.data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
        setConnected(false);
      };

      ws.onclose = () => {
        setConnected(false);
        console.log('WebSocket Disconnected - Attempting reconnect in 5s');
        
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setConnected(false);
    }
  };

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url]);

  return { stats, connected, lastLog };
};