"use client";

import { useState } from "react";
import { Source, SOURCE_TYPE_INFO } from "./types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";

interface SourceCardProps {
  source: Source;
  onToggle: (id: number, enabled: boolean) => void;
  onDelete: (id: number) => void;
  onEdit: (source: Source) => void;
}

export function SourceCard({
  source,
  onToggle,
  onDelete,
  onEdit,
}: SourceCardProps) {
  const [isToggling, setIsToggling] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const typeInfo = SOURCE_TYPE_INFO[source.type];

  const handleToggle = async () => {
    setIsToggling(true);
    await onToggle(source.id, !source.enabled);
    setIsToggling(false);
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete "${source.name}"?`)) return;
    setIsDeleting(true);
    await onDelete(source.id);
    setIsDeleting(false);
  };

  return (
    <Card className={!source.enabled ? "opacity-60" : ""}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{typeInfo.icon}</span>
            <div>
              <h3 className="font-medium">{source.name}</h3>
              <Badge variant="outline" className="mt-1">
                {typeInfo.label}
              </Badge>
            </div>
          </div>
          <Switch
            checked={source.enabled}
            onCheckedChange={handleToggle}
            disabled={isToggling}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Config preview */}
        <div className="text-sm text-muted-foreground">
          {source.type === "telegram" && !!source.config.group_name && (
            <p>Group: {String(source.config.group_name)}</p>
          )}
          {source.type === "ifttt" && !!source.config.event_name && (
            <p>Event: {String(source.config.event_name)}</p>
          )}
          {source.type === "rss" && !!source.config.feed_url && (
            <p className="truncate">URL: {String(source.config.feed_url)}</p>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <Card className="bg-muted/50">
            <CardContent className="p-2">
              <div className="text-muted-foreground">Signals</div>
              <div className="font-medium">{source.signals_count ?? 0}</div>
            </CardContent>
          </Card>
          <Card className="bg-muted/50">
            <CardContent className="p-2">
              <div className="text-muted-foreground">Win Rate</div>
              <div className="font-medium">
                {source.win_rate !== undefined
                  ? `${(source.win_rate * 100).toFixed(0)}%`
                  : "-"}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-muted/50">
            <CardContent className="p-2">
              <div className="text-muted-foreground">Last Signal</div>
              <div className="font-medium text-xs">
                {source.last_signal_at
                  ? new Date(source.last_signal_at).toLocaleDateString()
                  : "-"}
              </div>
            </CardContent>
          </Card>
        </div>

        <Separator />

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            className="flex-1"
            onClick={() => onEdit(source)}
          >
            Edit
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? "..." : "Delete"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
