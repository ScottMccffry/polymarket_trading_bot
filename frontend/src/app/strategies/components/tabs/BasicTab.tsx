"use client";

import { StrategyFormData } from "../types";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface BasicTabProps {
  formData: StrategyFormData;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
}

export function BasicTab({ formData, onChange }: BasicTabProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">
          Strategy Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          name="name"
          value={formData.name}
          onChange={onChange}
          placeholder="My Strategy"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={onChange}
          rows={2}
          placeholder="Optional description..."
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="default_take_profit">
            Take Profit (%) <span className="text-destructive">*</span>
          </Label>
          <Input
            id="default_take_profit"
            name="default_take_profit"
            type="number"
            value={formData.default_take_profit}
            onChange={onChange}
            step="0.1"
            min="0"
            placeholder="20"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="default_stop_loss">
            Stop Loss (%) <span className="text-destructive">*</span>
          </Label>
          <Input
            id="default_stop_loss"
            name="default_stop_loss"
            type="number"
            value={formData.default_stop_loss}
            onChange={onChange}
            step="0.1"
            min="0"
            placeholder="10"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="default_trailing_stop">Trailing Stop (%)</Label>
          <Input
            id="default_trailing_stop"
            name="default_trailing_stop"
            type="number"
            value={formData.default_trailing_stop}
            onChange={onChange}
            step="0.1"
            min="0"
            placeholder="5"
          />
        </div>
      </div>
    </div>
  );
}
