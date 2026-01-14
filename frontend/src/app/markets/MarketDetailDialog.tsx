"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { api, Market, PriceHistoryPoint } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface MarketDetailDialogProps {
  market: Market | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const INTERVAL_OPTIONS = [
  { value: "1h", label: "1 Hour" },
  { value: "6h", label: "6 Hours" },
  { value: "1d", label: "1 Day" },
  { value: "1w", label: "1 Week" },
  { value: "max", label: "All Time" },
];

export function MarketDetailDialog({
  market,
  open,
  onOpenChange,
}: MarketDetailDialogProps) {
  const [priceHistory, setPriceHistory] = useState<PriceHistoryPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interval, setInterval] = useState("1d");
  const [selectedTokenIndex, setSelectedTokenIndex] = useState(0);

  useEffect(() => {
    if (open && market && market.clob_token_ids.length > 0) {
      fetchPriceHistory();
    }
  }, [open, market, interval, selectedTokenIndex]);

  const fetchPriceHistory = async () => {
    if (!market || market.clob_token_ids.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const tokenId = market.clob_token_ids[selectedTokenIndex];
      const data = await api.getPriceHistory(tokenId, interval);
      setPriceHistory(data.history);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch price history"
      );
      setPriceHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const formatChartData = (history: PriceHistoryPoint[]) => {
    return history.map((point) => ({
      timestamp: point.t * 1000,
      price: parseFloat(point.p) * 100,
    }));
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    if (interval === "1h" || interval === "6h") {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  const formatTooltipDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  const chartData = formatChartData(priceHistory);
  const currentPrice =
    chartData.length > 0 ? chartData[chartData.length - 1].price : null;
  const startPrice = chartData.length > 0 ? chartData[0].price : null;
  const priceChange =
    currentPrice !== null && startPrice !== null
      ? currentPrice - startPrice
      : null;
  const priceChangePercent =
    priceChange !== null && startPrice !== null && startPrice !== 0
      ? (priceChange / startPrice) * 100
      : null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="pr-8 leading-normal">
            {market?.question}
          </DialogTitle>
          <DialogDescription>
            {market?.category && (
              <span className="text-muted-foreground">{market.category}</span>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex items-center gap-4">
              {currentPrice !== null && (
                <div>
                  <span className="text-2xl font-bold">
                    {currentPrice.toFixed(1)}¢
                  </span>
                  {priceChange !== null && (
                    <span
                      className={`ml-2 text-sm ${
                        priceChange >= 0 ? "text-green-500" : "text-red-500"
                      }`}
                    >
                      {priceChange >= 0 ? "+" : ""}
                      {priceChange.toFixed(1)}¢
                      {priceChangePercent !== null && (
                        <span className="ml-1">
                          ({priceChangePercent >= 0 ? "+" : ""}
                          {priceChangePercent.toFixed(1)}%)
                        </span>
                      )}
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              {market && market.clob_token_ids.length > 1 && (
                <Select
                  value={selectedTokenIndex.toString()}
                  onValueChange={(value) =>
                    setSelectedTokenIndex(parseInt(value))
                  }
                >
                  <SelectTrigger className="w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">Yes</SelectItem>
                    <SelectItem value="1">No</SelectItem>
                  </SelectContent>
                </Select>
              )}

              <Select value={interval} onValueChange={setInterval}>
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {INTERVAL_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="h-64 w-full">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <Skeleton className="h-full w-full" />
              </div>
            ) : chartData.length === 0 ? (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                No price history available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 5, left: 0, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={formatDate}
                    stroke="#888"
                    fontSize={12}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}¢`}
                    stroke="#888"
                    fontSize={12}
                    tickLine={false}
                    width={50}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-background border rounded-lg shadow-lg p-3">
                            <p className="text-sm text-muted-foreground">
                              {formatTooltipDate(data.timestamp)}
                            </p>
                            <p className="text-lg font-semibold">
                              {data.price.toFixed(2)}¢
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke={
                      priceChange !== null && priceChange >= 0
                        ? "#22c55e"
                        : "#ef4444"
                    }
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Volume</span>
              <p className="font-medium">
                {market?.volume
                  ? `$${(market.volume / 1000000).toFixed(2)}M`
                  : "-"}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">Liquidity</span>
              <p className="font-medium">
                {market?.liquidity
                  ? `$${(market.liquidity / 1000).toFixed(0)}K`
                  : "-"}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">End Date</span>
              <p className="font-medium">
                {market?.end_date_iso
                  ? new Date(market.end_date_iso).toLocaleDateString()
                  : "-"}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">Status</span>
              <p className="font-medium">
                {market?.active ? "Active" : "Inactive"}
              </p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
