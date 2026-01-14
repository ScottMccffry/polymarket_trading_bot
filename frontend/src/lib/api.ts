const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
  id: number;
  email: string;
  is_active: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface Signal {
  signal_id: string;
  source: string | null;
  message_text: string | null;
  keywords: string | null;
  market_id: string | null;
  token_id: string | null;
  market_question: string | null;
  side: string | null;
  confidence: number | null;
  price_at_signal: number | null;
  created_at: string | null;
}

export interface CustomStrategy {
  id: number;
  name: string;
  take_profit: number;
  stop_loss: number;
  trailing_stop: number | null;
  partial_exit_percent: number | null;
  partial_exit_threshold: number | null;
  created_at: string | null;
}

export interface CustomStrategyCreate {
  name: string;
  take_profit: number;
  stop_loss: number;
  trailing_stop?: number | null;
  partial_exit_percent?: number | null;
  partial_exit_threshold?: number | null;
}

export interface CustomStrategyUpdate {
  name?: string;
  take_profit?: number;
  stop_loss?: number;
  trailing_stop?: number | null;
  partial_exit_percent?: number | null;
  partial_exit_threshold?: number | null;
}

export interface AdvancedStrategySource {
  id: number;
  strategy_id: number;
  source: string;
  take_profit: number | null;
  stop_loss: number | null;
  trailing_stop: number | null;
  position_size_multiplier: number | null;
}

export interface AdvancedStrategySourceCreate {
  source: string;
  take_profit?: number | null;
  stop_loss?: number | null;
  trailing_stop?: number | null;
  position_size_multiplier?: number;
}

export interface AdvancedStrategyPartialExit {
  id: number;
  strategy_id: number;
  exit_order: number;
  exit_percent: number;
  threshold: number;
}

export interface AdvancedStrategyPartialExitCreate {
  exit_order: number;
  exit_percent: number;
  threshold: number;
}

export interface AdvancedStrategy {
  id: number;
  name: string;
  description: string | null;
  default_take_profit: number;
  default_stop_loss: number;
  default_trailing_stop: number | null;
  dynamic_trailing_enabled: number;
  dynamic_trailing_base: number | null;
  dynamic_trailing_tight: number | null;
  dynamic_trailing_threshold: number | null;
  time_trailing_enabled: number;
  time_trailing_start_hours: number | null;
  time_trailing_max_hours: number | null;
  time_trailing_tight: number | null;
  partial_exit_percent: number | null;
  partial_exit_threshold: number | null;
  min_source_win_rate: number | null;
  min_source_profit_factor: number | null;
  min_source_trades: number | null;
  lookback_days: number | null;
  enabled: number;
  created_at: string | null;
  updated_at: string | null;
  sources?: AdvancedStrategySource[];
  partial_exits?: AdvancedStrategyPartialExit[];
}

export interface AdvancedStrategyCreate {
  name: string;
  description?: string | null;
  default_take_profit: number;
  default_stop_loss: number;
  default_trailing_stop?: number | null;
  dynamic_trailing_enabled?: boolean;
  dynamic_trailing_base?: number;
  dynamic_trailing_tight?: number;
  dynamic_trailing_threshold?: number;
  time_trailing_enabled?: boolean;
  time_trailing_start_hours?: number;
  time_trailing_max_hours?: number;
  time_trailing_tight?: number;
  partial_exit_percent?: number | null;
  partial_exit_threshold?: number | null;
  min_source_win_rate?: number | null;
  min_source_profit_factor?: number | null;
  min_source_trades?: number | null;
  lookback_days?: number;
  enabled?: boolean;
  sources?: AdvancedStrategySourceCreate[];
  partial_exits?: AdvancedStrategyPartialExitCreate[];
}

export interface AdvancedStrategyUpdate {
  name?: string;
  description?: string | null;
  default_take_profit?: number;
  default_stop_loss?: number;
  default_trailing_stop?: number | null;
  dynamic_trailing_enabled?: boolean;
  dynamic_trailing_base?: number;
  dynamic_trailing_tight?: number;
  dynamic_trailing_threshold?: number;
  time_trailing_enabled?: boolean;
  time_trailing_start_hours?: number;
  time_trailing_max_hours?: number;
  time_trailing_tight?: number;
  partial_exit_percent?: number | null;
  partial_exit_threshold?: number | null;
  min_source_win_rate?: number | null;
  min_source_profit_factor?: number | null;
  min_source_trades?: number | null;
  lookback_days?: number;
  enabled?: boolean;
}

