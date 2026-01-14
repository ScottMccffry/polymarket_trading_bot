"use client";

import { useState, useEffect } from "react";
import { api, Market } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, Loader2 } from "lucide-react";
import { MarketDetailDialog } from "./MarketDetailDialog";

export default function Markets() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [harvesting, setHarvesting] = useState(false);
  const [harvestResult, setHarvestResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(0);
  const [schedulerStatus, setSchedulerStatus] = useState<{
    running: boolean;
    nextRun: string | null;
  } | null>(null);
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const pageSize = 20;

  const fetchMarkets = async () => {
    try {
      setLoading(true);
      const data = await api.getMarkets({
        limit: pageSize,
        offset: page * pageSize,
        search: search || undefined,
        category: category || undefined,
        active: true,
      });
      setMarkets(data);

      const countData = await api.getMarketsCount({
        search: search || undefined,
        category: category || undefined,
        active: true,
      });
      setTotalCount(countData.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch markets");
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const data = await api.getMarketCategories();
      setCategories(data.categories);
    } catch (err) {
      console.error("Failed to fetch categories:", err);
    }
  };

  const fetchSchedulerStatus = async () => {
    try {
      const status = await api.getSchedulerStatus();
      const harvestJob = status.jobs.find((j) => j.id === "harvest_markets");
      setSchedulerStatus({
        running: status.running,
        nextRun: harvestJob?.next_run || null,
      });
    } catch (err) {
      console.error("Failed to fetch scheduler status:", err);
    }
  };

  const handleHarvest = async () => {
    setHarvesting(true);
    setHarvestResult(null);
    setError(null);

    try {
      const result = await api.harvestMarkets();
      if (result.status === "success") {
        setHarvestResult(`Successfully harvested ${result.markets_harvested} markets`);
        fetchMarkets();
        fetchSchedulerStatus();
      } else {
        setError(result.message || "Harvest failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Harvest failed");
    } finally {
      setHarvesting(false);
    }
  };

  useEffect(() => {
    fetchMarkets();
    fetchCategories();
    fetchSchedulerStatus();
  }, [page, search, category]);

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleMarketClick = (market: Market) => {
    setSelectedMarket(market);
    setDialogOpen(true);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString();
  };

  const formatNumber = (num: number | null) => {
    if (num === null) return "-";
    if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `$${(num / 1000).toFixed(1)}K`;
    return `$${num.toFixed(0)}`;
  };

  return (
    <div className="container py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Markets</h1>
          <p className="text-muted-foreground mt-1">
            {totalCount} active markets
            {schedulerStatus?.nextRun && (
              <span className="ml-2 text-sm">
                | Next auto-harvest: {new Date(schedulerStatus.nextRun).toLocaleString()}
              </span>
            )}
          </p>
        </div>
        <Button onClick={handleHarvest} disabled={harvesting}>
          {harvesting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Harvesting...
            </>
          ) : (
            <>
              <RefreshCw className="mr-2 h-4 w-4" />
              Harvest Markets
            </>
          )}
        </Button>
      </div>

      {harvestResult && (
        <Alert className="mb-4 border-green-500 bg-green-500/10">
          <AlertDescription className="text-green-500">
            {harvestResult}
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex gap-4 mb-6">
        <Input
          placeholder="Search markets..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          className="flex-1"
        />
        <Select
          value={category}
          onValueChange={(value) => {
            setCategory(value === "all" ? "" : value);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Market</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Volume</TableHead>
                <TableHead>Liquidity</TableHead>
                <TableHead>End Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-20" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-16" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-16" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-20" />
                    </TableCell>
                  </TableRow>
                ))
              ) : markets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No markets available. Click &quot;Harvest Markets&quot; to fetch from Polymarket.
                  </TableCell>
                </TableRow>
              ) : (
                markets.map((market) => (
                  <TableRow
                    key={market.condition_id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleMarketClick(market)}
                  >
                    <TableCell>
                      <div className="font-medium max-w-md truncate">
                        {market.question}
                      </div>
                      {market.market_slug && (
                        <div className="text-sm text-muted-foreground truncate">
                          {market.market_slug}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {market.category || "-"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatNumber(market.volume)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatNumber(market.liquidity)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(market.end_date_iso)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <div className="flex justify-between items-center mt-4">
          <p className="text-sm text-muted-foreground">
            Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, totalCount)} of{" "}
            {totalCount}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              Previous
            </Button>
            <span className="px-3 py-1 text-sm text-muted-foreground flex items-center">
              Page {page + 1} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      <MarketDetailDialog
        market={selectedMarket}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
    </div>
  );
}
