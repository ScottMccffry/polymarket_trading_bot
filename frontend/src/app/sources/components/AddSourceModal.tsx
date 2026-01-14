"use client";

import { useState, useEffect } from "react";
import { Source, SourceType, SourceFormData, SOURCE_TYPE_INFO } from "./types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

interface AddSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: SourceFormData) => Promise<void>;
  editingSource?: Source | null;
}

export function AddSourceModal({
  isOpen,
  onClose,
  onSave,
  editingSource,
}: AddSourceModalProps) {
  const [formData, setFormData] = useState<SourceFormData>({
    name: "",
    type: "telegram",
    enabled: true,
    config: {},
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (editingSource) {
      setFormData({
        name: editingSource.name,
        type: editingSource.type,
        enabled: editingSource.enabled,
        config: editingSource.config,
      });
    } else {
      setFormData({
        name: "",
        type: "telegram",
        enabled: true,
        config: {},
      });
    }
  }, [editingSource, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await onSave(formData);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save source");
    } finally {
      setIsLoading(false);
    }
  };

  const updateConfig = (key: string, value: unknown) => {
    setFormData((prev) => ({
      ...prev,
      config: { ...prev.config, [key]: value },
    }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {editingSource ? "Edit Source" : "Add New Source"}
          </DialogTitle>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="source-name">
              Source Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="source-name"
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="My Signal Source"
              required
            />
          </div>

          {/* Type Selection */}
          {!editingSource && (
            <div className="space-y-2">
              <Label>Source Type</Label>
              <div className="grid grid-cols-2 gap-2">
                {(Object.keys(SOURCE_TYPE_INFO) as SourceType[]).map((type) => {
                  const info = SOURCE_TYPE_INFO[type];
                  const isSelected = formData.type === type;
                  return (
                    <Card
                      key={type}
                      className={cn(
                        "cursor-pointer transition-colors",
                        isSelected && "border-primary bg-primary/10"
                      )}
                      onClick={() =>
                        setFormData((prev) => ({
                          ...prev,
                          type,
                          config: {},
                        }))
                      }
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{info.icon}</span>
                          <span className="font-medium">{info.label}</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {info.description}
                        </p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          {/* Type-specific config */}
          {formData.type === "telegram" && (
            <div className="space-y-4">
              <Separator />
              <h4 className="font-medium">Telegram Configuration</h4>
              <div className="space-y-2">
                <Label htmlFor="group-id">Group/Channel ID or Username</Label>
                <Input
                  id="group-id"
                  value={(formData.config.group_id as string) || ""}
                  onChange={(e) => updateConfig("group_id", e.target.value)}
                  placeholder="@channel_name or -1001234567890"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="group-name">Display Name</Label>
                <Input
                  id="group-name"
                  value={(formData.config.group_name as string) || ""}
                  onChange={(e) => updateConfig("group_name", e.target.value)}
                  placeholder="Trading Signals"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="keywords">Keywords (comma-separated, optional)</Label>
                <Input
                  id="keywords"
                  value={
                    Array.isArray(formData.config.keywords)
                      ? (formData.config.keywords as string[]).join(", ")
                      : ""
                  }
                  onChange={(e) =>
                    updateConfig(
                      "keywords",
                      e.target.value
                        .split(",")
                        .map((k) => k.trim())
                        .filter(Boolean)
                    )
                  }
                  placeholder="buy, sell, signal"
                />
                <p className="text-xs text-muted-foreground">
                  Only process messages containing these keywords
                </p>
              </div>
            </div>
          )}

          {formData.type === "ifttt" && (
            <div className="space-y-4">
              <Separator />
              <h4 className="font-medium">IFTTT Configuration</h4>
              <div className="space-y-2">
                <Label htmlFor="event-name">Event Name</Label>
                <Input
                  id="event-name"
                  value={(formData.config.event_name as string) || ""}
                  onChange={(e) => updateConfig("event_name", e.target.value)}
                  placeholder="trading_signal"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="webhook-key">Webhook Key</Label>
                <Input
                  id="webhook-key"
                  type="password"
                  value={(formData.config.webhook_key as string) || ""}
                  onChange={(e) => updateConfig("webhook_key", e.target.value)}
                  placeholder="Your IFTTT webhook key"
                />
              </div>
              <Card className="bg-muted/50">
                <CardContent className="p-3">
                  <p className="text-sm">Your webhook URL will be:</p>
                  <code className="text-xs text-primary break-all">
                    {`${typeof window !== "undefined" ? window.location.origin : ""}/api/webhooks/ifttt/${formData.config.event_name || "{event_name}"}`}
                  </code>
                </CardContent>
              </Card>
            </div>
          )}

          {formData.type === "rss" && (
            <div className="space-y-4">
              <Separator />
              <h4 className="font-medium">RSS Configuration</h4>
              <div className="space-y-2">
                <Label htmlFor="feed-url">Feed URL</Label>
                <Input
                  id="feed-url"
                  type="url"
                  value={(formData.config.feed_url as string) || ""}
                  onChange={(e) => updateConfig("feed_url", e.target.value)}
                  placeholder="https://example.com/feed.xml"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="poll-interval">Poll Interval (minutes)</Label>
                <Input
                  id="poll-interval"
                  type="number"
                  value={(formData.config.poll_interval_minutes as number) || 15}
                  onChange={(e) =>
                    updateConfig("poll_interval_minutes", parseInt(e.target.value))
                  }
                  min="1"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rss-keywords">
                  Keywords (comma-separated, optional)
                </Label>
                <Input
                  id="rss-keywords"
                  value={
                    Array.isArray(formData.config.keywords)
                      ? (formData.config.keywords as string[]).join(", ")
                      : ""
                  }
                  onChange={(e) =>
                    updateConfig(
                      "keywords",
                      e.target.value
                        .split(",")
                        .map((k) => k.trim())
                        .filter(Boolean)
                    )
                  }
                  placeholder="polymarket, prediction"
                />
              </div>
            </div>
          )}

          {formData.type === "manual" && (
            <div className="space-y-4">
              <Separator />
              <Card className="bg-muted/50">
                <CardContent className="p-4">
                  <p className="text-sm">
                    Manual sources don&apos;t require configuration. You can
                    manually create signals from this source via the API or
                    dashboard.
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Enabled toggle */}
          <div className="space-y-4">
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium">Enable Source</h4>
                <p className="text-sm text-muted-foreground">
                  Start receiving signals from this source
                </p>
              </div>
              <Switch
                checked={formData.enabled}
                onCheckedChange={(checked) =>
                  setFormData((prev) => ({ ...prev, enabled: checked }))
                }
              />
            </div>
          </div>
        </form>

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading || !formData.name}>
            {isLoading
              ? "Saving..."
              : editingSource
                ? "Save Changes"
                : "Add Source"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
