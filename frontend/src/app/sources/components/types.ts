export type SourceType = "telegram" | "ifttt" | "rss" | "manual";

export interface Source {
  id: number;
  name: string;
  type: SourceType;
  enabled: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  // Stats
  signals_count?: number;
  win_rate?: number;
  last_signal_at?: string;
}

export interface TelegramSourceConfig {
  group_id: string;
  group_name: string;
  keywords?: string[];
}

export interface IFTTTSourceConfig {
  webhook_key: string;
  event_name: string;
}

export interface RSSSourceConfig {
  feed_url: string;
  poll_interval_minutes: number;
  keywords?: string[];
}

export interface SourceFormData {
  name: string;
  type: SourceType;
  enabled: boolean;
  config: Record<string, unknown>;
}

export const SOURCE_TYPE_INFO: Record<
  SourceType,
  { label: string; description: string; icon: string; color: string }
> = {
  telegram: {
    label: "Telegram",
    description: "Monitor Telegram groups/channels for trading signals",
    icon: "📱",
    color: "blue",
  },
  ifttt: {
    label: "IFTTT",
    description: "Receive signals via IFTTT webhooks",
    icon: "🔗",
    color: "orange",
  },
  rss: {
    label: "RSS Feed",
    description: "Monitor RSS feeds for news and signals",
    icon: "📰",
    color: "green",
  },
  manual: {
    label: "Manual",
    description: "Manually entered trading signals",
    icon: "✍️",
    color: "purple",
  },
};
