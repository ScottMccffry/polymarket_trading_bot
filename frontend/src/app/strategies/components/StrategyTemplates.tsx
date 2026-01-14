"use client";

import { StrategyFormData, STRATEGY_TEMPLATES } from "./types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface StrategyTemplatesProps {
  onSelectTemplate: (template: Partial<StrategyFormData>) => void;
}

export function StrategyTemplates({ onSelectTemplate }: StrategyTemplatesProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Strategy Templates</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card
            onClick={() => onSelectTemplate(STRATEGY_TEMPLATES.conservative)}
            className="cursor-pointer hover:border-green-500 transition-colors"
          >
            <CardContent className="pt-6">
              <h3 className="font-medium mb-2">Conservative</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Low risk, steady returns. Single partial exit at 10%.
              </p>
              <p className="text-xs text-muted-foreground">
                TP: 15% | SL: 5% | Trail: 3%
              </p>
            </CardContent>
          </Card>
          <Card
            onClick={() => onSelectTemplate(STRATEGY_TEMPLATES.aggressive)}
            className="cursor-pointer hover:border-red-500 transition-colors"
          >
            <CardContent className="pt-6">
              <h3 className="font-medium mb-2">Aggressive</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Higher risk with dynamic trailing. Multiple exit levels.
              </p>
              <p className="text-xs text-muted-foreground">
                TP: 30% | SL: 15% | Dynamic Trail
              </p>
            </CardContent>
          </Card>
          <Card
            onClick={() => onSelectTemplate(STRATEGY_TEMPLATES.news)}
            className="cursor-pointer hover:border-blue-500 transition-colors"
          >
            <CardContent className="pt-6">
              <h3 className="font-medium mb-2">News-Based</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Time-sensitive trailing for news events.
              </p>
              <p className="text-xs text-muted-foreground">
                TP: 20% | SL: 10% | Time Trail: 12-48h
              </p>
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  );
}
