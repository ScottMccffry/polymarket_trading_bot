"use client";

import { StrategyFormData } from "../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

interface TrailingTabProps {
  formData: StrategyFormData;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function TrailingTab({ formData, onChange }: TrailingTabProps) {
  const handleSwitchChange = (name: string, checked: boolean) => {
    const syntheticEvent = {
      target: {
        name,
        type: "checkbox",
        checked,
      },
    } as React.ChangeEvent<HTMLInputElement>;
    onChange(syntheticEvent);
  };

  return (
    <div className="space-y-6">
      {/* Dynamic Trailing */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Dynamic Trailing Stop</CardTitle>
              <CardDescription>
                Tighten trailing stop as profit increases
              </CardDescription>
            </div>
            <Switch
              checked={formData.dynamic_trailing_enabled}
              onCheckedChange={(checked) =>
                handleSwitchChange("dynamic_trailing_enabled", checked)
              }
            />
          </div>
        </CardHeader>
        {formData.dynamic_trailing_enabled && (
          <CardContent className="pt-0">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="dynamic_trailing_base">Base (%)</Label>
                <Input
                  id="dynamic_trailing_base"
                  name="dynamic_trailing_base"
                  type="number"
                  value={formData.dynamic_trailing_base}
                  onChange={onChange}
                  step="0.1"
                />
                <p className="text-xs text-muted-foreground">Initial trailing %</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="dynamic_trailing_tight">Tight (%)</Label>
                <Input
                  id="dynamic_trailing_tight"
                  name="dynamic_trailing_tight"
                  type="number"
                  value={formData.dynamic_trailing_tight}
                  onChange={onChange}
                  step="0.1"
                />
                <p className="text-xs text-muted-foreground">Tightened trailing %</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="dynamic_trailing_threshold">Threshold (%)</Label>
                <Input
                  id="dynamic_trailing_threshold"
                  name="dynamic_trailing_threshold"
                  type="number"
                  value={formData.dynamic_trailing_threshold}
                  onChange={onChange}
                  step="0.1"
                />
                <p className="text-xs text-muted-foreground">Profit to trigger tight</p>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Time-based Trailing */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Time-based Trailing Stop</CardTitle>
              <CardDescription>
                Tighten trailing stop as time passes
              </CardDescription>
            </div>
            <Switch
              checked={formData.time_trailing_enabled}
              onCheckedChange={(checked) =>
                handleSwitchChange("time_trailing_enabled", checked)
              }
            />
          </div>
        </CardHeader>
        {formData.time_trailing_enabled && (
          <CardContent className="pt-0">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="time_trailing_start_hours">Start (hours)</Label>
                <Input
                  id="time_trailing_start_hours"
                  name="time_trailing_start_hours"
                  type="number"
                  value={formData.time_trailing_start_hours}
                  onChange={onChange}
                  step="1"
                />
                <p className="text-xs text-muted-foreground">When to start tightening</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="time_trailing_max_hours">Max (hours)</Label>
                <Input
                  id="time_trailing_max_hours"
                  name="time_trailing_max_hours"
                  type="number"
                  value={formData.time_trailing_max_hours}
                  onChange={onChange}
                  step="1"
                />
                <p className="text-xs text-muted-foreground">When fully tightened</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="time_trailing_tight">Tight (%)</Label>
                <Input
                  id="time_trailing_tight"
                  name="time_trailing_tight"
                  type="number"
                  value={formData.time_trailing_tight}
                  onChange={onChange}
                  step="0.1"
                />
                <p className="text-xs text-muted-foreground">Final trailing %</p>
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
