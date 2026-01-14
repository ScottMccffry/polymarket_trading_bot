"use client";

import { useState } from "react";
import { api, AdvancedStrategy } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

interface StrategyCardProps {
  strategy: AdvancedStrategy;
  onDelete: (id: number) => void;
}

export function StrategyCard({ strategy, onDelete }: StrategyCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this strategy?")) return;
    setIsDeleting(true);
    try {
      await api.deleteAdvancedStrategy(strategy.id);
      onDelete(strategy.id);
    } catch (error) {
      console.error("Failed to delete strategy:", error);
      alert("Failed to delete strategy");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-base">{strategy.name}</CardTitle>
            <Badge variant={strategy.enabled ? "default" : "secondary"}>
              {strategy.enabled ? "Active" : "Disabled"}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDelete}
            disabled={isDeleting}
            className="h-8 w-8 text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {strategy.description && (
          <p className="text-sm text-muted-foreground">{strategy.description}</p>
        )}

        <div className="grid grid-cols-3 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">TP:</span>
            <span className="text-green-500 ml-1">
              {strategy.default_take_profit}%
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">SL:</span>
            <span className="text-destructive ml-1">
              {strategy.default_stop_loss}%
            </span>
          </div>
          {strategy.default_trailing_stop && (
            <div>
              <span className="text-muted-foreground">Trail:</span>
              <span className="text-yellow-500 ml-1">
                {strategy.default_trailing_stop}%
              </span>
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {strategy.dynamic_trailing_enabled === 1 && (
            <Badge variant="outline" className="text-xs">
              Dynamic Trailing
            </Badge>
          )}
          {strategy.time_trailing_enabled === 1 && (
            <Badge variant="outline" className="text-xs">
              Time Trailing
            </Badge>
          )}
          {strategy.sources && strategy.sources.length > 0 && (
            <Badge variant="outline" className="text-xs">
              {strategy.sources.length} source
              {strategy.sources.length > 1 ? "s" : ""}
            </Badge>
          )}
          {strategy.partial_exits && strategy.partial_exits.length > 0 && (
            <Badge variant="outline" className="text-xs">
              {strategy.partial_exits.length} exit level
              {strategy.partial_exits.length > 1 ? "s" : ""}
            </Badge>
          )}
        </div>

        {strategy.created_at && (
          <p className="text-xs text-muted-foreground">
            Created: {new Date(strategy.created_at).toLocaleDateString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
