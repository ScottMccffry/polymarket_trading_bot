"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Badge } from "@/components/ui/badge";
import { Wifi } from "lucide-react";

type TradingMode = "live" | "paper" | "all";

interface ModeToggleProps {
  value: TradingMode;
  onChange: (mode: TradingMode) => void;
  isConnected?: boolean;
}

export function ModeToggle({ value, onChange, isConnected }: ModeToggleProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {isConnected !== undefined && (
          <Badge variant={isConnected ? "default" : "secondary"} className="gap-1">
            <Wifi className={`h-3 w-3 ${isConnected ? "text-green-500" : "text-muted-foreground"}`} />
            {isConnected ? "Live" : "Disconnected"}
          </Badge>
        )}
      </div>
      <ToggleGroup
        type="single"
        value={value}
        onValueChange={(v) => v && onChange(v as TradingMode)}
      >
        <ToggleGroupItem value="live" size="sm" className="data-[state=on]:bg-green-500/20 data-[state=on]:text-green-500">
          Live
        </ToggleGroupItem>
        <ToggleGroupItem value="paper" size="sm" className="data-[state=on]:bg-yellow-500/20 data-[state=on]:text-yellow-500">
          Paper
        </ToggleGroupItem>
        <ToggleGroupItem value="all" size="sm">
          All
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}
