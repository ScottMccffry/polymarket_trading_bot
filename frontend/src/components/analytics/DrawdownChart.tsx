"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, AreaSeries, AreaData, Time } from "lightweight-charts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { TimeseriesResponse } from "@/lib/api";

interface DrawdownChartProps {
  data: TimeseriesResponse | null;
  isLoading?: boolean;
}

export function DrawdownChart({ data, isLoading }: DrawdownChartProps) {
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
      height: 200,
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
    });

    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor: "hsl(0 84.2% 60.2%)",
      topColor: "hsla(0, 84.2%, 60.2%, 0.4)",
      bottomColor: "hsla(0, 84.2%, 60.2%, 0.1)",
      lineWidth: 2,
      invertFilledArea: true,
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
      value: Math.abs(point.value),
    }));

    seriesRef.current.setData(chartData);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Drawdown</CardTitle>
        <CardDescription>Maximum loss from peak equity</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[200px] bg-muted animate-pulse rounded" />
        ) : (
          <div ref={chartContainerRef} className="h-[200px]" />
        )}
      </CardContent>
    </Card>
  );
}
