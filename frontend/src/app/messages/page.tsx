"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface TelegramMessage {
  message_id: number;
  chat_title: string;
  text: string;
  timestamp: string;
}

interface TelegramSource {
  id: number;
  name: string;
  config: {
    group_id?: string;
    group_name?: string;
  } | null;
}

export default function Messages() {
  const [messages, setMessages] = useState<TelegramMessage[]>([]);
  const [sources, setSources] = useState<TelegramSource[]>([]);
  const [selectedSource, setSelectedSource] = useState<TelegramSource | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<{ configured: boolean; authenticated: boolean } | null>(null);

  // Load telegram sources and status on mount
  useEffect(() => {
    loadTelegramSources();
    checkTelegramStatus();
  }, []);

  const checkTelegramStatus = async () => {
    try {
      const s = await api.getTelegramStatus();
      setStatus(s);
      return s;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to get status");
      return null;
    }
  };

  const loadTelegramSources = async () => {
    try {
      const allSources = await api.getSources("telegram", true);
      const telegramSources: TelegramSource[] = allSources.map((s) => ({
        id: s.id,
        name: s.name,
        config: s.config as { group_id?: string; group_name?: string } | null,
      }));
      setSources(telegramSources);
      if (telegramSources.length > 0 && !selectedSource) {
        setSelectedSource(telegramSources[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sources");
    }
  };

  const fetchMessages = async () => {
    if (!selectedSource) {
      setError("Please select a source first");
      return;
    }

    const groupId = selectedSource.config?.group_id || selectedSource.name;
    if (!groupId) {
      setError("Source has no group ID configured");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const s = await checkTelegramStatus();
      if (!s?.authenticated) {
        setError("Telegram not authenticated. Please connect in Settings.");
        return;
      }

      const data = await api.getTelegramMessages(groupId, 20);
      setMessages(data.messages);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch messages");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Messages</h1>

      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          {sources.length > 0 ? (
            <>
              <select
                value={selectedSource?.id || ""}
                onChange={(e) => {
                  const source = sources.find((s) => s.id === Number(e.target.value));
                  setSelectedSource(source || null);
                }}
                className="px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              >
                {sources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>

              <button
                onClick={fetchMessages}
                disabled={loading || !selectedSource}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
              >
                {loading ? "Fetching..." : "Fetch Messages"}
              </button>
            </>
          ) : (
            <p className="text-gray-400">
              No Telegram sources configured.{" "}
              <a href="/sources" className="text-blue-400 underline">
                Add a Telegram source
              </a>
            </p>
          )}

          <button
            onClick={checkTelegramStatus}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            Refresh Status
          </button>
        </div>

        {status && (
          <div className="text-sm text-gray-400 mb-4">
            Status: {status.configured ? "Configured" : "Not configured"} |{" "}
            {status.authenticated ? (
              <span className="text-green-400">Authenticated</span>
            ) : (
              <span className="text-yellow-400">Not authenticated</span>
            )}
          </div>
        )}

        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-300 px-4 py-2 rounded-lg mb-4">
            {error}
          </div>
        )}
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">No messages yet</p>
            <p className="text-gray-500 mt-2">
              Select a Telegram source and click &quot;Fetch Messages&quot; to load messages
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.message_id}
                className="bg-gray-700 rounded-lg p-4 border border-gray-600"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-blue-400 font-medium">{msg.chat_title}</span>
                  <span className="text-gray-500 text-sm">
                    {new Date(msg.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-gray-200 whitespace-pre-wrap">{msg.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
