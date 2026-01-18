"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
  DollarSign,
  AlertTriangle,
} from "lucide-react";
import type { AnalyticsSummary } from "@/lib/api";

interface KpiCardsProps {
  summary: AnalyticsSummary;
  isLoading?: boolean;
}

function formatCurrency(value: number): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}$${Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatPercent(value: number): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function formatMetric(value: number | null, fallback = "N/A"): string {
  if (value === null) return fallback;
  return value.toFixed(2);
}

export function KpiCards({ summary, isLoading }: KpiCardsProps) {
  const { basic, risk, efficiency } = summary;

  const cards = [
    {
      title: "Total P&L",
      icon: DollarSign,
      value: formatCurrency(basic.total_realized_pnl),
      valueClass: basic.total_realized_pnl >= 0 ? "text-green-500" : "text-red-500",
      subtitle: `Unrealized: ${formatCurrency(basic.total_unrealized_pnl)}`,
    },
    {
      title: "Win Rate",
      icon: Target,
      value: `${basic.win_rate.toFixed(1)}%`,
      valueClass: basic.win_rate >= 50 ? "text-green-500" : "text-yellow-500",
      subtitle: `${basic.wins}W / ${basic.losses}L`,
      progress: basic.win_rate,
    },
    {
      title: "Sharpe Ratio",
      icon: risk.sharpe_ratio && risk.sharpe_ratio > 1 ? TrendingUp : TrendingDown,
      value: formatMetric(risk.sharpe_ratio),
      valueClass: (risk.sharpe_ratio ?? 0) > 1 ? "text-green-500" : "text-yellow-500",
      subtitle: `Sortino: ${formatMetric(risk.sortino_ratio)}`,
    },
    {
      title: "Max Drawdown",
      icon: AlertTriangle,
      value: formatCurrency(-risk.max_drawdown),
      valueClass: "text-red-500",
      subtitle: formatPercent(-risk.max_drawdown_percent),
    },
    {
      title: "Profit Factor",
      icon: Activity,
      value: formatMetric(efficiency.profit_factor),
      valueClass: (efficiency.profit_factor ?? 0) > 1.5 ? "text-green-500" : "text-yellow-500",
      subtitle: `Avg Win: $${basic.avg_win.toFixed(2)} | Avg Loss: $${basic.avg_loss.toFixed(2)}`,
    },
    {
      title: "Open Positions",
      icon: Activity,
      value: String(basic.open_trades),
      valueClass: "text-foreground",
      subtitle: `${basic.total_trades} total closed`,
    },
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-20 bg-muted animate-pulse rounded mb-2" />
              <div className="h-3 w-32 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${card.valueClass}`}>
              {card.value}
            </div>
            {card.progress !== undefined && (
              <Progress value={card.progress} className="mt-2" />
            )}
            <p className="text-xs text-muted-foreground mt-1">{card.subtitle}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
