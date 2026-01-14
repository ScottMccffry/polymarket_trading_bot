"use client";

import { useState, useEffect } from "react";
import {
  SourceCard,
  AddSourceModal,
  Source,
  SourceFormData,
  SOURCE_TYPE_INFO,
  SourceType,
} from "./components";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus } from "lucide-react";


export default function Sources() {
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [filter, setFilter] = useState<SourceType | "all">("all");

  useEffect(() => {
    // TODO: Replace with actual API call when sources API is implemented
    const loadSources = async () => {
      setIsLoading(true);
      // No mock data - start with empty sources
      setSources([]);
      setIsLoading(false);
    };
    loadSources();
  }, []);

  const handleToggleSource = async (id: number, enabled: boolean) => {
    // TODO: API call to toggle source
    setSources((prev) =>
      prev.map((s) => (s.id === id ? { ...s, enabled } : s))
    );
  };

  const handleDeleteSource = async (id: number) => {
    // TODO: API call to delete source
    setSources((prev) => prev.filter((s) => s.id !== id));
  };

  const handleEditSource = (source: Source) => {
    setEditingSource(source);
    setIsModalOpen(true);
  };

  const handleSaveSource = async (data: SourceFormData) => {
    if (editingSource) {
      // TODO: API call to update source
      setSources((prev) =>
        prev.map((s) =>
          s.id === editingSource.id
            ? { ...s, ...data, updated_at: new Date().toISOString() }
            : s
        )
      );
    } else {
      // TODO: API call to create source
      const newSource: Source = {
        id: Math.max(...sources.map((s) => s.id), 0) + 1,
        ...data,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        signals_count: 0,
      };
      setSources((prev) => [...prev, newSource]);
    }
    setEditingSource(null);
  };

  const openAddModal = () => {
    setEditingSource(null);
    setIsModalOpen(true);
  };

  const filteredSources =
    filter === "all" ? sources : sources.filter((s) => s.type === filter);

  const stats = {
    total: sources.length,
    active: sources.filter((s) => s.enabled).length,
    totalSignals: sources.reduce((acc, s) => acc + (s.signals_count || 0), 0),
  };

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Signal Sources</h1>
          <p className="text-muted-foreground mt-1">
            Manage your trading signal sources
          </p>
        </div>
        <Button onClick={openAddModal}>
          <Plus className="w-4 h-4 mr-2" />
          Add Source
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Total Sources</div>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Active Sources</div>
            <div className="text-2xl font-bold text-green-500">{stats.active}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Total Signals</div>
            <div className="text-2xl font-bold text-blue-500">
              {stats.totalSignals}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={filter === "all" ? "default" : "secondary"}
          size="sm"
          onClick={() => setFilter("all")}
        >
          All
        </Button>
        {(Object.keys(SOURCE_TYPE_INFO) as SourceType[]).map((type) => (
          <Button
            key={type}
            variant={filter === type ? "default" : "secondary"}
            size="sm"
            onClick={() => setFilter(type)}
          >
            <span className="mr-1">{SOURCE_TYPE_INFO[type].icon}</span>
            {SOURCE_TYPE_INFO[type].label}
          </Button>
        ))}
      </div>

      {/* Sources Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      ) : filteredSources.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-2">
              {filter === "all"
                ? "No sources configured"
                : `No ${SOURCE_TYPE_INFO[filter].label} sources configured`}
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              Add a source to start receiving trading signals
            </p>
            <Button onClick={openAddModal}>Add Your First Source</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSources.map((source) => (
            <SourceCard
              key={source.id}
              source={source}
              onToggle={handleToggleSource}
              onDelete={handleDeleteSource}
              onEdit={handleEditSource}
            />
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      <AddSourceModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingSource(null);
        }}
        onSave={handleSaveSource}
        editingSource={editingSource}
      />
    </div>
  );
}
