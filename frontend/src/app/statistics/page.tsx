"use client";

import { useAnalytics } from "@/hooks/use-analytics";
import {
  KpiCards,
  ModeToggle,
  FilterBar,
  EquityCurve,
  DrawdownChart,
  PerformanceHeatmap,
  StrategyTable,
  TradesTable,
} from "@/components/analytics";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Wifi, WifiOff, RefreshCw } from "lucide-react";

export default function AnalyticsPage() {
  const {
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
    refresh,
    loadMoreTrades,
  } = useAnalytics({ initialFilters: { trading_mode: "live" } });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Trading performance metrics and analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={refresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Badge variant={isConnected ? "default" : "secondary"}>
            {isConnected ? (
              <><Wifi className="h-3 w-3 mr-1" /> Live</>
            ) : (
              <><WifiOff className="h-3 w-3 mr-1" /> Offline</>
            )}
          </Badge>
        </div>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Mode Toggle */}
      <ModeToggle
        value={(filters.trading_mode as "live" | "paper" | "all") || "live"}
        onChange={(mode) => setFilters({ ...filters, trading_mode: mode })}
        isConnected={isConnected}
      />

      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        filterOptions={filterOptions}
        onChange={setFilters}
      />

      {/* KPI Cards */}
      {summary?.totals && <KpiCards summary={summary.totals} isLoading={isLoading} />}

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        <EquityCurve data={equityTimeseries} isLoading={isLoading} />
        <div className="space-y-4">
          <DrawdownChart data={drawdownTimeseries} isLoading={isLoading} />
          <PerformanceHeatmap data={heatmap} isLoading={isLoading} />
        </div>
      </div>

      {/* Strategy Comparison */}
      {summary && summary.groups.length > 0 && (
        <StrategyTable data={summary} isLoading={isLoading} />
      )}

      {/* Trades Table */}
      <TradesTable
        data={trades}
        isLoading={isLoading}
        onLoadMore={loadMoreTrades}
      />
    </div>
  );
}
