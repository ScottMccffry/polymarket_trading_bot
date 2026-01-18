"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { useWebSocket } from "./use-websocket";
import type {
  AnalyticsSummaryResponse,
  TimeseriesResponse,
  HeatmapResponse,
  TradesResponse,
  AnalyticsFilters,
  FilterOptions,
} from "@/lib/api";

export interface UseAnalyticsOptions {
  initialFilters?: AnalyticsFilters;
  autoRefresh?: boolean;
}

export interface UseAnalyticsReturn {
  // Data
  summary: AnalyticsSummaryResponse | null;
  equityTimeseries: TimeseriesResponse | null;
  drawdownTimeseries: TimeseriesResponse | null;
  heatmap: HeatmapResponse | null;
  trades: TradesResponse | null;
  filterOptions: FilterOptions | null;

  // State
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;

  // Actions
  filters: AnalyticsFilters;
  setFilters: (filters: AnalyticsFilters) => void;
  refresh: () => Promise<void>;
  loadMoreTrades: () => Promise<void>;
}

export function useAnalytics(options: UseAnalyticsOptions = {}): UseAnalyticsReturn {
  const { initialFilters = { trading_mode: "live" }, autoRefresh = true } = options;

  const [filters, setFiltersState] = useState<AnalyticsFilters>(initialFilters);
  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null);
  const [equityTimeseries, setEquityTimeseries] = useState<TimeseriesResponse | null>(null);
  const [drawdownTimeseries, setDrawdownTimeseries] = useState<TimeseriesResponse | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [trades, setTrades] = useState<TradesResponse | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const tradesOffset = useRef(0);

  const fetchAllData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [summaryData, equityData, drawdownData, heatmapData, tradesData, options] =
        await Promise.all([
          api.getAnalyticsSummaryGrouped(filters, "strategy_name"),
          api.getAnalyticsTimeseries("equity", "daily", filters),
          api.getAnalyticsTimeseries("drawdown", "daily", filters),
          api.getAnalyticsHeatmap("day_of_week", "pnl", filters.trading_mode),
          api.getAnalyticsTrades(filters, "closed_at", "desc", 100, 0),
          api.getAnalyticsFilterOptions(),
        ]);

      setSummary(summaryData);
      setEquityTimeseries(equityData);
      setDrawdownTimeseries(drawdownData);
      setHeatmap(heatmapData);
      setTrades(tradesData);
      setFilterOptions(options);
      tradesOffset.current = 100;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch analytics");
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const loadMoreTrades = useCallback(async () => {
    if (!trades) return;

    try {
      const moreTrades = await api.getAnalyticsTrades(
        filters,
        "closed_at",
        "desc",
        100,
        tradesOffset.current
      );

      setTrades(prev => prev ? {
        ...prev,
        trades: [...prev.trades, ...moreTrades.trades],
      } : moreTrades);

      tradesOffset.current += 100;
    } catch (err) {
      console.error("Failed to load more trades:", err);
    }
  }, [filters, trades]);

  const setFilters = useCallback((newFilters: AnalyticsFilters) => {
    setFiltersState(newFilters);
    tradesOffset.current = 0;
  }, []);

  // WebSocket for real-time updates
  const { isConnected } = useWebSocket({
    enabled: autoRefresh,
    onPositionClosed: () => fetchAllData(),
    onPositionOpened: () => fetchAllData(),
    onPortfolioUpdate: () => {
      // Debounced refresh for position updates - only refresh summary
      api.getAnalyticsSummaryGrouped(filters, "strategy_name")
        .then(setSummary)
        .catch(console.error);
    },
  });

  // Initial fetch
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  return {
    summary,
    equityTimeseries,
    drawdownTimeseries,
    heatmap,
    trades,
    filterOptions,
    isLoading,
    error,
    isConnected,
    filters,
    setFilters,
    refresh: fetchAllData,
    loadMoreTrades,
  };
}
