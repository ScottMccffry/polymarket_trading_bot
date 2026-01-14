"use client";

import { StrategyFormData } from "../types";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface FiltersTabProps {
  formData: StrategyFormData;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function FiltersTab({ formData, onChange }: FiltersTabProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-medium mb-2">Statistical Filters</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Filter signals based on source performance
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="min_source_win_rate">Min Win Rate (%)</Label>
          <Input
            id="min_source_win_rate"
            name="min_source_win_rate"
            type="number"
            value={formData.min_source_win_rate}
            onChange={onChange}
            step="1"
            min="0"
            max="100"
            placeholder="50"
          />
          <p className="text-xs text-muted-foreground">
            Only accept signals from sources with this win rate
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="min_source_profit_factor">Min Profit Factor</Label>
          <Input
            id="min_source_profit_factor"
            name="min_source_profit_factor"
            type="number"
            value={formData.min_source_profit_factor}
            onChange={onChange}
            step="0.1"
            min="0"
            placeholder="1.5"
          />
          <p className="text-xs text-muted-foreground">Ratio of wins to losses</p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="min_source_trades">Min Source Trades</Label>
          <Input
            id="min_source_trades"
            name="min_source_trades"
            type="number"
            value={formData.min_source_trades}
            onChange={onChange}
            step="1"
            min="0"
            placeholder="10"
          />
          <p className="text-xs text-muted-foreground">
            Minimum trades for statistical significance
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="lookback_days">Lookback Days</Label>
          <Input
            id="lookback_days"
            name="lookback_days"
            type="number"
            value={formData.lookback_days}
            onChange={onChange}
            step="1"
            min="1"
            placeholder="30"
          />
          <p className="text-xs text-muted-foreground">
            Days to look back for statistics
          </p>
        </div>
      </div>
    </div>
  );
}
