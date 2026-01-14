"use client";

import { useState, useEffect } from "react";
import {
  api,
  AdvancedStrategyCreate,
  AdvancedStrategySourceCreate,
  AdvancedStrategyPartialExitCreate,
} from "@/lib/api";
import {
  StrategyFormData,
  SourceFormData,
  PartialExitFormData,
  initialFormData,
  initialSourceData,
  initialPartialExitData,
} from "./types";
import {
  BasicTab,
  TrailingTab,
  SourcesTab,
  PartialExitsTab,
  FiltersTab,
} from "./tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

type TabId = "basic" | "trailing" | "sources" | "exits" | "filters";

interface CreateStrategyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialData?: Partial<StrategyFormData>;
}

const TABS: { id: TabId; label: string }[] = [
  { id: "basic", label: "Basic" },
  { id: "trailing", label: "Trailing Stops" },
  { id: "sources", label: "Sources" },
  { id: "exits", label: "Partial Exits" },
  { id: "filters", label: "Filters" },
];

export function CreateStrategyModal({
  isOpen,
  onClose,
  onSuccess,
  initialData,
}: CreateStrategyModalProps) {
  const [formData, setFormData] = useState<StrategyFormData>({
    ...initialFormData,
    ...initialData,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<TabId>("basic");

  useEffect(() => {
    if (initialData) {
      setFormData({ ...initialFormData, ...initialData });
    }
  }, [initialData]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    if (type === "checkbox") {
      setFormData((prev) => ({
        ...prev,
        [name]: (e.target as HTMLInputElement).checked,
      }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  // Source management
  const addSource = () => {
    setFormData((prev) => ({
      ...prev,
      sources: [...prev.sources, { ...initialSourceData }],
    }));
  };

  const removeSource = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      sources: prev.sources.filter((_, i) => i !== index),
    }));
  };

  const updateSource = (
    index: number,
    field: keyof SourceFormData,
    value: string
  ) => {
    setFormData((prev) => ({
      ...prev,
      sources: prev.sources.map((s, i) =>
        i === index ? { ...s, [field]: value } : s
      ),
    }));
  };

  // Partial exit management
  const addPartialExit = () => {
    setFormData((prev) => ({
      ...prev,
      partial_exits: [...prev.partial_exits, { ...initialPartialExitData }],
    }));
  };

  const removePartialExit = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      partial_exits: prev.partial_exits.filter((_, i) => i !== index),
    }));
  };

  const updatePartialExit = (
    index: number,
    field: keyof PartialExitFormData,
    value: string
  ) => {
    setFormData((prev) => ({
      ...prev,
      partial_exits: prev.partial_exits.map((p, i) =>
        i === index ? { ...p, [field]: value } : p
      ),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const sources: AdvancedStrategySourceCreate[] = formData.sources
        .filter((s) => s.source)
        .map((s) => ({
          source: s.source,
          take_profit: s.take_profit ? parseFloat(s.take_profit) : null,
          stop_loss: s.stop_loss ? parseFloat(s.stop_loss) : null,
          trailing_stop: s.trailing_stop ? parseFloat(s.trailing_stop) : null,
          position_size_multiplier: s.position_size_multiplier
            ? parseFloat(s.position_size_multiplier)
            : 1.0,
        }));

      const partial_exits: AdvancedStrategyPartialExitCreate[] =
        formData.partial_exits
          .filter((p) => p.exit_percent && p.threshold)
          .map((p, index) => ({
            exit_order: index + 1,
            exit_percent: parseFloat(p.exit_percent),
            threshold: parseFloat(p.threshold),
          }));

      const strategy: AdvancedStrategyCreate = {
        name: formData.name,
        description: formData.description || null,
        default_take_profit: parseFloat(formData.default_take_profit),
        default_stop_loss: parseFloat(formData.default_stop_loss),
        default_trailing_stop: formData.default_trailing_stop
          ? parseFloat(formData.default_trailing_stop)
          : null,
        dynamic_trailing_enabled: formData.dynamic_trailing_enabled,
        dynamic_trailing_base: parseFloat(formData.dynamic_trailing_base),
        dynamic_trailing_tight: parseFloat(formData.dynamic_trailing_tight),
        dynamic_trailing_threshold: parseFloat(
          formData.dynamic_trailing_threshold
        ),
        time_trailing_enabled: formData.time_trailing_enabled,
        time_trailing_start_hours: parseFloat(
          formData.time_trailing_start_hours
        ),
        time_trailing_max_hours: parseFloat(formData.time_trailing_max_hours),
        time_trailing_tight: parseFloat(formData.time_trailing_tight),
        min_source_win_rate: formData.min_source_win_rate
          ? parseFloat(formData.min_source_win_rate)
          : null,
        min_source_profit_factor: formData.min_source_profit_factor
          ? parseFloat(formData.min_source_profit_factor)
          : null,
        min_source_trades: formData.min_source_trades
          ? parseInt(formData.min_source_trades)
          : null,
        lookback_days: parseInt(formData.lookback_days),
        enabled: true,
        sources: sources.length > 0 ? sources : undefined,
        partial_exits: partial_exits.length > 0 ? partial_exits : undefined,
      };

      await api.createAdvancedStrategy(strategy);
      setFormData(initialFormData);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create strategy");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Create Advanced Strategy</DialogTitle>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value as TabId)}
          className="flex-1 flex flex-col overflow-hidden"
        >
          <TabsList className="grid w-full grid-cols-5">
            {TABS.map((tab) => (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className="flex items-center gap-1"
              >
                {tab.label}
                {tab.id === "sources" && formData.sources.length > 0 && (
                  <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 justify-center">
                    {formData.sources.length}
                  </Badge>
                )}
                {tab.id === "exits" && formData.partial_exits.length > 0 && (
                  <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 justify-center">
                    {formData.partial_exits.length}
                  </Badge>
                )}
              </TabsTrigger>
            ))}
          </TabsList>

          <form
            onSubmit={handleSubmit}
            className="flex-1 overflow-y-auto py-4"
          >
            <TabsContent value="basic" className="mt-0">
              <BasicTab formData={formData} onChange={handleChange} />
            </TabsContent>
            <TabsContent value="trailing" className="mt-0">
              <TrailingTab formData={formData} onChange={handleChange} />
            </TabsContent>
            <TabsContent value="sources" className="mt-0">
              <SourcesTab
                sources={formData.sources}
                onAddSource={addSource}
                onRemoveSource={removeSource}
                onUpdateSource={updateSource}
              />
            </TabsContent>
            <TabsContent value="exits" className="mt-0">
              <PartialExitsTab
                partialExits={formData.partial_exits}
                onAddExit={addPartialExit}
                onRemoveExit={removePartialExit}
                onUpdateExit={updatePartialExit}
              />
            </TabsContent>
            <TabsContent value="filters" className="mt-0">
              <FiltersTab formData={formData} onChange={handleChange} />
            </TabsContent>
          </form>
        </Tabs>

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? "Creating..." : "Create Strategy"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
