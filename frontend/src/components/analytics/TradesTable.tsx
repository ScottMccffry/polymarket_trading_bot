"use client";

import { format } from "date-fns";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { TradesResponse } from "@/lib/api";

interface TradesTableProps {
  data: TradesResponse | null;
  isLoading?: boolean;
  onLoadMore?: () => void;
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

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  try {
    return format(new Date(dateStr), "MMM d, HH:mm");
  } catch {
    return "-";
  }
}

export function TradesTable({ data, isLoading, onLoadMore }: TradesTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
          <CardDescription>Detailed trade history</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  if (!data?.trades || data.trades.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
          <CardDescription>Detailed trade history</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            No trades found
          </div>
        </CardContent>
      </Card>
    );
  }

  const hasMore = data.trades.length >= 100;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Trades</CardTitle>
        <CardDescription>
          Showing {data.trades.length} trades
          {data.total_count && ` of ${data.total_count}`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Market</TableHead>
                <TableHead>Side</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead className="text-right">Entry</TableHead>
                <TableHead className="text-right">Exit</TableHead>
                <TableHead className="text-right">P&L</TableHead>
                <TableHead className="text-right">P&L %</TableHead>
                <TableHead>Closed</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.trades.map((trade) => (
                <TableRow key={trade.id} className={trade.trading_mode === "paper" ? "opacity-60" : ""}>
                  <TableCell className="max-w-[200px] truncate" title={trade.market_question || ""}>
                    {trade.market_question || "Unknown"}
                    {trade.trading_mode === "paper" && (
                      <Badge variant="outline" className="ml-2 text-xs">
                        Paper
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={trade.side === "YES" ? "default" : "secondary"}
                      className={trade.side === "YES" ? "bg-green-500/20 text-green-500" : "bg-red-500/20 text-red-500"}
                    >
                      {trade.side}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {trade.strategy_name || "-"}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    ${trade.entry_price?.toFixed(3) ?? "-"}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {trade.exit_price ? `$${trade.exit_price.toFixed(3)}` : "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={
                        (trade.realized_pnl ?? 0) >= 0
                          ? "text-green-500"
                          : "text-red-500"
                      }
                    >
                      {trade.realized_pnl !== null
                        ? formatCurrency(trade.realized_pnl)
                        : "-"}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={
                        (trade.realized_pnl_percent ?? 0) >= 0
                          ? "text-green-500"
                          : "text-red-500"
                      }
                    >
                      {trade.realized_pnl_percent !== null
                        ? formatPercent(trade.realized_pnl_percent)
                        : "-"}
                    </span>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(trade.closed_at)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {hasMore && onLoadMore && (
          <div className="flex justify-center mt-4">
            <Button variant="outline" onClick={onLoadMore}>
              Load More
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
