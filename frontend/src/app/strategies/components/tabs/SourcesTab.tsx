"use client";

import { SourceFormData, AVAILABLE_SOURCES } from "../types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Trash2 } from "lucide-react";

interface SourcesTabProps {
  sources: SourceFormData[];
  onAddSource: () => void;
  onRemoveSource: (index: number) => void;
  onUpdateSource: (index: number, field: keyof SourceFormData, value: string) => void;
}

export function SourcesTab({
  sources,
  onAddSource,
  onRemoveSource,
  onUpdateSource,
}: SourcesTabProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium">Signal Sources</h3>
          <p className="text-sm text-muted-foreground">Configure per-source overrides</p>
        </div>
        <Button type="button" size="sm" onClick={onAddSource}>
          Add Source
        </Button>
      </div>

      {sources.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">No sources configured</p>
            <p className="text-sm text-muted-foreground mt-1">
              Add sources to set per-source parameters
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {sources.map((source, index) => (
            <Card key={index}>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between mb-3">
                  <Select
                    value={source.source}
                    onValueChange={(value) => onUpdateSource(index, "source", value)}
                  >
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="Select source..." />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_SOURCES.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => onRemoveSource(index)}
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-4 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Take Profit (%)</Label>
                    <Input
                      type="number"
                      value={source.take_profit}
                      onChange={(e) =>
                        onUpdateSource(index, "take_profit", e.target.value)
                      }
                      step="0.1"
                      placeholder="Override"
                      className="h-8"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Stop Loss (%)</Label>
                    <Input
                      type="number"
                      value={source.stop_loss}
                      onChange={(e) =>
                        onUpdateSource(index, "stop_loss", e.target.value)
                      }
                      step="0.1"
                      placeholder="Override"
                      className="h-8"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Trailing (%)</Label>
                    <Input
                      type="number"
                      value={source.trailing_stop}
                      onChange={(e) =>
                        onUpdateSource(index, "trailing_stop", e.target.value)
                      }
                      step="0.1"
                      placeholder="Override"
                      className="h-8"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Size Multiplier</Label>
                    <Input
                      type="number"
                      value={source.position_size_multiplier}
                      onChange={(e) =>
                        onUpdateSource(
                          index,
                          "position_size_multiplier",
                          e.target.value
                        )
                      }
                      step="0.1"
                      min="0.1"
                      className="h-8"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
