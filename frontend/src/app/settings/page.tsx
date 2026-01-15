"use client";

import { useState, useEffect } from "react";
import {
  api,
  TelegramSettings,
  LLMSettings,
  QdrantSettings,
  QdrantStatus,
  SignalTestResponse,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ChevronDown, ArrowUp, ArrowDown, Minus, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConfigSectionProps {
  title: string;
  description: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function ConfigSection({
  title,
  description,
  children,
  defaultOpen = false,
}: ConfigSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-accent/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <CardTitle className="text-base">{title}</CardTitle>
                <Badge variant="secondary" className="text-xs">
                  {description}
                </Badge>
              </div>
              <ChevronDown
                className={cn(
                  "h-5 w-5 text-muted-foreground transition-transform",
                  isOpen && "rotate-180"
                )}
              />
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">{children}</CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

export default function Settings() {
  // Telegram state
  const [telegramSettings, setTelegramSettings] =
    useState<TelegramSettings | null>(null);
  const [telegramApiId, setTelegramApiId] = useState("");
  const [telegramApiHash, setTelegramApiHash] = useState("");
  const [telegramPhone, setTelegramPhone] = useState("");
  const [telegramSaving, setTelegramSaving] = useState(false);
  const [telegramMessage, setTelegramMessage] = useState("");

  // LLM state
  const [llmSettings, setLlmSettings] = useState<LLMSettings | null>(null);
  const [openaiApiKey, setOpenaiApiKey] = useState("");
  const [llmModel, setLlmModel] = useState("gpt-4o-mini");
  const [llmSaving, setLlmSaving] = useState(false);
  const [llmMessage, setLlmMessage] = useState("");

  // Qdrant state
  const [qdrantSettings, setQdrantSettings] = useState<QdrantSettings | null>(
    null
  );
  const [qdrantUrl, setQdrantUrl] = useState("");
  const [qdrantApiKey, setQdrantApiKey] = useState("");
  const [qdrantCollection, setQdrantCollection] = useState("polymarket_markets");
  const [qdrantSaving, setQdrantSaving] = useState(false);
  const [qdrantMessage, setQdrantMessage] = useState("");
  const [qdrantStatus, setQdrantStatus] = useState<QdrantStatus | null>(null);
  const [qdrantSyncing, setQdrantSyncing] = useState(false);

  // Signal simulation state
  const [simulationMessage, setSimulationMessage] = useState("");
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationResult, setSimulationResult] = useState<SignalTestResponse | null>(null);
  const [simulationError, setSimulationError] = useState("");

  // Load settings on mount
  useEffect(() => {
    loadAllSettings();
  }, []);

  const loadAllSettings = async () => {
    try {
      const settings = await api.getAllSettings();

      // Telegram
      setTelegramSettings(settings.telegram);
      setTelegramApiId(settings.telegram.api_id?.toString() || "");
      setTelegramPhone(settings.telegram.phone || "");

      // LLM
      setLlmSettings(settings.llm);
      setLlmModel(settings.llm.model || "gpt-4o-mini");

      // Qdrant
      setQdrantSettings(settings.qdrant);
      setQdrantUrl(settings.qdrant.url || "");
      setQdrantCollection(
        settings.qdrant.collection_name || "polymarket_markets"
      );

      // Load Qdrant status
      loadQdrantStatus();
    } catch (error) {
      console.error("Failed to load settings:", error);
    }
  };

  const loadQdrantStatus = async () => {
    try {
      const status = await api.getQdrantStatus();
      setQdrantStatus(status);
    } catch (error) {
      console.error("Failed to load Qdrant status:", error);
      setQdrantStatus({ configured: false, error: "Failed to connect" });
    }
  };

  const saveTelegramSettings = async () => {
    setTelegramSaving(true);
    setTelegramMessage("");
    try {
      const update: Record<string, unknown> = {};
      if (telegramApiId) update.api_id = parseInt(telegramApiId);
      if (telegramApiHash) update.api_hash = telegramApiHash;
      if (telegramPhone) update.phone = telegramPhone;

      const result = await api.updateTelegramSettings(update);
      setTelegramSettings(result);
      setTelegramMessage("Saved successfully");
      setTelegramApiHash(""); // Clear password field after save
    } catch (error) {
      setTelegramMessage(`Error: ${error}`);
    } finally {
      setTelegramSaving(false);
    }
  };

  const saveLlmSettings = async () => {
    setLlmSaving(true);
    setLlmMessage("");
    try {
      const update: Record<string, unknown> = { model: llmModel };
      if (openaiApiKey) update.openai_api_key = openaiApiKey;

      const result = await api.updateLLMSettings(update);
      setLlmSettings(result);
      setLlmMessage("Saved successfully");
      setOpenaiApiKey(""); // Clear password field after save
    } catch (error) {
      setLlmMessage(`Error: ${error}`);
    } finally {
      setLlmSaving(false);
    }
  };

  const saveQdrantSettings = async () => {
    setQdrantSaving(true);
    setQdrantMessage("");
    try {
      const update: Record<string, unknown> = {
        url: qdrantUrl,
        collection_name: qdrantCollection,
      };
      if (qdrantApiKey) update.api_key = qdrantApiKey;

      const result = await api.updateQdrantSettings(update);
      setQdrantSettings(result);
      setQdrantMessage("Saved successfully");
      setQdrantApiKey(""); // Clear password field after save
      loadQdrantStatus(); // Refresh status
    } catch (error) {
      setQdrantMessage(`Error: ${error}`);
    } finally {
      setQdrantSaving(false);
    }
  };

  const syncQdrantMarkets = async () => {
    setQdrantSyncing(true);
    setQdrantMessage("");
    try {
      const result = await api.embedMarkets();
      setQdrantMessage(`Synced ${result.count} markets`);
      loadQdrantStatus();
    } catch (error) {
      setQdrantMessage(`Error: ${error}`);
    } finally {
      setQdrantSyncing(false);
    }
  };

  const runSignalSimulation = async () => {
    if (!simulationMessage.trim()) {
      setSimulationError("Please enter a message to simulate");
      return;
    }

    setSimulationLoading(true);
    setSimulationError("");
    setSimulationResult(null);

    try {
      const result = await api.testSignal(simulationMessage, "simulation");
      setSimulationResult(result);
    } catch (error) {
      setSimulationError(`Error: ${error}`);
    } finally {
      setSimulationLoading(false);
    }
  };

  return (
    <div className="container max-w-4xl py-8">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>

      <section>
        <h2 className="text-lg font-semibold mb-4">Configuration</h2>
        <div className="space-y-4">
          {/* Telegram Credentials */}
          <ConfigSection
            title="Telegram Credentials"
            description="API ID, Hash, Phone"
            defaultOpen
          >
            <CardDescription className="mb-4">
              Configure Telegram API credentials for message monitoring.
            </CardDescription>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="telegram-api-id">API ID</Label>
                <Input
                  id="telegram-api-id"
                  value={telegramApiId}
                  onChange={(e) => setTelegramApiId(e.target.value)}
                  placeholder="Enter API ID"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="telegram-api-hash">API Hash</Label>
                <Input
                  id="telegram-api-hash"
                  type="password"
                  value={telegramApiHash}
                  onChange={(e) => setTelegramApiHash(e.target.value)}
                  placeholder={
                    telegramSettings?.api_hash_masked || "Enter API Hash"
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="telegram-phone">Phone Number</Label>
                <Input
                  id="telegram-phone"
                  value={telegramPhone}
                  onChange={(e) => setTelegramPhone(e.target.value)}
                  placeholder="+1234567890"
                />
              </div>
              <div className="flex items-center gap-4">
                <Button onClick={saveTelegramSettings} disabled={telegramSaving}>
                  {telegramSaving ? "Saving..." : "Save Telegram Settings"}
                </Button>
                {telegramMessage && (
                  <span
                    className={cn(
                      "text-sm",
                      telegramMessage.startsWith("Error")
                        ? "text-destructive"
                        : "text-green-500"
                    )}
                  >
                    {telegramMessage}
                  </span>
                )}
              </div>
            </div>
          </ConfigSection>

          {/* LLM Settings */}
          <ConfigSection
            title="LLM Settings"
            description="OpenAI API Key & Model"
            defaultOpen
          >
            <CardDescription className="mb-4">
              Configure OpenAI API for embeddings and analysis.
            </CardDescription>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="openai-api-key">OpenAI API Key</Label>
                <Input
                  id="openai-api-key"
                  type="password"
                  value={openaiApiKey}
                  onChange={(e) => setOpenaiApiKey(e.target.value)}
                  placeholder={llmSettings?.openai_api_key_masked || "sk-..."}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="llm-model">Model</Label>
                <Select value={llmModel} onValueChange={setLlmModel}>
                  <SelectTrigger id="llm-model">
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-4o">gpt-4o (Powerful)</SelectItem>
                    <SelectItem value="gpt-4o-mini">
                      gpt-4o-mini (Fast, Cheap)
                    </SelectItem>
                    <SelectItem value="gpt-4-turbo">gpt-4-turbo</SelectItem>
                    <SelectItem value="gpt-3.5-turbo">
                      gpt-3.5-turbo (Legacy)
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-4">
                <Button onClick={saveLlmSettings} disabled={llmSaving}>
                  {llmSaving ? "Saving..." : "Save LLM Settings"}
                </Button>
                {llmMessage && (
                  <span
                    className={cn(
                      "text-sm",
                      llmMessage.startsWith("Error")
                        ? "text-destructive"
                        : "text-green-500"
                    )}
                  >
                    {llmMessage}
                  </span>
                )}
              </div>
            </div>
          </ConfigSection>

          {/* Qdrant Vector Database */}
          <ConfigSection
            title="Qdrant Vector Database"
            description="Semantic search for markets (RAG)"
            defaultOpen
          >
            <CardDescription className="mb-4">
              Configure Qdrant for semantic market search. Values from
              environment variables (QDRANT_URL, QDRANT_API_KEY) are used if
              set.
            </CardDescription>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Settings form */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="qdrant-url">Qdrant URL</Label>
                  <Input
                    id="qdrant-url"
                    value={qdrantUrl}
                    onChange={(e) => setQdrantUrl(e.target.value)}
                    placeholder="http://localhost:6333"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="qdrant-api-key">Qdrant API Key</Label>
                  <Input
                    id="qdrant-api-key"
                    type="password"
                    value={qdrantApiKey}
                    onChange={(e) => setQdrantApiKey(e.target.value)}
                    placeholder={
                      qdrantSettings?.api_key_masked || "Enter API Key"
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="qdrant-collection">Collection Name</Label>
                  <Input
                    id="qdrant-collection"
                    value={qdrantCollection}
                    onChange={(e) => setQdrantCollection(e.target.value)}
                    placeholder="polymarket_markets"
                  />
                </div>
                <div className="flex items-center gap-4">
                  <Button onClick={saveQdrantSettings} disabled={qdrantSaving}>
                    {qdrantSaving ? "Saving..." : "Save Qdrant Settings"}
                  </Button>
                  {qdrantMessage && (
                    <span
                      className={cn(
                        "text-sm",
                        qdrantMessage.startsWith("Error")
                          ? "text-destructive"
                          : "text-green-500"
                      )}
                    >
                      {qdrantMessage}
                    </span>
                  )}
                </div>
              </div>

              {/* Status panel */}
              <Card className="bg-muted/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold">Status</CardTitle>
                </CardHeader>
                <CardContent>
                  {qdrantStatus ? (
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Status:</span>
                        <Badge
                          variant={
                            qdrantStatus.configured ? "default" : "destructive"
                          }
                        >
                          {qdrantStatus.configured ? "Connected" : "Not Connected"}
                        </Badge>
                      </div>
                      {qdrantStatus.configured && (
                        <>
                          <Separator />
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Collection:
                            </span>
                            <span>
                              {qdrantStatus.collection_name || qdrantCollection}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Vectors:</span>
                            <span>
                              {qdrantStatus.vectors_count?.toLocaleString() || 0}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Points:</span>
                            <span>
                              {qdrantStatus.points_count?.toLocaleString() || 0}
                            </span>
                          </div>
                        </>
                      )}
                      {qdrantStatus.error && (
                        <p className="text-destructive text-xs mt-2">
                          {qdrantStatus.error}
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Loading status...
                    </p>
                  )}

                  <div className="flex gap-2 mt-4">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={syncQdrantMarkets}
                      disabled={qdrantSyncing || !qdrantStatus?.configured}
                    >
                      {qdrantSyncing ? "Syncing..." : "Sync Markets"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={loadQdrantStatus}
                    >
                      Refresh
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ConfigSection>

          {/* Trading Parameters */}
          <ConfigSection
            title="Trading Parameters"
            description="Position size, confidence, spread limits"
          >
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="max-position">Max Position Size ($)</Label>
                <Input
                  id="max-position"
                  type="number"
                  placeholder="100"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="min-confidence">Minimum Confidence (%)</Label>
                <Input
                  id="min-confidence"
                  type="number"
                  placeholder="70"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-spread">Max Spread (%)</Label>
                <Input
                  id="max-spread"
                  type="number"
                  placeholder="5"
                />
              </div>
            </div>
          </ConfigSection>

          {/* Signal Simulation */}
          <ConfigSection
            title="Signal Simulation"
            description="Test if a message creates a signal"
            defaultOpen
          >
            <CardDescription className="mb-4">
              Enter a message to simulate how the signal trader would process it.
              This searches Qdrant for matching markets and analyzes them with the LLM.
            </CardDescription>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="simulation-message">Message to Simulate</Label>
                <Textarea
                  id="simulation-message"
                  value={simulationMessage}
                  onChange={(e) => setSimulationMessage(e.target.value)}
                  placeholder="Enter a message like you would see in a Telegram group... e.g., 'Breaking: Trump announces new tariffs on China'"
                  rows={4}
                />
              </div>

              <div className="flex items-center gap-4">
                <Button
                  onClick={runSignalSimulation}
                  disabled={simulationLoading || !simulationMessage.trim()}
                >
                  {simulationLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    "Run Simulation"
                  )}
                </Button>
                {simulationError && (
                  <span className="text-sm text-destructive">{simulationError}</span>
                )}
              </div>

              {/* Results */}
              {simulationResult && (
                <div className="mt-6 space-y-4">
                  <Separator />
                  <div className="flex items-center gap-4">
                    <Badge variant="outline">
                      Markets Found: {simulationResult.markets_found}
                    </Badge>
                    <Badge
                      variant={simulationResult.signals_generated > 0 ? "default" : "secondary"}
                    >
                      Signals Generated: {simulationResult.signals_generated}
                    </Badge>
                  </div>

                  {simulationResult.signals.length === 0 ? (
                    <Card className="bg-muted/50">
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">
                          No actionable signals were generated from this message.
                          {simulationResult.markets_found > 0
                            ? " Markets were found but none met the confidence threshold (70%)."
                            : " No matching markets were found in the vector database."}
                        </p>
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-sm">Generated Signals:</h4>
                      {simulationResult.signals.map((signal, index) => (
                        <Card key={index} className="bg-muted/50">
                          <CardContent className="pt-4 space-y-3">
                            <div className="flex items-start justify-between gap-4">
                              <p className="text-sm font-medium flex-1">
                                {signal.market_question}
                              </p>
                              <Badge
                                variant={signal.direction === "BUY" ? "default" : "destructive"}
                                className="flex items-center gap-1"
                              >
                                {signal.direction === "BUY" ? (
                                  <ArrowUp className="h-3 w-3" />
                                ) : signal.direction === "SELL" ? (
                                  <ArrowDown className="h-3 w-3" />
                                ) : (
                                  <Minus className="h-3 w-3" />
                                )}
                                {signal.direction}
                              </Badge>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                              <div>
                                <span className="text-muted-foreground">Confidence:</span>
                                <span className="ml-1 font-medium">
                                  {(signal.confidence * 100).toFixed(0)}%
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Relevance:</span>
                                <span className="ml-1 font-medium">
                                  {(signal.relevance_score * 100).toFixed(0)}%
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Similarity:</span>
                                <span className="ml-1 font-medium">
                                  {(signal.similarity_score * 100).toFixed(0)}%
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Type:</span>
                                <span className="ml-1 font-medium capitalize">
                                  {signal.message_type.replace(/_/g, " ")}
                                </span>
                              </div>
                            </div>

                            <div className="text-xs text-muted-foreground bg-background/50 p-2 rounded">
                              <span className="font-medium">Reasoning:</span> {signal.reasoning}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </ConfigSection>
        </div>
      </section>
    </div>
  );
}
