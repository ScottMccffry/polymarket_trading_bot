"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, TrendingDown, Target, Activity, DollarSign, Percent } from "lucide-react";
import { api, Position, Signal } from "@/lib/api";

// Chart configurations
const performanceChartConfig = {
  pnl: {
    label: "P&L",
    color: "hsl(var(--chart-1))",
  },
  cumulative: {
    label: "Cumulative",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig;

const winLossChartConfig = {
  wins: {
    label: "Wins",
    color: "hsl(142, 76%, 36%)",
  },
  losses: {
    label: "Losses",
    color: "hsl(0, 84%, 60%)",
  },
} satisfies ChartConfig;

const sourceChartConfig = {
  trades: {
    label: "Trades",
    color: "hsl(var(--chart-1))",
  },
  winRate: {
    label: "Win Rate %",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig;

// Generate performance data from actual positions
function generatePerformanceData(positions: Position[]) {
  const closedPositions = positions
    .filter(p => p.status === "closed" && p.closed_at)
    .sort((a, b) => new Date(a.closed_at!).getTime() - new Date(b.closed_at!).getTime());

  if (closedPositions.length === 0) return [];

  const dailyPnl: Record<string, number> = {};
  closedPositions.forEach(p => {
    const date = new Date(p.closed_at!).toLocaleDateString("en-US", { month: "short", day: "numeric" });
    dailyPnl[date] = (dailyPnl[date] || 0) + (p.realized_pnl || 0);
  });

  let cumulative = 0;
  return Object.entries(dailyPnl).map(([date, pnl]) => {
    cumulative += pnl;
    return {
      date,
      pnl: Math.round(pnl * 100) / 100,
      cumulative: Math.round(cumulative * 100) / 100,
    };
  });
}

// Calculate statistics from positions
function calculateStats(positions: Position[]) {
  const closedPositions = positions.filter(p => p.status === "closed");
  const openPositions = positions.filter(p => p.status === "open");

  const wins = closedPositions.filter(p => (p.realized_pnl || 0) > 0);
  const losses = closedPositions.filter(p => (p.realized_pnl || 0) <= 0);

  const totalRealizedPnl = closedPositions.reduce((sum, p) => sum + (p.realized_pnl || 0), 0);
  const totalUnrealizedPnl = openPositions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0);
  const avgWin = wins.length > 0
    ? wins.reduce((sum, p) => sum + (p.realized_pnl || 0), 0) / wins.length
    : 0;
  const avgLoss = losses.length > 0
    ? Math.abs(losses.reduce((sum, p) => sum + (p.realized_pnl || 0), 0) / losses.length)
    : 0;

  const winRate = closedPositions.length > 0
    ? (wins.length / closedPositions.length) * 100
    : 0;

  const profitFactor = avgLoss > 0 ? avgWin / avgLoss : avgWin > 0 ? Infinity : 0;

  // Group by source
  const bySource = positions.reduce((acc, p) => {
    const source = p.source || "Unknown";
    if (!acc[source]) {
      acc[source] = { total: 0, wins: 0, pnl: 0 };
    }
    acc[source].total++;
    if (p.status === "closed" && (p.realized_pnl || 0) > 0) {
      acc[source].wins++;
    }
    acc[source].pnl += (p.realized_pnl || 0) + (p.unrealized_pnl || 0);
    return acc;
  }, {} as Record<string, { total: number; wins: number; pnl: number }>);

  const sourceData = Object.entries(bySource).map(([source, data]) => ({
    source: source.length > 15 ? source.slice(0, 15) + "..." : source,
    trades: data.total,
    winRate: data.total > 0 ? Math.round((data.wins / data.total) * 100) : 0,
    pnl: Math.round(data.pnl * 100) / 100,
  }));

  return {
    totalTrades: closedPositions.length,
    openTrades: openPositions.length,
    winRate: Math.round(winRate * 10) / 10,
    totalRealizedPnl: Math.round(totalRealizedPnl * 100) / 100,
    totalUnrealizedPnl: Math.round(totalUnrealizedPnl * 100) / 100,
    avgWin: Math.round(avgWin * 100) / 100,
    avgLoss: Math.round(avgLoss * 100) / 100,
    profitFactor: profitFactor === Infinity ? "∞" : Math.round(profitFactor * 100) / 100,
    wins: wins.length,
    losses: losses.length,
    sourceData,
  };
}

export default function Statistics() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [positionsData, signalsData] = await Promise.all([
          api.getPositions(),
          api.getSignals(),
        ]);
        setPositions(positionsData);
        setSignals(signalsData);
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const stats = calculateStats(positions);
  const performanceData = generatePerformanceData(positions);

  const winLossData = [
    { name: "wins", value: stats.wins, fill: "hsl(142, 76%, 36%)" },
    { name: "losses", value: stats.losses, fill: "hsl(0, 84%, 60%)" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Statistics</h1>
        <p className="text-muted-foreground">Trading performance analytics and metrics</p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalTrades}</div>
            <p className="text-xs text-muted-foreground">
              {stats.openTrades} currently open
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.winRate}%</div>
            <Progress value={stats.winRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Realized P&L</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.totalRealizedPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
              ${stats.totalRealizedPnl.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Unrealized: ${stats.totalUnrealizedPnl.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Profit Factor</CardTitle>
            <Percent className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.profitFactor}</div>
            <p className="text-xs text-muted-foreground">
              Avg Win: ${stats.avgWin} | Avg Loss: ${stats.avgLoss}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Performance Chart */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Performance Over Time</CardTitle>
            <CardDescription>Daily P&L and cumulative returns (last 30 days)</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={performanceChartConfig} className="h-[300px] w-full">
              <AreaChart data={performanceData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `$${value}`}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area
                  type="monotone"
                  dataKey="cumulative"
                  stroke="hsl(var(--chart-2))"
                  fillOpacity={1}
                  fill="url(#colorPnl)"
                />
                <Line
                  type="monotone"
                  dataKey="pnl"
                  stroke="hsl(var(--chart-1))"
                  strokeWidth={2}
                  dot={false}
                />
              </AreaChart>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Win/Loss Pie Chart */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Win/Loss Distribution</CardTitle>
            <CardDescription>Breakdown of winning vs losing trades</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={winLossChartConfig} className="h-[300px] w-full">
              <PieChart>
                <Pie
                  data={winLossData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {winLossData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
              </PieChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Source Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Performance by Signal Source</CardTitle>
          <CardDescription>Trade count and win rate by signal source</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={sourceChartConfig} className="h-[300px] w-full">
            <BarChart data={stats.sourceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="source"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `${value}%`}
              />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar yAxisId="left" dataKey="trades" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="right" dataKey="winRate" fill="hsl(var(--chart-2))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Additional Metrics */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Risk Metrics</CardTitle>
            <CardDescription>Risk-adjusted performance indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Sharpe Ratio</span>
                <span className="font-medium text-muted-foreground">N/A</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Max Drawdown</span>
                <span className="font-medium text-muted-foreground">N/A</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Recovery Factor</span>
                <span className="font-medium text-muted-foreground">N/A</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Sortino Ratio</span>
                <span className="font-medium text-muted-foreground">N/A</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Trading Activity</CardTitle>
            <CardDescription>Signal and execution metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Signals</span>
                <span className="font-medium">{signals.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Execution Rate</span>
                <span className="font-medium">
                  {signals.length > 0
                    ? `${Math.round((positions.length / signals.length) * 100)}%`
                    : "N/A"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Avg. Hold Time</span>
                <span className="font-medium text-muted-foreground">N/A</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Best Trade</span>
                <span className="font-medium text-muted-foreground">N/A</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
