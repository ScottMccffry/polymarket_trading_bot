"use client";

import { PartialExitFormData } from "../types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2 } from "lucide-react";

interface PartialExitsTabProps {
  partialExits: PartialExitFormData[];
  onAddExit: () => void;
  onRemoveExit: (index: number) => void;
  onUpdateExit: (
    index: number,
    field: keyof PartialExitFormData,
    value: string
  ) => void;
}

export function PartialExitsTab({
  partialExits,
  onAddExit,
  onRemoveExit,
  onUpdateExit,
}: PartialExitsTabProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium">Partial Exit Levels</h3>
          <p className="text-sm text-muted-foreground">
            Scale out of positions at multiple profit levels
          </p>
        </div>
        <Button type="button" size="sm" onClick={onAddExit}>
          Add Exit Level
        </Button>
      </div>

      {partialExits.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">No partial exits configured</p>
            <p className="text-sm text-muted-foreground mt-1">
              Add exit levels to scale out of positions
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {partialExits.map((exit, index) => (
            <Card key={index}>
              <CardContent className="py-4">
                <div className="flex items-center gap-4">
                  <div className="text-muted-foreground font-medium">#{index + 1}</div>
                  <div className="flex-1 space-y-1">
                    <Label className="text-xs">Exit % of Position</Label>
                    <Input
                      type="number"
                      value={exit.exit_percent}
                      onChange={(e) =>
                        onUpdateExit(index, "exit_percent", e.target.value)
                      }
                      step="1"
                      min="1"
                      max="100"
                      placeholder="50"
                    />
                  </div>
                  <div className="flex-1 space-y-1">
                    <Label className="text-xs">At Profit Threshold (%)</Label>
                    <Input
                      type="number"
                      value={exit.threshold}
                      onChange={(e) =>
                        onUpdateExit(index, "threshold", e.target.value)
                      }
                      step="0.1"
                      min="0"
                      placeholder="10"
                    />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => onRemoveExit(index)}
                    className="mt-4 h-8 w-8 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card className="bg-muted/50">
        <CardContent className="py-3">
          <p className="text-sm">
            <span className="font-medium">Example:</span> Exit 50% at 10% profit,
            then 30% at 15% profit, remaining 20% at take profit.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
