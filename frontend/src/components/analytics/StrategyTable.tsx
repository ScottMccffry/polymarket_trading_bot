"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { AnalyticsSummaryResponse } from "@/lib/api";

interface StrategyTableProps {
  data: AnalyticsSummaryResponse | null;
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
  return `${value.toFixed(1)}%`;
}

function formatMetric(value: number | null): string {
  if (value === null) return "N/A";
  return value.toFixed(2);
}

export function StrategyTable({ data, isLoading }: StrategyTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Strategy Performance</CardTitle>
          <CardDescription>Comparison across trading strategies</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  if (!data?.groups || data.groups.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Strategy Performance</CardTitle>
          <CardDescription>Comparison across trading strategies</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            No strategy data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Strategy Performance</CardTitle>
        <CardDescription>Comparison across trading strategies</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Strategy</TableHead>
              <TableHead className="text-right">Trades</TableHead>
              <TableHead className="text-right">Win Rate</TableHead>
              <TableHead className="text-right">P&L</TableHead>
              <TableHead className="text-right">Sharpe</TableHead>
              <TableHead className="text-right">Profit Factor</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.groups.map((group) => (
              <TableRow key={group.group_value}>
                <TableCell className="font-medium">
                  {group.group_value || "Unknown"}
                </TableCell>
                <TableCell className="text-right">
                  {group.summary.basic.total_trades}
                </TableCell>
                <TableCell className="text-right">
                  <span
                    className={
                      group.summary.basic.win_rate >= 50
                        ? "text-green-500"
                        : "text-yellow-500"
                    }
                  >
                    {formatPercent(group.summary.basic.win_rate)}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <span
                    className={
                      group.summary.basic.total_realized_pnl >= 0
                        ? "text-green-500"
                        : "text-red-500"
                    }
                  >
                    {formatCurrency(group.summary.basic.total_realized_pnl)}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  {formatMetric(group.summary.risk.sharpe_ratio)}
                </TableCell>
                <TableCell className="text-right">
                  {formatMetric(group.summary.efficiency.profit_factor)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
