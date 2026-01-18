"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, AreaSeries, AreaData, Time } from "lightweight-charts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { TimeseriesResponse } from "@/lib/api";

interface EquityCurveProps {
  data: TimeseriesResponse | null;
  isLoading?: boolean;
  onGranularityChange?: (granularity: "daily" | "weekly" | "monthly") => void;
  granularity?: "daily" | "weekly" | "monthly";
}

export function EquityCurve({
  data,
  isLoading,
  onGranularityChange,
  granularity = "daily",
}: EquityCurveProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const seriesRef = useRef<ReturnType<ReturnType<typeof createChart>["addSeries"]> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "hsl(var(--foreground))",
      },
      grid: {
        vertLines: { color: "hsl(var(--border))" },
        horzLines: { color: "hsl(var(--border))" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 300,
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
    });

    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor: "hsl(142.1 76.2% 36.3%)",
      topColor: "hsla(142.1, 76.2%, 36.3%, 0.4)",
      bottomColor: "hsla(142.1, 76.2%, 36.3%, 0.1)",
      lineWidth: 2,
    });

    chartRef.current = chart;
    seriesRef.current = areaSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !data?.data) return;

    const chartData: AreaData<Time>[] = data.data.map((point) => ({
      time: point.timestamp as Time,
      value: point.value,
    }));

    seriesRef.current.setData(chartData);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Equity Curve</CardTitle>
          <CardDescription>Cumulative P&L over time</CardDescription>
        </div>
        <ToggleGroup
          type="single"
          value={granularity}
          onValueChange={(v) => v && onGranularityChange?.(v as "daily" | "weekly" | "monthly")}
        >
          <ToggleGroupItem value="daily" size="sm">1D</ToggleGroupItem>
          <ToggleGroupItem value="weekly" size="sm">1W</ToggleGroupItem>
          <ToggleGroupItem value="monthly" size="sm">1M</ToggleGroupItem>
        </ToggleGroup>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[300px] bg-muted animate-pulse rounded" />
        ) : (
          <div ref={chartContainerRef} className="h-[300px]" />
        )}
      </CardContent>
    </Card>
  );
}
