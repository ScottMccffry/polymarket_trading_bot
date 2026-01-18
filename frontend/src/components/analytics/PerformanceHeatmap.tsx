"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import type { HeatmapResponse } from "@/lib/api";

interface PerformanceHeatmapProps {
  data: HeatmapResponse | null;
  isLoading?: boolean;
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function getColorForValue(value: number, min: number, max: number): string {
  if (value === 0) return "hsl(var(--muted))";

  const range = Math.max(Math.abs(min), Math.abs(max));
  if (range === 0) return "hsl(var(--muted))";

  const normalizedValue = value / range;

  if (normalizedValue > 0) {
    // Green for positive
    const intensity = Math.min(normalizedValue, 1);
    return `hsla(142.1, 76.2%, 36.3%, ${0.2 + intensity * 0.6})`;
  } else {
    // Red for negative
    const intensity = Math.min(Math.abs(normalizedValue), 1);
    return `hsla(0, 84.2%, 60.2%, ${0.2 + intensity * 0.6})`;
  }
}

function formatValue(value: number): string {
  if (value >= 0) return `+$${value.toFixed(2)}`;
  return `-$${Math.abs(value).toFixed(2)}`;
}

export function PerformanceHeatmap({ data, isLoading }: PerformanceHeatmapProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Performance by Day</CardTitle>
          <CardDescription>P&L distribution across weekdays</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  if (!data?.cells || data.cells.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Performance by Day</CardTitle>
          <CardDescription>P&L distribution across weekdays</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Build map from day -> value
  const dayValues = new Map<string, number>();
  data.cells.forEach((cell) => {
    dayValues.set(cell.x, cell.value);
  });

  const values = Array.from(dayValues.values());
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Performance by Day</CardTitle>
        <CardDescription>P&L distribution across weekdays</CardDescription>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          <div className="grid grid-cols-7 gap-2">
            {DAYS.map((day) => {
              const value = dayValues.get(day) ?? 0;
              const bgColor = getColorForValue(value, min, max);

              return (
                <Tooltip key={day}>
                  <TooltipTrigger asChild>
                    <div
                      className="aspect-square rounded-md flex flex-col items-center justify-center cursor-pointer transition-transform hover:scale-105"
                      style={{ backgroundColor: bgColor }}
                    >
                      <span className="text-xs font-medium">{day}</span>
                      <span className={`text-sm font-bold ${value >= 0 ? "text-green-700 dark:text-green-400" : "text-red-700 dark:text-red-400"}`}>
                        {value !== 0 ? (value >= 0 ? "+" : "") + value.toFixed(0) : "-"}
                      </span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{day}: {formatValue(value)}</p>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>
        </TooltipProvider>

        {/* Legend */}
        <div className="flex items-center justify-center gap-4 mt-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: "hsla(0, 84.2%, 60.2%, 0.6)" }} />
            <span>Loss</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-muted" />
            <span>Break-even</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: "hsla(142.1, 76.2%, 36.3%, 0.6)" }} />
            <span>Profit</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
