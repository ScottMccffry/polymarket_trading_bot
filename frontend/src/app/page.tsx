"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { Line, LineChart, ResponsiveContainer, Area, AreaChart } from "recharts";
import {
  api,
  Signal,
  CustomStrategy,
  AdvancedStrategy,
  Position,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Activity,
  DollarSign,
  BarChart3,
  Clock,
  Zap,
  Wifi,
  WifiOff,
} from "lucide-react";
import {
  useWebSocket,
  PositionsBatch,
  PositionClosed,
  SignalCreated,
} from "@/hooks/use-websocket";

// Generate sparkline data
function generateSparklineData(trend: "up" | "down" | "neutral", points = 12) {
  const data = [];
  let value = 100;
  for (let i = 0; i < points; i++) {
    const change =
      trend === "up"
        ? Math.random() * 8 - 2
        : trend === "down"
        ? Math.random() * 8 - 6
        : Math.random() * 6 - 3;
    value = Math.max(50, Math.min(150, value + change));
    data.push({ value });
  }
  return data;
}

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  icon: React.ReactNode;
  sparklineData?: { value: number }[];
  valueColor?: string;
}

function KPICard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  sparklineData,
  valueColor,
}: KPICardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between">
          <div>
            <p className={`text-2xl font-bold ${valueColor || ""}`}>{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
            )}
            {trend && trendValue && (
              <div className="flex items-center gap-1 mt-1">
                {trend === "up" ? (
                  <TrendingUp className="h-3 w-3 text-green-500" />
                ) : trend === "down" ? (
                  <TrendingDown className="h-3 w-3 text-red-500" />
                ) : null}
                <span
                  className={`text-xs ${
                    trend === "up"
                      ? "text-green-500"
                      : trend === "down"
                      ? "text-red-500"
                      : "text-muted-foreground"
                  }`}
                >
                  {trendValue}
                </span>
              </div>
            )}
          </div>
          {sparklineData && (
            <div className="h-[40px] w-[80px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sparklineData}>
                  <defs>
                    <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor={trend === "up" ? "#22c55e" : trend === "down" ? "#ef4444" : "#6b7280"}
                        stopOpacity={0.3}
                      />
                      <stop
                        offset="95%"
                        stopColor={trend === "up" ? "#22c55e" : trend === "down" ? "#ef4444" : "#6b7280"}
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke={trend === "up" ? "#22c55e" : trend === "down" ? "#ef4444" : "#6b7280"}
                    strokeWidth={1.5}
                    fill={`url(#gradient-${title})`}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [customStrategies, setCustomStrategies] = useState<CustomStrategy[]>([]);
  const [advancedStrategies, setAdvancedStrategies] = useState<AdvancedStrategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // WebSocket event handlers
  const handlePositionsBatch = useCallback((data: PositionsBatch) => {
    setPositions((prev) => {
      const updates = new Map(data.positions.map((p) => [p.position_id, p]));
      return prev.map((p) => {
        const update = updates.get(p.id);
        return update
          ? {
              ...p,
              current_price: update.current_price,
              unrealized_pnl: update.unrealized_pnl,
              unrealized_pnl_percent: update.unrealized_pnl_percent,
            }
          : p;
      });
    });
  }, []);

  const handlePositionClosed = useCallback((data: PositionClosed) => {
    setPositions((prev) =>
      prev.map((p) =>
        p.id === data.position_id
          ? {
              ...p,
              status: "closed",
              exit_price: data.exit_price,
              realized_pnl: data.realized_pnl,
              realized_pnl_percent: data.realized_pnl_percent,
              unrealized_pnl: 0,
              unrealized_pnl_percent: 0,
            }
          : p
      )
    );

    // Show toast notification
    const pnlSign = data.realized_pnl >= 0 ? "+" : "";
    toast.success(`Position closed: ${data.reason}`, {
      description: `P&L: ${pnlSign}$${data.realized_pnl.toFixed(2)} (${pnlSign}${data.realized_pnl_percent.toFixed(1)}%)`,
    });
  }, []);

  const handleSignalCreated = useCallback((data: SignalCreated) => {
    const newSignal: Signal = {
      signal_id: data.signal_id,
      source: data.source,
      message_text: null,
      keywords: null,
      market_id: null,
      token_id: null,
      market_question: data.market_question,
      side: data.side,
      confidence: data.confidence,
      price_at_signal: null,
      created_at: data.created_at,
    };

    setSignals((prev) => [newSignal, ...prev.slice(0, 9)]); // Keep last 10

    // Show toast notification
    toast.info("New signal detected!", {
      description: data.market_question?.slice(0, 60) || "Unknown market",
    });
  }, []);

  // Initialize WebSocket connection
  const { isConnected } = useWebSocket({
    onPositionsBatch: handlePositionsBatch,
    onPositionClosed: handlePositionClosed,
    onSignalCreated: handleSignalCreated,
  });

  useEffect(() => {
    async function fetchData() {
      try {
        const [signalsData, strategiesData, positionsData] = await Promise.all([
          api.getRecentSignals(10),
          api.getStrategies(),
          api.getPositions(),
        ]);
        setSignals(signalsData);
        setCustomStrategies(strategiesData.custom);
        setAdvancedStrategies(strategiesData.advanced);
        setPositions(positionsData);
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, []);

  // Calculate portfolio stats
  const portfolioStats = useMemo(() => {
    const openPositions = positions.filter((p) => p.status === "open");
    const closedPositions = positions.filter((p) => p.status === "closed");

    const portfolioValue = openPositions.reduce(
      (sum, p) => sum + (p.size || 0),
      0
    );
    const unrealizedPnl = openPositions.reduce(
      (sum, p) => sum + (p.unrealized_pnl || 0),
      0
    );
    const realizedPnl = closedPositions.reduce(
      (sum, p) => sum + (p.realized_pnl || 0),
      0
    );
    const totalPnl = unrealizedPnl + realizedPnl;

    // Calculate win rate
    const wins = closedPositions.filter((p) => (p.realized_pnl || 0) > 0).length;
    const winRate = closedPositions.length > 0
      ? (wins / closedPositions.length) * 100
      : 0;

    return {
      portfolioValue,
      unrealizedPnl,
      realizedPnl,
      totalPnl,
      openCount: openPositions.length,
      closedCount: closedPositions.length,
      winRate,
    };
  }, [positions]);

  // Generate sparkline data
  const sparklines = useMemo(
    () => ({
      portfolio: generateSparklineData("up"),
      pnl: generateSparklineData(portfolioStats.totalPnl >= 0 ? "up" : "down"),
      trades: generateSparklineData("neutral"),
      winRate: generateSparklineData(portfolioStats.winRate >= 50 ? "up" : "down"),
    }),
    [portfolioStats.totalPnl, portfolioStats.winRate]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your trading activity</p>
        </div>
        {/* WebSocket Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted">
          {isConnected ? (
            <>
              <Wifi className="h-4 w-4 text-green-500" />
              <span className="text-xs font-medium text-green-500">Live</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">Offline</span>
            </>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Portfolio Value"
          value={`$${portfolioStats.portfolioValue.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}`}
          subtitle={`${portfolioStats.openCount} open positions`}
          trend="up"
          trendValue="+12.5% this week"
          icon={<Wallet className="h-4 w-4" />}
          sparklineData={sparklines.portfolio}
        />
        <KPICard
          title="Total P&L"
          value={`${portfolioStats.totalPnl >= 0 ? "+" : ""}$${portfolioStats.totalPnl.toLocaleString(
            undefined,
            { minimumFractionDigits: 2, maximumFractionDigits: 2 }
          )}`}
          subtitle={`Unrealized: $${portfolioStats.unrealizedPnl.toFixed(2)}`}
          trend={portfolioStats.totalPnl >= 0 ? "up" : "down"}
          trendValue={portfolioStats.totalPnl >= 0 ? "+8.3% today" : "-2.1% today"}
          icon={<DollarSign className="h-4 w-4" />}
          sparklineData={sparklines.pnl}
          valueColor={portfolioStats.totalPnl >= 0 ? "text-green-500" : "text-red-500"}
        />
        <KPICard
          title="Total Trades"
          value={portfolioStats.closedCount + portfolioStats.openCount}
          subtitle={`${portfolioStats.closedCount} closed`}
          trend="neutral"
          trendValue="+5 this week"
          icon={<Activity className="h-4 w-4" />}
          sparklineData={sparklines.trades}
        />
        <KPICard
          title="Win Rate"
          value={`${portfolioStats.winRate.toFixed(1)}%`}
          subtitle={`${positions.filter((p) => p.status === "closed" && (p.realized_pnl || 0) > 0).length} wins / ${portfolioStats.closedCount} trades`}
          trend={portfolioStats.winRate >= 50 ? "up" : "down"}
          trendValue={portfolioStats.winRate >= 50 ? "Above average" : "Below target"}
          icon={<BarChart3 className="h-4 w-4" />}
          sparklineData={sparklines.winRate}
          valueColor={portfolioStats.winRate >= 50 ? "text-green-500" : "text-yellow-500"}
        />
      </div>

      {/* Main Content */}
      <div className="grid gap-4 lg:grid-cols-7">
        {/* Open Positions */}
        <Card className="lg:col-span-4">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Open Positions</CardTitle>
                <CardDescription>Currently active trades</CardDescription>
              </div>
              <Badge variant="outline">{portfolioStats.openCount} active</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : positions.filter((p) => p.status === "open").length === 0 ? (
              <div className="text-center py-8">
                <Activity className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
                <p className="text-muted-foreground">No open positions</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Positions will appear here when trades are executed
                </p>
              </div>
            ) : (
              <ScrollArea className="h-[300px]">
                <div className="space-y-3">
                  {positions
                    .filter((p) => p.status === "open")
                    .slice(0, 10)
                    .map((position) => (
                      <div
                        key={position.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge
                              variant={position.side === "YES" ? "default" : "destructive"}
                              className="text-xs"
                            >
                              {position.side}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {position.source}
                            </span>
                          </div>
                          <p className="text-sm font-medium truncate">
                            {position.market_question}
                          </p>
                          <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                            <span>Entry: ${position.entry_price?.toFixed(2)}</span>
                            <span>Size: ${position.size?.toFixed(2)}</span>
                          </div>
                        </div>
                        <div className="text-right ml-4">
                          <p
                            className={`text-sm font-semibold ${
                              (position.unrealized_pnl || 0) >= 0
                                ? "text-green-500"
                                : "text-red-500"
                            }`}
                          >
                            {(position.unrealized_pnl || 0) >= 0 ? "+" : ""}$
                            {position.unrealized_pnl?.toFixed(2)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {(position.unrealized_pnl_percent || 0) >= 0 ? "+" : ""}
                            {position.unrealized_pnl_percent?.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Recent Signals */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Signals</CardTitle>
                <CardDescription>Latest detected opportunities</CardDescription>
              </div>
              <Zap className="h-4 w-4 text-yellow-500" />
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-20" />
                ))}
              </div>
            ) : signals.length === 0 ? (
              <div className="text-center py-8">
                <Zap className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
                <p className="text-muted-foreground">No signals yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Signals will appear when detected
                </p>
              </div>
            ) : (
              <ScrollArea className="h-[300px]">
                <div className="space-y-3">
                  {signals.slice(0, 8).map((signal) => (
                    <div
                      key={signal.signal_id}
                      className="p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-muted-foreground">
                          {signal.source || "Unknown"}
                        </span>
                        <Badge
                          variant={
                            signal.side === "YES"
                              ? "default"
                              : signal.side === "NO"
                              ? "destructive"
                              : "secondary"
                          }
                        >
                          {signal.side || "N/A"}
                        </Badge>
                      </div>
                      <p className="text-sm line-clamp-2 mb-2">
                        {signal.market_question || signal.message_text || "No description"}
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1">
                          <Progress
                            value={(signal.confidence || 0) * 100}
                            className="h-1.5 w-16"
                          />
                          <span className="text-xs text-muted-foreground">
                            {signal.confidence
                              ? `${(signal.confidence * 100).toFixed(0)}%`
                              : "N/A"}
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {signal.created_at
                            ? new Date(signal.created_at).toLocaleDateString()
                            : "N/A"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Strategies Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Active Strategies</CardTitle>
              <CardDescription>Your configured trading strategies</CardDescription>
            </div>
            <Badge variant="outline">
              {customStrategies.length + advancedStrategies.filter((s) => s.enabled).length} active
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          ) : customStrategies.length === 0 && advancedStrategies.length === 0 ? (
            <div className="text-center py-8">
              <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
              <p className="text-muted-foreground">No strategies configured</p>
              <p className="text-sm text-muted-foreground mt-1">
                Create a strategy in the Strategies page
              </p>
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {/* Custom Strategies */}
              {customStrategies.map((strategy) => (
                <div
                  key={`custom-${strategy.id}`}
                  className="p-4 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium">{strategy.name}</span>
                    <Badge variant="outline">Custom</Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-green-500" />
                      <span className="text-muted-foreground">TP:</span>
                      <span className="text-green-500">{strategy.take_profit}%</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-red-500" />
                      <span className="text-muted-foreground">SL:</span>
                      <span className="text-red-500">{strategy.stop_loss}%</span>
                    </div>
                    {strategy.trailing_stop && (
                      <div className="flex items-center gap-2 col-span-2">
                        <div className="h-2 w-2 rounded-full bg-yellow-500" />
                        <span className="text-muted-foreground">Trail:</span>
                        <span className="text-yellow-500">{strategy.trailing_stop}%</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Advanced Strategies */}
              {advancedStrategies.map((strategy) => (
                <div
                  key={`advanced-${strategy.id}`}
                  className="p-4 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{strategy.name}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant={strategy.enabled ? "default" : "secondary"}>
                        {strategy.enabled ? "Active" : "Inactive"}
                      </Badge>
                      <Badge variant="outline" className="text-purple-500 border-purple-500">
                        Advanced
                      </Badge>
                    </div>
                  </div>
                  {strategy.description && (
                    <p className="text-xs text-muted-foreground mb-3 line-clamp-1">
                      {strategy.description}
                    </p>
                  )}
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-green-500" />
                      <span className="text-muted-foreground">TP:</span>
                      <span className="text-green-500">{strategy.default_take_profit}%</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-red-500" />
                      <span className="text-muted-foreground">SL:</span>
                      <span className="text-red-500">{strategy.default_stop_loss}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