export interface StrategiesResponse {
  custom: CustomStrategy[];
  advanced: AdvancedStrategy[];
}

export interface Market {
  condition_id: string;
  question: string;
  description: string | null;
  market_slug: string | null;
  end_date_iso: string | null;
  clob_token_ids: string[];
  liquidity: number;
  volume: number;
  category: string | null;
  active: boolean;
  closed: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface MarketCreate {
  condition_id: string;
  question: string;
  description?: string | null;
  market_slug?: string | null;
  end_date_iso?: string | null;
  clob_token_ids?: string[];
  liquidity?: number;
  volume?: number;
  category?: string | null;
  active?: boolean;
  closed?: boolean;
}

export interface MarketUpdate {
  question?: string;
  description?: string | null;
  market_slug?: string | null;
  end_date_iso?: string | null;
  clob_token_ids?: string[];
  liquidity?: number;
  volume?: number;
  category?: string | null;
  active?: boolean;
  closed?: boolean;
}

export interface Position {
  id: number;
  signal_id: string | null;
  strategy_id: number | null;
  strategy_name: string | null;
  market_id: string | null;
  token_id: string | null;
  market_question: string | null;
  side: string | null;
  entry_price: number | null;
  current_price: number | null;
  exit_price: number | null;
  size: number | null;
  status: string;
  unrealized_pnl: number | null;
  unrealized_pnl_percent: number | null;
  realized_pnl: number | null;
  realized_pnl_percent: number | null;
  source: string | null;
  opened_at: string | null;
  closed_at: string | null;
}

// Settings interfaces
export interface TelegramSettings {
  api_id: number;
  api_hash_masked: string;
  phone: string;
  monitored_groups: string;
}

export interface TelegramSettingsUpdate {
  api_id?: number;
  api_hash?: string;
  phone?: string;
  monitored_groups?: string;
}

export interface LLMSettings {
  openai_api_key_masked: string;
  model: string;
}

export interface LLMSettingsUpdate {
  openai_api_key?: string;
  model?: string;
}

export interface QdrantSettings {
  url: string;
  api_key_masked: string;
  collection_name: string;
}

export interface QdrantSettingsUpdate {
  url?: string;
  api_key?: string;
  collection_name?: string;
}

export interface AllSettings {
  telegram: TelegramSettings;
  llm: LLMSettings;
  qdrant: QdrantSettings;
}

export interface QdrantStatus {
  configured: boolean;
  error?: string;
  collection_name?: string;
  vectors_count?: number;
  points_count?: number;
  status?: string;
}

export interface PriceHistoryPoint {
  t: number;
  p: string;
}

export interface PriceHistoryResponse {
  token_id: string;
  interval: string;
  history: PriceHistoryPoint[];
}

export interface StrategyOverview {
  strategy_id: number | null;
  strategy_name: string;
  total_positions: number;
  open_positions_count: number;
  closed_positions_count: number;
  total_realized_pnl: number;
  total_realized_pnl_percent: number;
  total_unrealized_pnl: number;
  total_unrealized_pnl_percent: number;
  win_rate: number;
  total_invested: number;
}

export interface StrategyPositionsResponse {
  overview: StrategyOverview;
  open_positions: Position[];
  closed_positions: Position[];
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("token");
    }
    return null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "An error occurred");
    }

    return response.json();
  }

  // Auth
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append("username", credentials.email);
    formData.append("password", credentials.password);

    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Login failed");
    }

    const data: AuthResponse = await response.json();
    localStorage.setItem("token", data.access_token);
    return data;
  }

  async getMe(): Promise<User> {
    return this.request<User>("/api/auth/me");
  }

  logout(): void {
    localStorage.removeItem("token");
  }

  // Signals
  async getSignals(limit: number = 50, offset: number = 0): Promise<Signal[]> {
    return this.request<Signal[]>(`/api/signals?limit=${limit}&offset=${offset}`);
  }

  async getRecentSignals(limit: number = 10): Promise<Signal[]> {
    return this.request<Signal[]>(`/api/signals/recent?limit=${limit}`);
  }

  async getSignal(signalId: string): Promise<Signal> {
    return this.request<Signal>(`/api/signals/${signalId}`);
  }

  // Strategies
  async getStrategies(): Promise<StrategiesResponse> {
    return this.request<StrategiesResponse>("/api/strategies");
  }

  async getCustomStrategies(): Promise<CustomStrategy[]> {
    return this.request<CustomStrategy[]>("/api/strategies/custom");
  }

  async createCustomStrategy(strategy: CustomStrategyCreate): Promise<CustomStrategy> {
    return this.request<CustomStrategy>("/api/strategies/custom", {
      method: "POST",
      body: JSON.stringify(strategy),
    });
  }

  async updateCustomStrategy(id: number, strategy: CustomStrategyUpdate): Promise<CustomStrategy> {
    return this.request<CustomStrategy>(`/api/strategies/custom/${id}`, {
      method: "PUT",
      body: JSON.stringify(strategy),
    });
  }

  async deleteCustomStrategy(id: number): Promise<void> {
    await this.request(`/api/strategies/custom/${id}`, {
      method: "DELETE",
    });
  }

  async getAdvancedStrategies(): Promise<AdvancedStrategy[]> {
    return this.request<AdvancedStrategy[]>("/api/strategies/advanced");
  }

  async getAdvancedStrategy(id: number): Promise<AdvancedStrategy> {
    return this.request<AdvancedStrategy>(`/api/strategies/advanced/${id}`);
  }

  async createAdvancedStrategy(strategy: AdvancedStrategyCreate): Promise<AdvancedStrategy> {
    return this.request<AdvancedStrategy>("/api/strategies/advanced", {
      method: "POST",
      body: JSON.stringify(strategy),
    });
  }

  async updateAdvancedStrategy(id: number, strategy: AdvancedStrategyUpdate): Promise<AdvancedStrategy> {
    return this.request<AdvancedStrategy>(`/api/strategies/advanced/${id}`, {
      method: "PUT",
      body: JSON.stringify(strategy),
    });
  }

  async deleteAdvancedStrategy(id: number): Promise<void> {
    await this.request(`/api/strategies/advanced/${id}`, {
      method: "DELETE",
    });
  }

  // Advanced Strategy Sources
  async addStrategySource(strategyId: number, source: AdvancedStrategySourceCreate): Promise<AdvancedStrategySource> {
    return this.request<AdvancedStrategySource>(`/api/strategies/advanced/${strategyId}/sources`, {
      method: "POST",
      body: JSON.stringify(source),
    });
  }

  async deleteStrategySource(strategyId: number, sourceId: number): Promise<void> {
    await this.request(`/api/strategies/advanced/${strategyId}/sources/${sourceId}`, {
      method: "DELETE",
    });
  }

  // Advanced Strategy Partial Exits
  async addStrategyPartialExit(strategyId: number, partialExit: AdvancedStrategyPartialExitCreate): Promise<AdvancedStrategyPartialExit> {
    return this.request<AdvancedStrategyPartialExit>(`/api/strategies/advanced/${strategyId}/partial-exits`, {
      method: "POST",
      body: JSON.stringify(partialExit),
    });
  }

  async deleteStrategyPartialExit(strategyId: number, exitId: number): Promise<void> {
    await this.request(`/api/strategies/advanced/${strategyId}/partial-exits/${exitId}`, {
      method: "DELETE",
    });
  }

  // Positions
  async getPositions(status?: string, strategyId?: number): Promise<Position[]> {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (strategyId) params.append("strategy_id", strategyId.toString());
    const query = params.toString() ? `?${params.toString()}` : "";
    return this.request<Position[]>(`/api/positions${query}`);
  }

  async getOpenPositions(strategyId?: number): Promise<Position[]> {
    const query = strategyId ? `?strategy_id=${strategyId}` : "";
    return this.request<Position[]>(`/api/positions/open${query}`);
  }

  async getClosedPositions(strategyId?: number, limit: number = 50): Promise<Position[]> {
    const params = new URLSearchParams();
    if (strategyId) params.append("strategy_id", strategyId.toString());
    params.append("limit", limit.toString());
    return this.request<Position[]>(`/api/positions/closed?${params.toString()}`);
  }

  async getPositionsByStrategy(strategyId: number): Promise<StrategyPositionsResponse> {
    return this.request<StrategyPositionsResponse>(`/api/positions/strategy/${strategyId}`);
  }

  async getStrategiesOverview(): Promise<StrategyOverview[]> {
    return this.request<StrategyOverview[]>("/api/positions/overview");
  }

  async getPosition(positionId: number): Promise<Position> {
    return this.request<Position>(`/api/positions/${positionId}`);
  }

  // Markets
  async getMarkets(options?: {
    limit?: number;
    offset?: number;
    search?: string;
    category?: string;
    active?: boolean;
    closed?: boolean;
  }): Promise<Market[]> {
    const params = new URLSearchParams();
    if (options?.limit) params.append("limit", options.limit.toString());
    if (options?.offset) params.append("offset", options.offset.toString());
    if (options?.search) params.append("search", options.search);
    if (options?.category) params.append("category", options.category);
    if (options?.active !== undefined) params.append("active", options.active.toString());
    if (options?.closed !== undefined) params.append("closed", options.closed.toString());
    const query = params.toString() ? `?${params.toString()}` : "";
    return this.request<Market[]>(`/api/markets${query}`);
  }

  async getMarketsCount(options?: {
    search?: string;
    category?: string;
    active?: boolean;
    closed?: boolean;
  }): Promise<{ count: number }> {
    const params = new URLSearchParams();
    if (options?.search) params.append("search", options.search);
    if (options?.category) params.append("category", options.category);
    if (options?.active !== undefined) params.append("active", options.active.toString());
    if (options?.closed !== undefined) params.append("closed", options.closed.toString());
    const query = params.toString() ? `?${params.toString()}` : "";
    return this.request<{ count: number }>(`/api/markets/count${query}`);
  }

  async getMarketCategories(): Promise<{ categories: string[] }> {
    return this.request<{ categories: string[] }>("/api/markets/categories");
  }

  async getMarket(conditionId: string): Promise<Market> {
    return this.request<Market>(`/api/markets/${conditionId}`);
  }

  async createMarket(market: MarketCreate): Promise<Market> {
    return this.request<Market>("/api/markets", {
      method: "POST",
      body: JSON.stringify(market),
    });
  }

  async updateMarket(conditionId: string, market: MarketUpdate): Promise<Market> {
    return this.request<Market>(`/api/markets/${conditionId}`, {
      method: "PUT",
      body: JSON.stringify(market),
    });
  }

  async deleteMarket(conditionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/markets/${conditionId}`, {
      method: "DELETE",
    });
  }

  async deleteAllMarkets(): Promise<{ message: string }> {
    return this.request<{ message: string }>("/api/markets?confirm=true", {
      method: "DELETE",
    });
  }

  async getPriceHistory(
    tokenId: string,
    interval: string = "1d",
    fidelity: number = 60
  ): Promise<PriceHistoryResponse> {
    const params = new URLSearchParams();
    params.append("interval", interval);
    params.append("fidelity", fidelity.toString());
    return this.request<PriceHistoryResponse>(
      `/api/markets/price-history/${tokenId}?${params.toString()}`
    );
  }

  // Scheduler
  async harvestMarkets(): Promise<{ status: string; markets_harvested?: number; message?: string }> {
    return this.request<{ status: string; markets_harvested?: number; message?: string }>("/scheduler/harvest", {
      method: "POST",
    });
  }

  async getSchedulerStatus(): Promise<{
    running: boolean;
    jobs: Array<{
      id: string;
      name: string;
      next_run: string | null;
      trigger: string;
    }>;
  }> {
    return this.request("/scheduler/status");
  }

  // Health
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/health");
  }

  // Settings
  async getAllSettings(): Promise<AllSettings> {
    return this.request<AllSettings>("/api/settings");
  }

  async getTelegramSettings(): Promise<TelegramSettings> {
    return this.request<TelegramSettings>("/api/settings/telegram");
  }

  async updateTelegramSettings(settings: TelegramSettingsUpdate): Promise<TelegramSettings> {
    return this.request<TelegramSettings>("/api/settings/telegram", {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  }

  async getLLMSettings(): Promise<LLMSettings> {
    return this.request<LLMSettings>("/api/settings/llm");
  }

  async updateLLMSettings(settings: LLMSettingsUpdate): Promise<LLMSettings> {
    return this.request<LLMSettings>("/api/settings/llm", {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  }

  async getQdrantSettings(): Promise<QdrantSettings> {
    return this.request<QdrantSettings>("/api/settings/qdrant");
  }

  async updateQdrantSettings(settings: QdrantSettingsUpdate): Promise<QdrantSettings> {
    return this.request<QdrantSettings>("/api/settings/qdrant", {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  }

  async getQdrantStatus(): Promise<QdrantStatus> {
    return this.request<QdrantStatus>("/api/markets/qdrant/status");
  }

  async embedMarkets(): Promise<{ message: string; count: number }> {
    return this.request<{ message: string; count: number }>("/api/markets/qdrant/embed", {
      method: "POST",
    });
  }
}

export const api = new ApiClient(API_URL);
