"use client";

import { useEffect, useState } from "react";
import {
  api,
  StrategyOverview,
  Position,
  StrategyPositionsResponse,
  CustomStrategy,
  AdvancedStrategy,
} from "@/lib/api";

type Strategy = (CustomStrategy | AdvancedStrategy) & { type: "custom" | "advanced" };

function formatPnl(value: number | null, showSign: boolean = true): string {
  if (value === null) return "$0.00";
  const sign = showSign && value >= 0 ? "+" : "";
  return `${sign}$${value.toFixed(2)}`;
}

function formatPercent(value: number | null, showSign: boolean = true): string {
  if (value === null) return "0.00%";
  const sign = showSign && value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function PnlBadge({ value, percent }: { value: number | null; percent: number | null }) {
  const isPositive = (value || 0) >= 0;
  return (
    <div className={`text-sm ${isPositive ? "text-green-400" : "text-red-400"}`}>
      <span className="font-medium">{formatPnl(value)}</span>
      <span className="ml-1 text-xs">({formatPercent(percent)})</span>
    </div>
  );
}

function PositionCard({ position, isOpen }: { position: Position; isOpen: boolean }) {
  return (
    <div className="border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <span className="text-white font-medium text-sm line-clamp-1">
          {position.market_question || "Unknown Market"}
        </span>
        <span
          className={`text-xs px-2 py-1 rounded ${
            position.side === "YES"
              ? "bg-green-900/50 text-green-400"
              : position.side === "NO"
              ? "bg-red-900/50 text-red-400"
              : "bg-gray-700 text-gray-400"
          }`}
        >
          {position.side || "N/A"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm mb-3">
        <div>
          <span className="text-gray-400">Entry:</span>
          <span className="text-white ml-1">${position.entry_price?.toFixed(2) || "0.00"}</span>
        </div>
        <div>
          <span className="text-gray-400">{isOpen ? "Current:" : "Exit:"}</span>
          <span className="text-white ml-1">
            ${(isOpen ? position.current_price : position.exit_price)?.toFixed(2) || "0.00"}
          </span>
        </div>
        <div>
          <span className="text-gray-400">Size:</span>
          <span className="text-white ml-1">${position.size?.toFixed(2) || "0.00"}</span>
        </div>
        <div>
          <span className="text-gray-400">Source:</span>
          <span className="text-white ml-1">{position.source || "N/A"}</span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-gray-700">
        <span className="text-gray-400 text-xs">
          {isOpen ? "Unrealized P&L:" : "Realized P&L:"}
        </span>
        <PnlBadge
          value={isOpen ? position.unrealized_pnl : position.realized_pnl}
          percent={isOpen ? position.unrealized_pnl_percent : position.realized_pnl_percent}
        />
      </div>

      <div className="text-xs text-gray-500 mt-2">
        {isOpen
          ? `Opened: ${position.opened_at ? new Date(position.opened_at).toLocaleString() : "N/A"}`
          : `Closed: ${position.closed_at ? new Date(position.closed_at).toLocaleString() : "N/A"}`}
      </div>
    </div>
  );
}

export default function StrategiesOverview() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | null>(null);
  const [strategyData, setStrategyData] = useState<StrategyPositionsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingPositions, setIsLoadingPositions] = useState(false);

  // Fetch all strategies on mount
  useEffect(() => {
    async function fetchStrategies() {
      try {
        const data = await api.getStrategies();
        const allStrategies: Strategy[] = [
          ...data.custom.map((s) => ({ ...s, type: "custom" as const })),
          ...data.advanced.map((s) => ({ ...s, type: "advanced" as const })),
        ];
        setStrategies(allStrategies);

        // Auto-select first strategy if available
        if (allStrategies.length > 0) {
          setSelectedStrategyId(allStrategies[0].id);
        }
      } catch (error) {
        console.error("Failed to fetch strategies:", error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchStrategies();
  }, []);

  // Fetch positions when strategy changes
  useEffect(() => {
    if (selectedStrategyId === null) {
      setStrategyData(null);
      return;
    }

    async function fetchPositions() {
      setIsLoadingPositions(true);
      try {
        const data = await api.getPositionsByStrategy(selectedStrategyId!);
        setStrategyData(data);
      } catch (error) {
        console.error("Failed to fetch positions:", error);
        setStrategyData(null);
      } finally {
        setIsLoadingPositions(false);
      }
    }
    fetchPositions();
  }, [selectedStrategyId]);

  if (isLoading) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold text-white mb-6">Strategies Overview</h1>
        <div className="text-gray-400 text-center py-12">Loading strategies...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Strategies Overview</h1>

      {/* Strategy Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-300 mb-2">Select Strategy</label>
        <select
          value={selectedStrategyId ?? ""}
          onChange={(e) => setSelectedStrategyId(e.target.value ? Number(e.target.value) : null)}
          className="w-full max-w-md bg-gray-800 border border-gray-700 rounded-md px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select a strategy...</option>
          {strategies.map((strategy) => (
            <option key={`${strategy.type}-${strategy.id}`} value={strategy.id}>
              {strategy.name} ({strategy.type})
            </option>
          ))}
        </select>
      </div>

      {selectedStrategyId === null ? (
        <div className="text-gray-400 text-center py-12">
          Select a strategy to view positions and performance
        </div>
      ) : isLoadingPositions ? (
        <div className="text-gray-400 text-center py-12">Loading positions...</div>
      ) : strategyData ? (
        <>
          {/* Overview Cards */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">Performance Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Realized P&L</h3>
                <div
                  className={`text-2xl font-bold ${
                    strategyData.overview.total_realized_pnl >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  }`}
                >
                  {formatPnl(strategyData.overview.total_realized_pnl)}
                </div>
                <div
                  className={`text-sm ${
                    strategyData.overview.total_realized_pnl_percent >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  }`}
                >
                  {formatPercent(strategyData.overview.total_realized_pnl_percent)}
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Unrealized P&L</h3>
                <div
                  className={`text-2xl font-bold ${
                    strategyData.overview.total_unrealized_pnl >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  }`}
                >
                  {formatPnl(strategyData.overview.total_unrealized_pnl)}
                </div>
                <div
                  className={`text-sm ${
                    strategyData.overview.total_unrealized_pnl_percent >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  }`}
                >
                  {formatPercent(strategyData.overview.total_unrealized_pnl_percent)}
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Win Rate</h3>
                <div className="text-2xl font-bold text-white">
                  {strategyData.overview.win_rate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-400">
                  {strategyData.overview.closed_positions_count} closed trades
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Total Invested</h3>
                <div className="text-2xl font-bold text-white">
                  ${strategyData.overview.total_invested.toFixed(2)}
                </div>
                <div className="text-sm text-gray-400">
                  {strategyData.overview.total_positions} total positions
                </div>
              </div>
            </div>
          </section>

          {/* Positions Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Open Positions */}
            <section>
              <h2 className="text-xl font-semibold text-white mb-4">
                Open Positions ({strategyData.overview.open_positions_count})
              </h2>
              <div className="bg-gray-800 rounded-lg p-4 max-h-[600px] overflow-y-auto">
                {strategyData.open_positions.length === 0 ? (
                  <div className="text-gray-400 text-center py-8">No open positions</div>
                ) : (
                  <div className="space-y-3">
                    {strategyData.open_positions.map((position) => (
                      <PositionCard key={position.id} position={position} isOpen={true} />
                    ))}
                  </div>
                )}
              </div>
            </section>

            {/* Closed Positions */}
            <section>
              <h2 className="text-xl font-semibold text-white mb-4">
                Closed Positions ({strategyData.overview.closed_positions_count})
              </h2>
              <div className="bg-gray-800 rounded-lg p-4 max-h-[600px] overflow-y-auto">
                {strategyData.closed_positions.length === 0 ? (
                  <div className="text-gray-400 text-center py-8">No closed positions</div>
                ) : (
                  <div className="space-y-3">
                    {strategyData.closed_positions.map((position) => (
                      <PositionCard key={position.id} position={position} isOpen={false} />
                    ))}
                  </div>
                )}
              </div>
            </section>
          </div>
        </>
      ) : (
        <div className="text-gray-400 text-center py-12">
          No data available for this strategy
        </div>
      )}
    </div>
  );
}
