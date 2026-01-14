export interface SourceFormData {
  source: string;
  take_profit: string;
  stop_loss: string;
  trailing_stop: string;
  position_size_multiplier: string;
}

export interface PartialExitFormData {
  exit_percent: string;
  threshold: string;
}

export interface StrategyFormData {
  name: string;
  description: string;
  default_take_profit: string;
  default_stop_loss: string;
  default_trailing_stop: string;
  // Dynamic trailing
  dynamic_trailing_enabled: boolean;
  dynamic_trailing_base: string;
  dynamic_trailing_tight: string;
  dynamic_trailing_threshold: string;
  // Time-based trailing
  time_trailing_enabled: boolean;
  time_trailing_start_hours: string;
  time_trailing_max_hours: string;
  time_trailing_tight: string;
  // Statistical filters
  min_source_win_rate: string;
  min_source_profit_factor: string;
  min_source_trades: string;
  lookback_days: string;
  // Sources and partial exits
  sources: SourceFormData[];
  partial_exits: PartialExitFormData[];
}

export const initialSourceData: SourceFormData = {
  source: "",
  take_profit: "",
  stop_loss: "",
  trailing_stop: "",
  position_size_multiplier: "1.0",
};

export const initialPartialExitData: PartialExitFormData = {
  exit_percent: "",
  threshold: "",
};

export const initialFormData: StrategyFormData = {
  name: "",
  description: "",
  default_take_profit: "",
  default_stop_loss: "",
  default_trailing_stop: "",
  dynamic_trailing_enabled: false,
  dynamic_trailing_base: "20",
  dynamic_trailing_tight: "5",
  dynamic_trailing_threshold: "50",
  time_trailing_enabled: false,
  time_trailing_start_hours: "24",
  time_trailing_max_hours: "72",
  time_trailing_tight: "5",
  min_source_win_rate: "",
  min_source_profit_factor: "",
  min_source_trades: "",
  lookback_days: "30",
  sources: [],
  partial_exits: [],
};

export const AVAILABLE_SOURCES = [
  "telegram_channel_1",
  "telegram_channel_2",
  "telegram_channel_3",
  "ifttt_webhook",
  "rss_feed",
  "manual",
];

export const STRATEGY_TEMPLATES: Record<string, Partial<StrategyFormData>> = {
  conservative: {
    name: "Conservative Strategy",
    default_take_profit: "15",
    default_stop_loss: "5",
    default_trailing_stop: "3",
    dynamic_trailing_enabled: false,
    time_trailing_enabled: false,
    partial_exits: [{ exit_percent: "50", threshold: "10" }],
  },
  aggressive: {
    name: "Aggressive Strategy",
    default_take_profit: "30",
    default_stop_loss: "15",
    default_trailing_stop: "5",
    dynamic_trailing_enabled: true,
    dynamic_trailing_base: "20",
    dynamic_trailing_tight: "5",
    dynamic_trailing_threshold: "50",
    partial_exits: [
      { exit_percent: "30", threshold: "15" },
      { exit_percent: "30", threshold: "25" },
    ],
  },
  news: {
    name: "News-Based Strategy",
    default_take_profit: "20",
    default_stop_loss: "10",
    default_trailing_stop: "5",
    time_trailing_enabled: true,
    time_trailing_start_hours: "12",
    time_trailing_max_hours: "48",
    time_trailing_tight: "3",
  },
};
