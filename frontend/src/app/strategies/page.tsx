"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, AdvancedStrategy } from "@/lib/api";
import {
  StrategyCard,
  StrategyTemplates,
  CreateStrategyModal,
  StrategyFormData,
} from "./components";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function Strategies() {
  const [strategies, setStrategies] = useState<AdvancedStrategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [templateData, setTemplateData] = useState<
    Partial<StrategyFormData> | undefined
  >(undefined);

  const fetchStrategies = async () => {
    try {
      const data = await api.getAdvancedStrategies();
      setStrategies(data);
    } catch (error) {
      console.error("Failed to fetch strategies:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStrategies();
  }, []);

  const handleDeleteStrategy = (id: number) => {
    setStrategies((prev) => prev.filter((s) => s.id !== id));
  };

  const handleSelectTemplate = (template: Partial<StrategyFormData>) => {
    setTemplateData(template);
    setIsModalOpen(true);
  };

  const openNewStrategyModal = () => {
    setTemplateData(undefined);
    setIsModalOpen(true);
  };

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Strategies</h1>
        <Button asChild variant="secondary">
          <Link href="/strategies/overview">View Performance Overview</Link>
        </Button>
      </div>

      <div className="space-y-6">
        {/* Advanced Strategies Section */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle>Advanced Strategies</CardTitle>
            <Button onClick={openNewStrategyModal}>New Strategy</Button>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-48" />
                ))}
              </div>
            ) : strategies.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No strategies configured</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Create a strategy to start automated trading
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {strategies.map((strategy) => (
                  <StrategyCard
                    key={strategy.id}
                    strategy={strategy}
                    onDelete={handleDeleteStrategy}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Strategy Templates */}
        <StrategyTemplates onSelectTemplate={handleSelectTemplate} />
      </div>

      {/* Create Strategy Modal */}
      <CreateStrategyModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setTemplateData(undefined);
        }}
        onSuccess={fetchStrategies}
        initialData={templateData}
      />
    </div>
  );
}
