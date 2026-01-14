"use client";

import { useEffect, useRef, useState, useCallback } from "react";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

// Event types matching backend
export type EventType =
  | "positions_batch"
  | "position_update"
  | "position_closed"
  | "position_opened"
  | "signal_created"
  | "portfolio_update"
  | "heartbeat"
  | "pong"
  | "error";

export interface WebSocketEvent<T = unknown> {
  type: EventType;
  payload: T;
  timestamp: string;
}

// Payload types
export interface PositionUpdate {
  position_id: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

export interface PositionsBatch {
  positions: PositionUpdate[];
}

export interface PositionClosed {
  position_id: number;
  exit_price: number;
  realized_pnl: number;
  realized_pnl_percent: number;
  reason: string;
}

export interface PositionOpened {
  position_id: number;
  market_question: string | null;
  side: string | null;
  entry_price: number;
  size: number;
  strategy_name: string | null;
}

export interface SignalCreated {
  signal_id: string;
  source: string | null;
  market_question: string | null;
  side: string | null;
  confidence: number | null;
  created_at: string | null;
}

export interface PortfolioUpdate {
  unrealized_pnl: number;
  open_positions_count: number;
  realized_pnl?: number;
  total_value?: number;
}

// Callback types
type EventCallback<T> = (payload: T) => void;

export interface UseWebSocketOptions {
  onPositionUpdate?: EventCallback<PositionUpdate>;
  onPositionsBatch?: EventCallback<PositionsBatch>;
  onPositionClosed?: EventCallback<PositionClosed>;
  onPositionOpened?: EventCallback<PositionOpened>;
  onSignalCreated?: EventCallback<SignalCreated>;
  onPortfolioUpdate?: EventCallback<PortfolioUpdate>;
  onError?: EventCallback<{ message: string }>;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  enabled?: boolean;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  reconnectAttempts: number;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    onPositionUpdate,
    onPositionsBatch,
    onPositionClosed,
    onPositionOpened,
    onSignalCreated,
    onPortfolioUpdate,
    onError,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    enabled = true,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Store callbacks in refs to avoid reconnection on callback changes
  const callbacksRef = useRef(options);
  callbacksRef.current = options;

  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  const disconnect = useCallback(() => {
    clearTimers();
    if (wsRef.current) {
      wsRef.current.close(1000, "Client disconnect");
      wsRef.current = null;
    }
    setIsConnected(false);
    setReconnectAttempts(0);
  }, [clearTimers]);

  const connect = useCallback(() => {
    if (!enabled) return;

    // Don't connect if already connected or connecting
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    // Get token for authentication
    const token =
      typeof window !== "undefined" ? localStorage.getItem("token") : null;

    const url = token ? `${WS_URL}?token=${token}` : WS_URL;

    try {
      console.log("[WebSocket] Connecting to", url);
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        console.log("[WebSocket] Connected");
        setIsConnected(true);
        setReconnectAttempts(0);
        callbacksRef.current.onConnect?.();

        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: "ping" }));
          }
        }, 25000);
      };

      wsRef.current.onclose = (event) => {
        console.log("[WebSocket] Disconnected", event.code, event.reason);
        setIsConnected(false);
        clearTimers();
        callbacksRef.current.onDisconnect?.();

        // Auto reconnect if enabled and not at max attempts
        if (
          autoReconnect &&
          reconnectAttempts < maxReconnectAttempts &&
          event.code !== 1000 // Don't reconnect if intentionally closed
        ) {
          const delay = Math.min(
            reconnectInterval * Math.pow(1.5, reconnectAttempts),
            30000
          );
          console.log(
            `[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1})`
          );
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts((prev) => prev + 1);
            connect();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data: WebSocketEvent = JSON.parse(event.data);

          switch (data.type) {
            case "position_update":
              callbacksRef.current.onPositionUpdate?.(
                data.payload as PositionUpdate
              );
              break;
            case "positions_batch":
              callbacksRef.current.onPositionsBatch?.(
                data.payload as PositionsBatch
              );
              break;
            case "position_closed":
              callbacksRef.current.onPositionClosed?.(
                data.payload as PositionClosed
              );
              break;
            case "position_opened":
              callbacksRef.current.onPositionOpened?.(
                data.payload as PositionOpened
              );
              break;
            case "signal_created":
              callbacksRef.current.onSignalCreated?.(
                data.payload as SignalCreated
              );
              break;
            case "portfolio_update":
              callbacksRef.current.onPortfolioUpdate?.(
                data.payload as PortfolioUpdate
              );
              break;
            case "error":
              callbacksRef.current.onError?.(
                data.payload as { message: string }
              );
              break;
            // Ignore pong and heartbeat
            case "pong":
            case "heartbeat":
              break;
            default:
              console.log("[WebSocket] Unknown event type:", data.type);
          }
        } catch (e) {
          console.error("[WebSocket] Failed to parse message:", e);
        }
      };
    } catch (error) {
      console.error("[WebSocket] Failed to connect:", error);
    }
  }, [
    enabled,
    autoReconnect,
    reconnectInterval,
    maxReconnectAttempts,
    reconnectAttempts,
    clearTimers,
  ]);

  // Connect on mount if enabled, disconnect on unmount
  useEffect(() => {
    if (enabled) {
      connect();
    }
    return () => disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  return {
    isConnected,
    reconnectAttempts,
    connect,
    disconnect,
  };
}
